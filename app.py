from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, flash)  # Flask for creating the web application
from flask import render_template
from books import books  # Import the book data
from librarybooks import librarybooks
import shelve

# Initialize Flask app
app = Flask(__name__)
# Database configuration
app.secret_key = "your_secret_key"  # Secret key for securely managing sessions in Flask
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


@app.route("/")
def home():
    # check if the users exist or not
    if not session.get("name"):
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
        username = request.form['username']
        password = request.form['password']

        # Open the shelve database
        with shelve.open('users.db') as db:
            if 'Users' in db:
                users = db['Users']
                if username in users and users[username]['password'] == password:
                    session['username'] = username
                    flash('Login successful!', 'success')
                    return redirect(url_for('home'))
            flash('Invalid username or password', 'danger')
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password'].lower()
        email = request.form['email']

        # Open the shelve database
        with shelve.open('users.db', writeback=True) as db:
            if 'Users' not in db:
                db['Users'] = {}

            users = db['Users']

            if username in users:
                flash('Username already exists!', 'danger')
            elif any(user['email'] == email for user in users.values()):
                flash('Email already registered!', 'danger')
            else:
                users[username] = {'password': password, 'email': email}
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
                for username, info in users.items():
                    if info['email'] == email:
                        flash(f'Password for {username}: {info["password"]}', 'info')
                        return redirect(url_for('login'))
        flash('Email not found!', 'danger')
    return render_template('forgot_password.html')


@app.route('/admin')
def admin_panel():
    with shelve.open('users.db', 'r') as db:
        users = db.get('Users', {})
    return render_template('admin.html', users=users)


if __name__ == "__main__":
    app.run(debug=True)
