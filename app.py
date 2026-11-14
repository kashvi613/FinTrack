from flask import Flask, render_template, request, redirect, url_for
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

    conn.close()
    return render_template("index.html", stats=stats, expenses=recent)

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
    if request.method == "POST":
        amount = float(request.form["amount"])
        category = request.form["category"]
        date = request.form["date"]
        description = request.form["description"]

        conn = get_connection()
        # Kyun ?: SQL injection se bachne ke liye parameterized query
        conn.execute(
            "INSERT INTO expenses (amount, category, date, description) VALUES (?, ?, ?, ?)",
            (amount, category, date, description),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    return render_template("add.html", categories=CATEGORIES)


if __name__ == "__main__":
    app.run(debug=True)

# from flask import Flask: Flask library se Flask class import kar rahe hain.
# app = Flask(__name__): ye hamara web application object banata hai. __name__ 
# Flask ko batata hai ki project ki files (templates, static) kahan hain.
# @app.route("/"): ye decorator hai. Matlab: jab koi browser / (home page) khole, 
# neeche wala function chalao. Isi ko route kehte hain.
# def home(): aur return "...": ye function browser ko jo text return karega 
# wahi screen pe dikhega.
# if __name__ == "__main__":: ye tab True hota hai jab tum file ko seedha 
# python app.py se chalao. Kisi aur file se import hone par server automatically 
# start nahi hoga.
# app.run(debug=True): server start karta hai. debug=True se code save karte hi 
# server auto-reload hota hai aur error browser mein dikhta hai. Ye sirf development ke 
# liye hai, production mein kabhi on nahi rakhte.

# python app.py
#  * Serving Flask app 'app'
#  * Debug mode: on
# WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
#  * Running on http://127.0.0.1:5000
# Press CTRL+C to quit
#  * Restarting with stat
#  * Debugger is active!
#  * Debugger PIN: 255-243-657
# 127.0.0.1 - - [14/Nov/2026 16:42:01] "GET / HTTP/1.1" 200 -
# 127.0.0.1 - - [14/Nov/2026 16:42:01] "GET /favicon.ico HTTP/1.1" 404 -

# Debug mode: on: debug=True ki wajah se. Code save karte hi server restart hoga.
# Running on http://127.0.0.1:5000: 127.0.0.1 tumhara apna computer hai (localhost), 
# aur 5000 port number hai. Matlab server sirf tumhare laptop pe chal raha hai, 
# internet pe nahi.
# Restarting with stat: Flask file changes pe nazar rakhta hai aur auto-reload karta hai.
# Debugger PIN: browser mein error aaye toh interactive debugger khulta hai, 
# ye PIN uske liye hai. Ise kisi ke saath share nahi karte.

# render_template ko import kiya. Ye templates/ folder se HTML file uthata hai 
# aur browser ko bhejta hai.
# home() ab seedha text return karne ke bajay index.html return karta hai.
