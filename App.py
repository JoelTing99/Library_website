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

db = sqlite3.connect("FinalProject.db")

@app.route("/")
def index():
    return render_template("layout.html")

@app.route("/account")
def account():
    return render_template("layout.html")

@app.route("/account/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return render_template("/")

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
    return render_template("/register.html")
