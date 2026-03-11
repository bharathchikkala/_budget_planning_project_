from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "budget_app_secret_key"


# ---------------- DB HELPERS ----------------
def get_db():
    conn = sqlite3.connect("budget.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():         #here final make  stopp stopp 
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT,
        budget REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        amount REAL,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        budget = float(request.form["budget"])

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password, budget) VALUES (?, ?, ?, ?)",
            (name, email, password, budget)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # Get all expenses
    cur.execute("""
        SELECT category, amount, description
        FROM expenses
        WHERE user_id = ?
    """, (session["user_id"],))
    expenses = cur.fetchall()

    # Category-wise totals
    cur.execute("""
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
    """, (session["user_id"],))
    category_totals = cur.fetchall()

    # Total spent
    cur.execute("""
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
    """, (session["user_id"],))
    row = cur.fetchone()
    total_expense = row["total"] if row["total"] else 0

    # ✅ FETCH USER BUDGET (THIS WAS MISSING / WRONG EARLIER)
    cur.execute("""
        SELECT budget
        FROM users
        WHERE id = ?
    """, (session["user_id"],))
    row = cur.fetchone()
    budget = row["budget"] if row else 0

    # Remaining balance
    remaining = budget - total_expense

    conn.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        expenses=expenses,
        category_totals=category_totals,
        total_expense=total_expense,
        budget=budget,
        remaining=remaining
    )


@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO expenses (user_id, category, amount, description)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], category, amount, description))
        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add_expense.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)