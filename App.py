import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helper import login_required

# Create the application instance
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

database_name = "FinalProject.db"

@app.route("/")
@login_required
def index():
    return render_template("layout.html")

@app.route("/account")
@login_required
def account():
    return render_template("layout.html")

@app.route("/account/login", methods=["GET", "POST"])
def login():
    # Clear any user_id
    session.clear()
 
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        print(username)
        print(password)
        # Ensure username and password is not empty
        if not username:
            flash("must provide username")
            print("must provide username")
            return render_template("login.html")

        elif not password:
            flash("must provide password")
            print("must provide password")
            return render_template("login.html")

        with sqlite3.connect(database_name) as conn:
            db = conn.cursor()
            # Get user by username from database
            users_db = db.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = users_db.fetchone()

        # Ensure the username and the password are correct 
        if not check_password_hash(user[2], password):
            flash("invalid username and/or password")
            print(user[2])
            return render_template("login.html")

        # Remember user has logged in
        session["user_id"] = user[0]

        conn.close()

        flash("Logged in")
        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/account/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Ensure username was submitted
        if not username:
            flash("must provide username")
            return render_template("register.html")

        # Ensure password was submitted
        elif not password:
            flash("must provide password")
            return render_template("register.html")

        # Ensure password was same
        elif password != confirm_password:
            flash("two passwords are not the same")
            return render_template("register.html")

        hash_password = generate_password_hash(password)

        with sqlite3.connect(database_name) as conn:
            db = conn.cursor()

            if len(db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchall()) != 0:
                flash("username already exists")
                return render_template("register.html")

            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",(username, hash_password,))
            conn.commit()
            
            users_db = db.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = users_db.fetchone()

        session["user_id"] = user[0]

        flash("Registered")
        return redirect("/")

    return render_template("register.html")
