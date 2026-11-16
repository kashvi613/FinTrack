import pytest

import database
from app import app, format_inr, validate_expense
from insights import build_insights


# Kyun fixture: har test ko apna naya, khaali database chahiye
# Kyun tmp_path: pytest ka temporary folder, tests ke baad apne aap delete ho jaata hai
# Kyun monkeypatch: database.py ka DATABASE naam test ke dauran temporary file par mod deta hai,
# taaki tumhara asli database.db (153 seed expenses) kabhi na chhua jaye
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE", str(tmp_path / "test.db"))
    database.init_db()
    app.config["TESTING"] = True
    return app.test_client()


def make_expense(client, **overrides):
    """Helper: API se ek expense banata hai. overrides se koi bhi field badal sakte hain."""
    payload = {"amount": 250, "category": "Food", "date": "2026-11-16", "description": "test"}
    payload.update(overrides)
    return client.post("/api/expenses", json=payload)


# ---------- format_inr (Indian number format) ----------

@pytest.mark.parametrize(
    "value, expected",
    [
        (0, "₹0.00"),
        (None, "₹0.00"),
        (999, "₹999.00"),
        (1500, "₹1,500.00"),
        (150000, "₹1,50,000.00"),
        (12345678, "₹1,23,45,678.00"),
    ],
)
def test_format_inr(value, expected):
    assert format_inr(value) == expected


# ---------- validate_expense ----------

def valid_form(**overrides):
    form = {"amount": "250", "category": "Food", "date": "2026-11-16", "description": "lunch"}
    form.update(overrides)
    return form


def test_validate_accepts_good_input():
    error, amount = validate_expense(valid_form())
    assert error is None
    assert amount == 250.0


# Kyun parametrize: ek hi test function alag-alag galat inputs par chalta hai
@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"amount": "abc"}, "must be a number"),
        ({"amount": "-5"}, "greater than 0"),
        ({"amount": "0"}, "greater than 0"),
        ({"amount": "nan"}, "greater than 0"),
        ({"amount": "inf"}, "greater than 0"),
        ({"amount": "20000000"}, "too large"),
        ({"category": "Gaming"}, "valid category"),
        ({"date": "2026-02-31"}, "valid date"),
        ({"description": "x" * 101}, "100 characters"),
    ],
)
def test_validate_rejects_bad_input(overrides, message):
    error, amount = validate_expense(valid_form(**overrides))
    assert message in error
    assert amount is None


# ---------- REST API ----------

def test_api_list_is_empty_at_start(client):
    response = client.get("/api/expenses")
    assert response.status_code == 200
    assert response.get_json() == []


def test_api_create_returns_201_and_saves(client):
    response = make_expense(client, amount=300, category="Travel")
    assert response.status_code == 201
    assert response.get_json()["id"] == 1

    listed = client.get("/api/expenses").get_json()
    assert len(listed) == 1
    assert listed[0]["category"] == "Travel"


def test_api_create_rejects_bad_amount_with_400(client):
    response = make_expense(client, amount=-5)
    assert response.status_code == 400
    assert "greater than 0" in response.get_json()["error"]
    assert client.get("/api/expenses").get_json() == []   # kuch save nahi hua


def test_api_delete_and_delete_missing(client):
    new_id = make_expense(client).get_json()["id"]

    assert client.delete(f"/api/expenses/{new_id}").status_code == 200
    assert client.delete(f"/api/expenses/{new_id}").status_code == 404   # ab hai hi nahi


def test_api_summary_totals(client):
    make_expense(client, amount=100)
    make_expense(client, amount=300)

    summary = client.get("/api/summary").get_json()
    assert summary["total"] == 400
    assert summary["count"] == 2
    assert summary["average"] == 200


# Kyun ye test: SQL injection se bachav (parameterized query) sach mein kaam kar raha hai ya nahi
def test_category_filter_is_safe_from_sql_injection(client):
    make_expense(client)
    response = client.get("/api/expenses", query_string={"category": "Food' OR '1'='1"})
    assert response.get_json() == []


# ---------- Web pages ----------

def test_home_and_insights_work_with_empty_database(client):
    assert client.get("/").status_code == 200
    assert client.get("/insights").status_code == 200


def test_add_form_saves_and_redirects(client):
    response = client.post(
        "/add",
        data={"amount": "500", "category": "Shopping", "date": "2026-11-10", "description": "shoes"},
    )
    assert response.status_code == 302   # redirect (Post-Redirect-Get)
    assert len(client.get("/api/expenses").get_json()) == 1


def test_add_form_shows_error_on_bad_input(client):
    response = client.post(
        "/add",
        data={"amount": "-1", "category": "Food", "date": "2026-11-10", "description": ""},
    )
    assert response.status_code == 200
    assert b"Amount must be greater than 0." in response.data
    assert client.get("/api/expenses").get_json() == []


def test_web_delete_removes_expense(client):
    new_id = make_expense(client).get_json()["id"]

    response = client.post(f"/delete/{new_id}")
    assert response.status_code == 302
    assert client.get("/api/expenses").get_json() == []


# ---------- Pandas insights ----------

def test_insights_top_category_and_biggest(client):
    make_expense(client, amount=100, category="Food", date="2026-01-05")
    make_expense(client, amount=5000, category="Shopping", date="2026-01-06")

    data = build_insights()
    assert data["top_category"]["category"] == "Shopping"
    assert data["biggest"]["amount"] == 5000
    assert data["total"] == 5100