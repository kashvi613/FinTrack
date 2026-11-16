import random
import sys
from datetime import date, timedelta

from database import get_connection, init_db

# Kyun seed(42): har baar same "random" data bane, taaki tests aur screenshots stable rahein
random.seed(42)

# category: (min amount, max amount, sample descriptions)
CATEGORY_DATA = {
    "Food": (80, 900, ["Swiggy order", "Zomato dinner", "Canteen lunch", "Groceries", "Cafe coffee", "Street food"]),
    "Travel": (50, 3500, ["Metro recharge", "Uber ride", "Auto fare", "Train ticket", "Bus pass", "Petrol"]),
    "Shopping": (300, 6000, ["Amazon order", "Myntra clothes", "Shoes", "Headphones", "Gift", "Stationery"]),
    "Education": (200, 8000, ["Online course", "Books", "Exam fee", "Notes printing", "Coding platform"]),
    "Other": (50, 2000, ["Mobile recharge", "Movie tickets", "Medicines", "Haircut", "Subscription"]),
}

# Kyun weights: asli zindagi mein Food zyada hota hai, Education kam
WEIGHTS = {"Food": 45, "Travel": 25, "Shopping": 12, "Education": 8, "Other": 10}

# Kyun outliers: anomaly detection (baad mein) ko kuch asli "unusual" expenses chahiye
OUTLIERS = [
    ("Shopping", 45000, "Laptop"),
    ("Travel", 28000, "Flight tickets"),
    ("Food", 9500, "Party dinner"),
]


def build_expenses(count=150, days=90):
    today = date.today()
    categories = list(CATEGORY_DATA.keys())
    weights = [WEIGHTS[c] for c in categories]
    rows = []

    for _ in range(count):
        category = random.choices(categories, weights=weights)[0]
        low, high, descriptions = CATEGORY_DATA[category]

        # Kyun triangular: zyadatar amounts chhote, kabhi-kabhi bade (uniform se zyada realistic)
        amount = round(random.triangular(low, high, low + (high - low) * 0.15))
        day = today - timedelta(days=random.randint(0, days - 1))
        rows.append((amount, category, day.isoformat(), random.choice(descriptions)))

    for category, amount, description in OUTLIERS:
        day = today - timedelta(days=random.randint(5, days - 1))
        rows.append((amount, category, day.isoformat(), description))

    return rows


def seed(reset=False):
    init_db()
    conn = get_connection()

    if reset:
        conn.execute("DELETE FROM expenses")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'expenses'")

    rows = build_expenses()
    # Kyun executemany: ek hi query ko 153 baar chalata hai, ek-ek execute likhne se tez aur saaf
    conn.executemany(
        "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"Inserted {len(rows)} demo expenses.")


if __name__ == "__main__":
    # python seed.py --reset  -> pehle saare expenses delete, phir demo data
    seed(reset="--reset" in sys.argv)