from datetime import date

import pandas as pd

from database import get_connection


def load_expenses():
    conn = get_connection()
    rows = conn.execute("SELECT amount, category, date FROM expenses").fetchall()
    conn.close()
    # Kyun dict(row): sqlite3.Row se seedha DataFrame banane mein dikkat ho sakti hai
    return pd.DataFrame([dict(row) for row in rows])


def build_insights():
    df = load_expenses()
    if df.empty:
        return None

    # Kyun to_datetime: date abhi text hai, usse asli date banane par din/mahina nikal sakte hain
    df["date"] = pd.to_datetime(df["date"])
    total = df["amount"].sum()

    # 1) Category-wise total aur share
    by_category = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    categories = [
        {
            "category": name,
            "total": round(float(amount), 2),
            "share": round(float(amount / total * 100), 1),
        }
        for name, amount in by_category.items()
    ]

    # 2) Sabse bada ek expense. idxmax = sabse bade amount wali row ka index
    biggest = df.loc[df["amount"].idxmax()]

    # 3) Sabse zyada kharche wala din (ek din ke saare expenses ka sum)
    by_day = df.groupby("date")["amount"].sum()
    top_day = by_day.idxmax()

    # 4) Average daily spend (pehle din se aakhri din tak, saare dinon par)
    days = (df["date"].max() - df["date"].min()).days + 1
    avg_daily = total / days

    # 5) Month-over-month change, sirf poore mahinon ke liye
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["amount"].sum()
    current_month = pd.Period(date.today().strftime("%Y-%m"), freq="M")
    first_month = df["month"].min()
    # Kyun filter: pehla mahina (data shuru hua) aur current mahina adhoore hote hain
    complete = monthly[(monthly.index > first_month) & (monthly.index < current_month)]

    month_change = None
    if len(complete) >= 2:
        previous, latest = complete.iloc[-2], complete.iloc[-1]
        month_change = {
            "from_month": complete.index[-2].strftime("%b %Y"),
            "to_month": complete.index[-1].strftime("%b %Y"),
            "change": round(float((latest - previous) / previous * 100), 1),
        }

    return {
        "total": round(float(total), 2),
        "top_category": categories[0],
        "categories": categories,
        "biggest": {
            "amount": float(biggest["amount"]),
            "category": biggest["category"],
            "date": biggest["date"].strftime("%d %b %Y"),
        },
        "top_day": {
            "date": top_day.strftime("%d %b %Y"),
            "total": round(float(by_day.max()), 2),
        },
        "avg_daily": round(float(avg_daily), 2),
        "month_change": month_change,
    }