from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash)  # Flask for creating the web application
from books import books  # Import the book data
from librarybooks import librarybooks
from librarybooksV2 import *

# Initialize Flask app
app = Flask(__name__)
# Database configuration
app.secret_key = "your_secret_key"  # Secret key for securely managing sessions in Flask
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/bookstore")
def bookstore():
    return render_template('bookstore.html', books=books)  # Pass the book data to the template


@app.route("/library")
def library_home():
    return render_template("library_home.html")


@app.route("/book-loan")
def book_loan():
    return render_template("book_loan.html", books=librarybooks)


@app.route("/audiobooks")
def audiobooks():
    return render_template("audiobooks.html")


@app.route("/enquiries")
def enquiries():
    return render_template("enquiries.html")


@app.route("/events")
def events():
    return render_template("events.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if email and password are provided
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html')

            # Open the shelve database
        with shelve.open('users.db') as db:
            if 'Users' in db:
                users = db['Users']
                # Loop through users to find if any user has the matching email
                if email in users and users[email]['password'] == password:
                    session['email'] = email  # Store email in session instead of username
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
                else:
                    flash('Invalid email or password', 'danger')
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('email', None)  # Remove 'email' from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Open the shelve database
        with shelve.open('users.db', writeback=True) as db:
            if 'Users' not in db:
                db['Users'] = {}

            users = db['Users']

            # Check if the email is already registered
            if any(user['email'] == email for user in users.values()):
                flash('Email already registered!', 'danger')
            else:
                # Add new user to the database
                users[email] = {'password': password, 'email': email}
                db['Users'] = users
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
    return render_template("sign_up.html")


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        with shelve.open('users.db') as db:
            if 'Users' in db:
                users = db['Users']
                # Loop through users to find if any user has the matching email
                for user_info in users.values():
                    if user_info['email'] == email:
                        flash(f'Password for {email}: {user_info["password"]}', 'info')
                        return redirect(url_for('login'))
        flash('Email not found!', 'danger')
    return render_template('forgot_password.html')


@app.route('/admin')
def admin_panel():
    if not session.get('email'):  # Ensure user is logged in
        flash('You must be logged in to access the admin panel.', 'danger')
        return redirect(url_for('login'))
    with shelve.open('users.db', 'r') as db:
        users = db.get('Users', {})
    return render_template('admin.html', users=users)


@app.route("/book-loanv2", methods=["GET", "POST"])
def book_loanv2():
    # Handle adding a new book
    if request.method == "POST" and "addBook" in request.form:
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        category = request.form["category"]
        description = request.form["description"]
        copies = int(request.form["copies"])

        with shelve.open("books.db", writeback=True) as db:
            if isbn in db:
                flash("A book with this ISBN already exists.", "danger")
            else:
                add_book(db, title, author, isbn, category, description, copies)
                flash("Book added successfully!", "success")
        return redirect(url_for("book_loanv2"))

    # Retrieve all books
    with shelve.open("books.db") as db:
        books = {isbn: vars(book) for isbn, book in db.items()}
    return render_template("book_loanv2.html", books=books)


@app.route("/deleteBook/<isbn>", methods=["POST"])
def delete_book_route(isbn):
    with shelve.open("books.db", writeback=True) as db:
        delete_book(db, isbn)
    flash(f"Book with ISBN {isbn} has been deleted.", "success")
    return redirect(url_for("book_loanv2"))


@app.route("/updateBook/<isbn>", methods=["POST"])
def update_book_route(isbn):
    with shelve.open("books.db", writeback=True) as db:
        if isbn in db:
            update_book(db, isbn)
            flash(f"Book with ISBN {isbn} has been updated.", "success")
    return redirect(url_for("book_loanv2"))


if __name__ == "__main__":
    app.run(debug=True)
