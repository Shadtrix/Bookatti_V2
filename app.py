from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash)  # Flask for creating the web application
from librarybooks import librarybooks
from librarybooksV2 import *
from bookstore_management import *
import random
import os
from werkzeug.utils import secure_filename
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Flask app
app = Flask(__name__, static_url_path='/static')
# Database configuration
app.secret_key = "your_secret_key"  # Secret key for securely managing sessions in Flask
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


def check_admin():
    """Helper function to check if the logged-in user is an admin."""
    if not session.get('email'):  # Check if the user is logged in
        flash('You must be logged in to access this page.', 'danger')
        return False

    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')  # Get logged-in user's email

        if user_email not in users or users[user_email].get('admin') != 1:
            flash('You do not have permission to access this page.', 'danger')
            return False
    return True


@app.route("/")
def home():
    user_email = session.get('email')  # Get the logged-in user's email

    # Open the users database to check the logged-in user's details
    with shelve.open('users.db') as db:
        users = db.get('Users', {})

        # If the user is logged in, get the current user's info
        if user_email in users:
            current_user = users.get(user_email)

            # Check if the logged-in user is an admin
            if current_user.get('admin') == 1:
                # Fetch contact messages if the user is an admin
                with shelve.open('contacts.db') as contact_db:
                    messages = contact_db.get('messages', [])
                return render_template('home.html', is_admin=True, messages=messages, users=users)

            # If the user is not an admin, just show their info
            return render_template('home.html', users={user_email: current_user})

    # If the user is not logged in, just render the home page without the admin info
    return render_template('home.html')


@app.route("/bookstore")
def bookstore():
    if 'email' not in session:  # Ensure user is logged in
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))
    # Retrieve book data from shelve database
    with shelve.open("bs_books.db") as db:
        books = {isbn: vars(book) for isbn, book in db.items()}
        # Shuffle the dictionary keys
        shuffled_keys = list(books.keys())
        random.shuffle(shuffled_keys)

        # Create a new dictionary with shuffled keys
        shuffled_books = {key: books[key] for key in shuffled_keys}
    return render_template('bookstore.html', books=shuffled_books)  # Pass the shuffled book data to the template


@app.route("/library")
def library_home():
    return render_template("library_home.html")


@app.route("/book-loan")
def book_loan():
    return render_template("book_loan.html", books=librarybooks)


@app.route("/audiobooks")
def audiobooks():
    return render_template("audiobooks.html")


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form['first']
        last_name = request.form['last']
        email = request.form['email']
        message = request.form['message']

        # Save the data into the shelve database
        with shelve.open('contacts.db', writeback=True) as db:
            if 'messages' not in db:
                db['messages'] = []  # Initialize as a list to store messages

            # Append the new message
            db['messages'].append({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'message': message
            })
        return redirect('/')  # Redirect back to the contact page
    return render_template("contact.html")


@app.route('/admin')
def admin_panel():
    if 'email' not in session:  # Ensure user is logged in
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))

    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')  # Get the logged-in user's email

        # Get the current user's information
        current_user = users.get(user_email)

        if not current_user:
            flash('User not found.', 'danger')
            return redirect(url_for('home'))

        # If the user is an admin, show all users. Otherwise, show only their info.
        if current_user.get('admin') == 1:
            is_admin = current_user.get('admin') == 1
            return render_template('admin.html', is_admin=is_admin, users=users)  # Show all users
        else:
            return render_template('admin.html', users={user_email: current_user})  # Show only logged-in user's info


@app.route('/admin/update/<username>', methods=['GET', 'POST'])
def update_user(username):
    # Ensure user is logged in
    if 'email' not in session:
        flash('You must be logged in to update your info.', 'danger')
        return redirect(url_for('login'))

    user_email = session.get('email')  # Get the logged-in user's email

    with shelve.open('users.db', writeback=True) as db:
        users = db.get('Users', {})
        user_info = users.get(username)

        if not user_info:
            flash('User not found!', 'danger')
            return redirect(url_for('home'))

        if request.method == 'POST':
            # Get updated data from the form
            new_email = request.form['email']
            new_password = request.form['password']

            # Update the user's data
            user_info['email'] = new_email
            user_info['password'] = new_password
            db['Users'] = users

            flash(f'User {username} updated successfully!', 'success')
            return redirect(url_for('home'))  # After updating, redirect to home

    return render_template('update_user.html', username=username, user_info=user_info)


@app.route('/admin/delete/<username>', methods=['POST'])
def delete_user(username):
    # Ensure user is logged in
    if 'email' not in session:
        flash('You must be logged in to delete your info.', 'danger')
        return redirect(url_for('login'))

    user_email = session.get('email')  # Get the logged-in user's email

    with shelve.open('users.db', writeback=True) as db:
        users = db.get('Users', {})

        # Delete the user account
        del users[username]
        db['Users'] = users
        flash(f'User {username} deleted successfully!', 'success')

    return redirect(url_for('home'))  # After deleting, redirect to home


@app.route('/admin/contacts')
def admin_contacts():
    # Check if the user is logged in
    user_email = session.get('email')  # Get the logged-in user's email

    # Open the users database to check the logged-in user's details
    with shelve.open('users.db') as db:
        users = db.get('Users', {})

        # If the user is logged in, get the current user's info
        if user_email and user_email in users:
            current_user = users.get(user_email)

            # Check if the logged-in user is an admin
            is_admin = current_user.get('admin') == 1

            # If the user is an admin, fetch contact messages
            with shelve.open('contacts.db') as contact_db:
                messages = contact_db.get('messages', [])

            return render_template('admin_contacts.html', messages=messages, is_admin=is_admin)

    # If the user is not logged in, redirect to login page
    flash('You must be logged in to access the admin contacts.', 'danger')
    return redirect(url_for('login'))


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
            flash('Please fill out all the required fields.', 'danger')
            return render_template('login.html')

            # Open the shelve database
        with shelve.open('users.db') as db:
            if 'Users' in db:
                users = db['Users']
                # Loop through users to find if any user has the matching email
                if email in users and users[email]['password'] == password:
                    session['email'] = email  # Store email in session instead of username
                    return redirect(url_for('home'))
                else:
                    flash('Invalid email or password', 'danger')
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('email', None)  # Remove 'email' from the session
    return redirect(url_for('home'))


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if the passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template("sign_up.html")

        # Open the shelve database
        with shelve.open('users.db', writeback=True) as db:
            if 'Users' not in db:
                db['Users'] = {}

            users = db['Users']

            # Check if the email is already registered
            if any(user['email'] == email for user in users.values()):
                flash('Email already registered!', 'danger')
            else:
                is_admin = 1 if email == "bookattiLibrary@gmail.com" else 0
                # Add new user to the database with the is_admin flag
                users[email] = {'username': username, 'password': password, 'email': email, 'admin': is_admin}
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
                # Find user with the given email
                for username, user_info in users.items():
                    if user_info['email'] == email:
                        flash('Email found! Proceed to reset your password.', 'success')
                        return redirect(url_for('reset_password', username=username))
        flash('Email not found!', 'danger')
    return render_template('forgot_password.html')


@app.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('reset_password', username=username))

        # Update password in Shelve
        with shelve.open('users.db') as db:
            if 'Users' in db:
                users = db['Users']
                if username in users:
                    users[username]['password'] = new_password  # Update the password
                    db['Users'] = users  # Save the changes
                    flash('Password successfully updated!', 'success')
                    return redirect(url_for('login'))
        flash('User not found!', 'danger')
        return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', username=username)


@app.route("/admin/book-loanv2", methods=["GET", "POST"])
def book_loanv2():
    if 'email' not in session:
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))

        # Open users database and check if logged-in user is an admin
    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')
        current_user = users.get(user_email, {})
        is_admin = current_user.get('admin', 0) == 1  # Ensure is_admin is set correctly

    if not is_admin:  # If not an admin, prevent access
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == "POST" and "addBook" in request.form:
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        category = request.form["category"]
        description = request.form["description"]
        copies = int(request.form["copies"])
        image = request.files.get("image")  # Get the uploaded image file

        # Handle image upload
        image_filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                filename = f"{base}_{counter}{ext}"
                counter += 1
            image.save(os.path.join(UPLOAD_FOLDER, filename))
            image_filename = filename

        with shelve.open("books.db", writeback=True) as db:
            if isbn in db:
                flash("A book with this ISBN already exists.", "danger")
            else:
                add_book(db, title, author, isbn, category, description, copies, image_filename)
                flash("Book added successfully!", "success")
        return redirect(url_for("book_loanv2"))

    with shelve.open("books.db") as db:
        books = {isbn: vars(book) for isbn, book in db.items()}
    return render_template("book_loanv2.html", books=books, is_admin=is_admin)


@app.route("/deleteBook/<isbn>", methods=["POST"])
def delete_book_route(isbn):
    with shelve.open("books.db", writeback=True) as db:
        delete_book(db, isbn)
    flash(f"Book with ISBN {isbn} has been deleted.", "success")
    return redirect(url_for("book_loanv2"))


@app.route("/updateBook/<isbn>", methods=["POST"])
def update_book_route(isbn):
    title = request.form.get("title")
    author = request.form.get("author")
    category = request.form.get("category")
    description = request.form.get("description")
    copies = request.form.get("copies")
    image = request.files.get("image")

    with shelve.open("books.db", writeback=True) as db:
        if isbn in db:
            book = db[isbn]
            book.title = title
            book.author = author
            book.category = category
            book.description = description
            book.copies = int(copies)

            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                    filename = f"{base}_{counter}{ext}"
                    counter += 1
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(image_path)
                book.image = filename

            db[isbn] = book
            flash(f"Book with ISBN {isbn} has been updated.", "success")
        else:
            flash(f"Book with ISBN {isbn} not found.", "danger")
    return redirect(url_for("book_loanv2"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_book(db, title, author, isbn, category, description, copies, image=None):
    book = Book(title, author, isbn, category, description, copies, image)
    db[isbn] = book
    print(f"Book '{title}' added successfully!")


@app.route('/borrowed-books', methods=['GET'])
def borrowed_books():
    borrowed_books_json = request.args.get('borrowedBooks')
    if borrowed_books_json:
        borrowed_books = json.loads(borrowed_books_json)
    else:
        borrowed_books = []

    return render_template('borrowed-books.html', borrowed_books=borrowed_books)

@app.route("/admin/bookstore-management", methods=["GET", "POST"])
def bookstore_management():
    if 'email' not in session:
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))

        # Open users database and check if logged-in user is an admin
    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')
        current_user = users.get(user_email, {})
        is_admin = current_user.get('admin', 0) == 1  # Ensure is_admin is set correctly

    if not is_admin:  # If not an admin, prevent access
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))

    # Handle adding a new book
    if request.method == "POST" and "addBook" in request.form:
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        category = request.form["category"]
        description = request.form["description"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])

        with shelve.open("bs_books.db", writeback=True) as db:
            if isbn in db:
                flash("A book with this ISBN already exists.", "danger")
            else:
                add_book(db, title, author, isbn, category, description, price, stock)
                flash("Book added successfully!", "success")
        return redirect(url_for("bookstore_management"))

    # Retrieve all books
    with shelve.open("bs_books.db") as db:
        books = {isbn: vars(book) for isbn, book in db.items()}
    return render_template("bookstore_management.html", books=books, is_admin=is_admin)


@app.route("/deletebsBook/<isbn>", methods=["POST"])
def delete_bs_book_route(isbn):
    with shelve.open("bs_books.db", writeback=True) as db:
        delete_bs_book(db, isbn)
    flash(f"Book with ISBN {isbn} has been deleted.", "success")
    return redirect(url_for("bookstore_management"))


@app.route("/updatebsBook/<isbn>", methods=["POST"])
def update_bs_book_route(isbn):
    title = request.form.get("title")
    author = request.form.get("author")
    category = request.form.get("category")
    description = request.form.get("description")
    price = request.form.get("price")
    stock = request.form.get("stock")

    with shelve.open("bs_books.db", writeback=True) as db:
        if isbn in db:
            book = db[isbn]
            book.title = title
            book.author = author
            book.category = category
            book.description = description
            book.price = float(price)
            book.stock = int(stock)
            db[isbn] = book
            flash(f"Book with ISBN {isbn} has been updated.", "success")
        else:
            flash(f"Book with ISBN {isbn} not found.", "danger")
    return redirect(url_for("bookstore_management"))

if __name__ == "__main__":
    app.run(debug=True)