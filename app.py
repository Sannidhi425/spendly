from datetime import date, datetime
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import init_db, get_db
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
init_db()
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Education", "Entertainment", "Other"]


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if len(username) < 3 or len(password) < 6:
            flash("Username needs 3+ characters and password needs 6+ characters.")
            return redirect(url_for("register"))
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already taken.")
            return redirect(url_for("register"))
        finally:
            conn.close()
        flash("Account created. Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
        return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    # Selected month, defaulting to the current month
    month = request.args.get(
        "month",
        date.today().strftime("%Y-%m")
    )

    # Validate month format
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        month = date.today().strftime("%Y-%m")

    expenses = conn.execute(
        """
        SELECT * FROM expenses
        WHERE user_id = ?
        AND substr(expense_date, 1, 7) = ?
        ORDER BY expense_date DESC, id DESC
        """,
        (session["user_id"], month)
    ).fetchall()

    row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = ?
        AND substr(expense_date, 1, 7) = ?
        """,
        (session["user_id"], month)
    ).fetchone()

    category_rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        AND substr(expense_date, 1, 7) = ?
        GROUP BY category
        ORDER BY total DESC
        """,
        (session["user_id"], month)
    ).fetchall()

    category_rows = [dict(r) for r in category_rows]

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        month_total=row["total"],
        categories=CATEGORIES,
        category_data=category_rows,
        today=date.today().isoformat(),
        selected_month=month
    )



@app.route("/add", methods=["POST"])
def add_expense():
    if "user_id" not in session:
        return redirect(url_for("login"))
    title = request.form["title"].strip()
    category = request.form["category"]
    expense_date = request.form["expense_date"]
    try:
        amount = float(request.form["amount"])
    except ValueError:
        amount = 0
    if not title or amount <= 0 or category not in CATEGORIES:
        flash("Please enter a valid title, amount and category.")
        return redirect(url_for("dashboard"))
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, title, amount, category, expense_date) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], title, amount, category, expense_date),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    ).fetchone()

    if expense is None:
        conn.close()
        flash("Expense not found.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form["title"].strip()
        category = request.form["category"]
        expense_date = request.form["expense_date"]

        try:
            amount = float(request.form["amount"])
        except ValueError:
            amount = 0

        if not title or amount <= 0 or category not in CATEGORIES:
            conn.close()
            flash("Please enter valid expense details.")
            return redirect(url_for("edit_expense", expense_id=expense_id))

        conn.execute(
            "UPDATE expenses SET title = ?, amount = ?, category = ?, "
            "expense_date = ? WHERE id = ? AND user_id = ?",
            (
                title,
                amount,
                category,
                expense_date,
                expense_id,
                session["user_id"],
            ),
        )
        conn.commit()
        conn.close()
        flash("Expense updated successfully.")
        return redirect(url_for("dashboard"))

    conn.close()
    return render_template(
        "edit_expense.html",
        expense=expense,
        categories=CATEGORIES,
    )

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)