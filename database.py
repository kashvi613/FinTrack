import sqlite3

DATABASE = "database.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")



# sqlite3.connect(DATABASE): database.db file se connection kholta hai. 
# File nahi hai toh bana deta hai.
# row_factory = sqlite3.Row: rows ko dictionary jaisa banata hai, 
# to baad mein row["amount"] likh sakte hain.
# CREATE TABLE IF NOT EXISTS: table sirf tab banata hai jab pehle se na ho, 
# isliye code dobara chalane par error nahi aata.
# id INTEGER PRIMARY KEY AUTOINCREMENT: har expense ka unique number, 
# apne aap badhta hai.
# amount REAL NOT NULL: decimal number, khaali nahi chhod sakte.
# date TEXT: SQLite mein dates text (2026-11-15) ke roop mein store hoti hain.
# commit(): changes ko permanently save karta hai. Iske bina table save nahi hoga.