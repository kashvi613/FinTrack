import math
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_connection, init_db

app = Flask(__name__)
init_db()

CATEGORIES = ["Food", "Travel", "Shopping", "Education", "Other"]


# Custom Jinja filter: 150000 -> ₹1,50,000.00 (Indian grouping)
@app.template_filter("inr")
def format_inr(value):
    value = float(value or 0)
    whole, decimal = f"{value:.2f}".split(".")
    if len(whole) > 3:
        last3 = whole[-3:]      # aakhri 3 digits ek group
        rest = whole[:-3]       # baaki digits 2-2 ke groups mein
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        whole = ",".join(parts) + "," + last3
    return f"₹{whole}.{decimal}"


def validate_expense(form):
    """Form data check karta hai. Return: (error_message, amount)."""
    # Kyun server-side validation: HTML ke required/min browser mein bypass ho sakte hain
    try:
        amount = float(form["amount"])
    except ValueError:
        return "Amount must be a number.", None

    # Kyun isfinite: float("nan") aur float("inf") bhi valid float hote hain
    if not math.isfinite(amount) or amount <= 0:
        return "Amount must be greater than 0.", None
    if amount > 10_000_000:
        return "Amount is too large.", None

    if form["category"] not in CATEGORIES:
        return "Please choose a valid category.", None

    try:
        datetime.strptime(form["date"], "%Y-%m-%d")
    except ValueError:
        return "Please enter a valid date.", None

    if len(form["description"]) > 100:
        return "Description must be 100 characters or less.", None

    return None, amount


@app.route("/")
def home():
    conn = get_connection()

    # Kyun COALESCE: table khaali ho to SUM/AVG NULL deta hai, usse 0 bana deta hai
    stats = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total,
               COUNT(*) AS count,
               COALESCE(AVG(amount), 0) AS average
        FROM expenses
        """
    ).fetchone()

    recent = conn.execute(
        "SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT 5"
    ).fetchall()

    # Kyun GROUP BY: har category ke rows ek group mein, phir har group ka SUM
    category_rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """
    ).fetchall()

    conn.close()

    # Kyun lists: sqlite3.Row JSON mein convert nahi hota, isliye simple lists banayi
    labels = [row["category"] for row in category_rows]
    values = [row["total"] for row in category_rows]

    return render_template(
        "index.html",
        stats=stats,
        expenses=recent,
        labels=labels,
        values=values,
    )


@app.route("/history")
def history():
    # Kyun request.args: filter URL mein aata hai (/history?category=Food), isliye args, form nahi
    selected = request.args.get("category", "")

    conn = get_connection()
    if selected:
        # Kyun WHERE category = ?: sirf us category ki rows, aur ? se SQL injection se bachav
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC, id DESC",
            (selected,),
        ).fetchall()
    else:
        expenses = conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC"
        ).fetchall()
    conn.close()

    return render_template(
        "history.html",
        expenses=expenses,
        categories=CATEGORIES,
        selected=selected,
    )


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    error = None
    # Kyun form dict: galti hone par user ne jo bhara tha wo wapas dikhana hai
    form = {"amount": "", "category": CATEGORIES[0], "date": "", "description": ""}

    if request.method == "POST":
        form = {
            "amount": request.form.get("amount", "").strip(),
            "category": request.form.get("category", ""),
            "date": request.form.get("date", ""),
            "description": request.form.get("description", "").strip(),
        }
        error, amount = validate_expense(form)

        if error is None:
            conn = get_connection()
            # Kyun ?: SQL injection se bachne ke liye parameterized query
            conn.execute(
                "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
                (amount, form["category"], form["date"], form["description"]),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("home"))

    return render_template("add.html", categories=CATEGORIES, form=form, error=error)


# Kyun <int:expense_id>: URL ka number function ko mil jaata hai (/delete/5 -> expense_id = 5)
# Kyun sirf POST: delete data badalta hai, GET se hota to koi link kholte hi data ud jata
@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

    # Delete ke baad usi filter par wapas jao jahan se aaye the
    return redirect(url_for("history", category=request.form.get("category") or None))

# ---------------- REST API (JSON) ----------------

@app.route("/api/expenses", methods=["GET"])
def api_list_expenses():
    category = request.args.get("category", "")

    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE category = ? ORDER BY date DESC, id DESC",
            (category,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC, id DESC"
        ).fetchall()
    conn.close()

    # Kyun dict(row): sqlite3.Row ko JSON mein nahi badal sakte, dict ko badal sakte hain
    return jsonify([dict(row) for row in rows])


@app.route("/api/expenses", methods=["POST"])
def api_create_expense():
    # Kyun silent=True: galat JSON aaye to crash nahi, None milta hai
    data = request.get_json(silent=True) or {}

    form = {
        "amount": str(data.get("amount", "")).strip(),
        "category": str(data.get("category", "")),
        "date": str(data.get("date", "")),
        "description": str(data.get("description", "")).strip(),
    }
    # Kyun wahi validate_expense: web form aur API dono ke rules same rahein
    error, amount = validate_expense(form)
    if error:
        return jsonify({"error": error}), 400

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
        (amount, form["category"], form["date"], form["description"]),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_id, "amount": amount, **{k: form[k] for k in ("category", "date", "description")}}), 201


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def api_delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

    # Kyun rowcount: 0 matlab us id ki koi row thi hi nahi
    if cursor.rowcount == 0:
        return jsonify({"error": "Expense not found."}), 404
    return jsonify({"deleted": expense_id})


@app.route("/api/summary", methods=["GET"])
def api_summary():
    conn = get_connection()
    stats = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total,
               COUNT(*) AS count,
               COALESCE(AVG(amount), 0) AS average
        FROM expenses
        """
    ).fetchone()
    by_category = conn.execute(
        """
        SELECT category, SUM(amount) AS total, COUNT(*) AS count
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """
    ).fetchall()
    conn.close()

    return jsonify({
        "total": stats["total"],
        "count": stats["count"],
        "average": round(stats["average"], 2),
        "by_category": [dict(row) for row in by_category],
    })

if __name__ == "__main__":
    app.run(debug=True)