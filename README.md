# FinTrack: Expense Analytics System

A personal expense tracking and analytics web app built with **Python, Flask and SQLite**.
Add, edit and filter expenses, see spending charts, and get data-driven insights with Pandas.

## Features

- **Dashboard**: total spent, number of transactions, average spend
- **Charts**: category-wise spending (doughnut) and monthly trend (line), built with Chart.js
- **Full CRUD**: add, view, edit and delete expenses
- **Category filter**: Food, Travel, Shopping, Education, Other
- **Insights (Pandas)**: top category, biggest expense, highest-spend day, average daily spend, month-over-month change
- **REST API**: JSON endpoints for expenses, summary, monthly totals and insights
- **Validation**: server-side checks (amount, category, date, description length)
- **Responsive UI**: sidebar on desktop, bottom navigation on mobile
- **Indian number formatting**: ₹1,50,000.00
- **Automated tests**: pytest suite covering validation, API, pages and insights

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite (raw SQL with `sqlite3`) |
| Data analysis | Pandas |
| Frontend | HTML, CSS, JavaScript, Jinja2 templates |
| Charts | Chart.js |
| Testing | pytest |
| Version control | Git, GitHub |

## Getting started

```bash
# 1. Clone the repository
git clone https://github.com/kashvi613/FinTrack.git
cd FinTrack

# 2. Create and activate a virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Load demo data: ~150 expenses over 3 months
python seed.py --reset

# 5. Run the app
python app.py
```

Open http://127.0.0.1:5000 in your browser.

The database file (`database.db`) is created automatically on first run and is
not committed to Git, since it holds personal data. Use `seed.py` for demo data.

## Running the tests

```bash
python -m pytest -v
```

Tests run against a temporary database, so your real data is never touched.

## REST API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/expenses` | List expenses (optional `?category=Food`) |
| POST | `/api/expenses` | Create an expense (returns 201) |
| PUT | `/api/expenses/<id>` | Update an expense |
| DELETE | `/api/expenses/<id>` | Delete an expense |
| GET | `/api/summary` | Total, count, average, per-category totals |
| GET | `/api/monthly` | Month-wise totals |
| GET | `/api/insights` | Pandas-based insights |

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 250, "category": "Food", "date": "2026-11-16", "description": "Lunch"}'
```

Invalid input returns `400` with an error message; unknown ids return `404`.

## Project structure

```
FinTrack/
├── app.py            # Flask routes, validation, REST API
├── database.py       # SQLite connection and table setup
├── insights.py       # Pandas analytics
├── seed.py           # Demo data generator
├── static/
│   └── style.css     # Dark blue theme, responsive layout
├── templates/        # Jinja2 templates (base, dashboard, history, add/edit, insights)
├── tests/
│   └── test_fintrack.py
├── requirements.txt
└── README.md
```

## Design decisions

- **Raw SQL instead of an ORM**: to work directly with `GROUP BY`, aggregates and parameterized queries.
- **Parameterized queries (`?`)** everywhere, which protects against SQL injection (covered by a test).
- **One `validate_expense()` function** shared by the web form and the API, so rules never drift apart.
- **Server-side validation** in addition to HTML attributes, because browser checks can be bypassed.
- **POST for delete**: state-changing actions are never triggered by GET.
- **Month-over-month ignores partial months**, so incomplete data doesn't distort the trend.

## Roadmap

- [ ] Anomaly detection for unusual expenses (z-score, then Isolation Forest)
- [ ] React frontend consuming the REST API
- [ ] Natural-language questions over the data

## Author

Kashvi, [GitHub](https://github.com/kashvi613)