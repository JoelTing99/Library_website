import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from uuid import uuid4

UPLOAD_FOLDER = "static/uploads/"

# Create the application instance
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Set file path
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
Session(app)

database_name = "FinalProject.db"


"""CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
    title TEXT NOT NULL,
    publish_date DATE DEFAULT CURRENT_DATE,
    publisher TEXT NOT NULL,
    creater_id INTEGER NOT NULL,
    pages INTEGER NOT NULL,
    file_name TEXT NOT NULL)"""

"""CREATE TABLE historys (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    title TEXT NOT NULL,
    time DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    action TEXT NOT NULL)"""

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/account/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/search", methods=["GET"])
@login_required
def search():
    return render_template("index.html")

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
            return redirect(request.url)

        elif not password:
            flash("must provide password")
            return redirect(request.url)

        with sqlite3.connect(database_name) as conn:
            db = conn.cursor()
            # Get user by username from database
            users_db = db.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = users_db.fetchone()

        # Ensure the username and the password are correct 
        if user == None or not check_password_hash(user[2], password):
            flash("invalid username and/or password")
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
            return render_template(request.url)

        # Ensure password was submitted
        elif not password:
            flash("must provide password")
            return render_template(request.url)

        # Ensure password was same
        elif password != confirm_password:
            flash("two passwords are not the same")
            return render_template(request.url)

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


@app.route("/account/add_book", methods=["GET", "POST"])
@login_required
def Add_book():
    
    if request.method == "POST":

        user_id = session["user_id"]

        title = request.form.get("title")
        publisher = request.form.get("publisher")
        pages = request.form.get("pages")
        book_pdf = request.files.get("book_pdf")
        
        

        if not title:
            flash("must provide title")
            return redirect(request.url)

        if not publisher:
            flash("must provide publisher")
            return redirect(request.url)

        if not pages:
            flash("must provide pages")
            return redirect(request.url)

        if  book_pdf.filename == "":
            flash("must provide file")
            return redirect(request.url)

        book_pdf_name = secure_filename(book_pdf.filename)

        if book_pdf_name == "pdf":
            book_pdf_name = str(uuid4().hex) + ".pdf"

        book_pdf.save(os.path.join(UPLOAD_FOLDER, book_pdf_name))

        with sqlite3.connect(database_name) as conn:
            db = conn.cursor()
            
            # Check exist
            book_db = db.execute("SELECT * FROM books WHERE title = ? AND publisher = ? AND file_name = ?", (title, publisher, book_pdf_name,))
            
            if len(book_db.fetchall()) > 1:
                flash("this book exists") 
                return redirect(request.url)

            # Add book
            db.execute("INSERT INTO books (title, publisher, pages, creater_id, file_name) VALUES(?, ?, ?, ?, ?)", (title, publisher, pages, user_id, book_pdf_name,))

            # Get book
            book_db = db.execute("SELECT id FROM books WHERE title = ? AND publisher = ? AND pages = ? AND creater_id = ?", (title, publisher, pages, user_id,))
            book = book_db.fetchone()

            # Add history
            db.execute("INSERT INTO historys (title, user_id, book_id, action) VALUES(?, ?, ?, ?)", (title, user_id, book[0], "ADD",))

            conn.commit()

        flash("Book Added")
        return redirect("/")

    return render_template("add_book.html") 

@app.route("/account/remove_book", methods=["GET", "POST"])
@login_required
def Remove_book():

    user_id = session["user_id"]

    if request.method == "POST":

        book_id = request.form.get("id")

        if book_id:
            with sqlite3.connect(database_name) as conn:
                db = conn.cursor()

                # Remove book
                db.execute("DELETE FROM books WHERE id = ?", (book_id,))

                # Add history
                db.execute("INSERT INTO historys (title, user_id, book_id, action) VALUES(?, ?, ?, ?)", (request.form.get("title"), user_id, book_id, "REMOVE",))
                conn.commit()

        return redirect("/account/remove_book")

    with sqlite3.connect(database_name) as conn:
        db = conn.cursor()

        books_db = db.execute("SELECT * FROM books WHERE creater_id = ?", (user_id,))
        books = books_db.fetchall()

    return render_template("remove_book.html", books = books)

@app.route("/account/my_book", methods=["GET"])
@login_required
def My_book():
    user_id = session["user_id"]

    with sqlite3.connect(database_name) as conn:
        db = conn.cursor()

        books_db = db.execute("SELECT * FROM books WHERE creater_id = ?", (user_id,))
        books = books_db.fetchall()

    return render_template("my_book.html", books=books)

@app.route("/account", methods=["GET"])
@login_required
def account():
    return redirect("/account/my_book")

@app.route("/history", methods=["GET"])
@login_required
def Get_history():
    user_id = session["user_id"]

    with sqlite3.connect(database_name) as conn:
        db = conn.cursor()

        historys_db = db.execute("SELECT * FROM historys WHERE user_id = ? ORDER BY TIME DESC LIMIT 16", (user_id,))
        historys = historys_db.fetchall()


    return render_template("history.html", historys = historys)