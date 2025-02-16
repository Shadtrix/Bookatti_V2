
from flask import (Flask, render_template, request,
                   redirect, url_for, session, flash, send_from_directory)
from librarybooksV2 import *
from bookstore_management import *
from librarybooksV2 import delete_book, Book
from bookstore_management import add_bookBS, delete_bs_bookBS
import random
import os
from werkzeug.utils import secure_filename
from process_orders import *
import struct

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["AUDIO_UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static', 'uploads', 'audio')
app.config["EVENTS_UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static', 'uploads', 'events')
app.config["IMAGE_UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static', 'uploads', 'images')


os.makedirs(app.config["IMAGE_UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["AUDIO_UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["EVENTS_UPLOAD_FOLDER"], exist_ok=True)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.secret_key = "your_secret_key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


def check_admin():
    """Helper function to check if the logged-in user is an admin."""
    if not session.get('email'):
        flash('You must be logged in to access this page.', 'danger')
        return False

    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')

        if user_email not in users or users[user_email].get('admin') != 1:
            return False
    return True


@app.route("/")
def home():
    return render_template('home.html')


@app.route('/process-checkout', methods=['POST'])
def process_checkout():
    """Processes checkout and updates stock dynamically."""
    try:
        cart_data = request.json

        if not cart_data:
            return {"message": "No items in the cart."}, 400

        with shelve.open('bs_books.db', writeback=True) as db:
            for item in cart_data:
                isbn = item["isbn"]
                quantity = int(item["quantity"])
                if isbn in db:
                    book = db[isbn]
                    if book.stock >= quantity:
                        book.stock -= quantity
                        db[isbn] = book
                    else:
                        return {"message": f"Not enough stock for {book.title}. Available: {book.stock}"}, 400

        return {"message": "Checkout successful! Stock updated."}, 200

    except Exception as e:
        return {"message": f"Error processing checkout: {str(e)}"}, 500


@app.route("/bookstore")
def bookstore():
    if 'email' not in session:
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))
    with shelve.open("bs_books.db") as db:
        books = {isbn: vars(book) for isbn, book in db.items()}
        shuffled_keys = list(books.keys())
        random.shuffle(shuffled_keys)

        shuffled_books = {key: books[key] for key in shuffled_keys}
    return render_template('bookstore.html', books=shuffled_books)


@app.route("/library")
def library_home():
    return render_template("library_home.html")


@app.route('/book-loan')
def book_loan():
    if 'email' not in session:
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))
    with shelve.open('books.db') as db:
        books = []
        for book in db.values():
            if not hasattr(book, 'image'):
                continue

            if hasattr(book, 'category'):
                category = (
                    book.category.strip().lower()
                    .replace(' & ', '-')
                    .replace(' ', '-')
                    .replace('_', '-')
                )
            else:
                category = 'uncategorized'

            books.append({
                'title': book.title,
                'author': book.author,
                'isbn': book.isbn,
                'category': category,
                'image': book.image if book.image else 'default.jpg'
            })

    return render_template("book_loan.html", books=books)

@app.route('/audiobooks')
def audiobooks_page():
    with shelve.open("audiobooks.db") as db:
        audiobooks_data = db.get("Audiobooks", {})

    return render_template("audiobooks.html", audiobooks=audiobooks_data)

@app.route('/admin/audiobooks', methods=['GET', 'POST'])
def admin_audiobooks():
    if not check_admin():
        return redirect(url_for('home'))

    with shelve.open("audiobooks.db", writeback=True) as db:
        audiobooks = db.get("Audiobooks", {})

        if request.method == 'POST':
            if 'audio' not in request.files:
                flash('No audio file part', 'error')
            else:
                audio = request.files['audio']
                if audio.filename == '':
                    flash('No selected file', 'error')
                else:
                    filename = secure_filename(audio.filename)
                    audio_path = os.path.join(app.config["AUDIO_UPLOAD_FOLDER"], filename)
                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    audio.save(audio_path)

                    if audiobooks:
                        existing_ids = [int(id) for id in audiobooks.keys()]
                        audiobook_id = str(max(existing_ids) + 1)
                    else:
                        audiobook_id = '1'

                    audiobooks[audiobook_id] = {
                        'title': request.form['title'],
                        'author': request.form['author'],
                        'audio_file': filename
                    }
                    db["Audiobooks"] = audiobooks

                    flash('Audio uploaded successfully', 'success')
                    return redirect(url_for('admin_audiobooks'))

        return render_template("admin_audiobooks.html", audiobooks=audiobooks)


@app.route('/admin/updateAudiobook/<audiobook_id>', methods=['POST'])
def update_audiobook(audiobook_id):
    with shelve.open("audiobooks.db", writeback=True) as db:
        audiobooks = db.get("Audiobooks", {})

        if audiobook_id in audiobooks:
            audiobooks[audiobook_id]['title'] = request.form['title']
            audiobooks[audiobook_id]['author'] = request.form['author']

            if 'audio' in request.files and request.files['audio'].filename != '':
                audio = request.files['audio']
                filename = secure_filename(audio.filename)
                audio_path = os.path.join(app.config["AUDIO_UPLOAD_FOLDER"], filename)

                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                audio.save(audio_path)

                audiobooks[audiobook_id]['audio_file'] = filename

            db["Audiobooks"] = audiobooks
            flash('Audiobook updated successfully!', 'success')
        else:
            flash('Audiobook not found!', 'danger')

    return redirect(url_for('admin_audiobooks'))


@app.route('/admin/delete_audiobook/<audiobook_id>', methods=['POST'])
def delete_audiobook(audiobook_id):
    with shelve.open("audiobooks.db", writeback=True) as db:
        audiobooks = db.get("Audiobooks", {})

        if audiobook_id in audiobooks:
            del audiobooks[audiobook_id]
            db["Audiobooks"] = audiobooks
            flash("Audiobook deleted successfully!", "success")
        else:
            flash("Audiobook not found!", "danger")

    return redirect(url_for('admin_audiobooks'))


app.config["AUDIO_UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")


@app.route('/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(app.config["AUDIO_UPLOAD_FOLDER"], filename)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form['first']
        last_name = request.form['last']
        email = request.form['email']
        message = request.form['message']

        with shelve.open('contacts.db', writeback=True) as db:
            if 'messages' not in db:
                db['messages'] = []
            db['messages'].append({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'message': message
            })

        return redirect('/')

    return render_template("contact.html")


@app.route('/admin')
def admin_panel():
    if 'email' not in session:
        flash('You must be logged in to access this page.', 'danger')
        return redirect(url_for('login'))

    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')

        current_user = users.get(user_email)

        if not current_user:
            flash('User not found.', 'danger')
            return redirect(url_for('home'))

        is_admin = current_user.get('admin') == 1

        if is_admin:
            return render_template(
                'admin.html',
                is_admin=True,
                users=users,
                contacts_url=url_for('admin_contacts'),
                bookstore_management_url=url_for('bookstore_management'),
                book_loanv2_url=url_for('book_loanv2'),
                admin_audiobooks_url=url_for('admin_audiobooks'),
                admin_events_url=url_for('admin_events')
            )
        else:
            return render_template(
                'admin.html',
                is_admin=False,
                users={user_email: current_user}
            )


@app.route('/admin/update/<username>', methods=['GET', 'POST'])
def update_user(username):
    if 'email' not in session:
        flash('You must be logged in to update your info.', 'danger')
        return redirect(url_for('login'))

    user_email = session.get('email')

    with shelve.open('users.db', writeback=True) as db:
        users = db.get('Users', {})
        user_info = users.get(username)

        if not user_info:
            flash('User not found!', 'danger')
            return redirect(url_for('home'))

        if request.method == 'POST':
            new_email = request.form['email']
            new_password = request.form['password']

            user_info['email'] = new_email
            user_info['password'] = new_password
            db['Users'] = users

            flash(f'User {username} updated successfully!', 'success')
            return redirect(url_for('home'))

    return render_template('update_user.html', username=username, user_info=user_info)


@app.route('/admin/delete/<username>', methods=['POST'])
def delete_user(username):
    if 'email' not in session:
        flash('You must be logged in to delete your info.', 'danger')
        return redirect(url_for('login'))

    user_email = session.get('email')

    with shelve.open('users.db', writeback=True) as db:
        users = db.get('Users', {})

        del users[username]
        db['Users'] = users
        flash(f'User {username} deleted successfully!', 'success')

    return redirect(url_for('home'))


@app.route('/admin/contacts')
def admin_contacts():
    if not check_admin():
        return redirect(url_for('home'))

    with shelve.open('contacts.db') as contact_db:
        messages = contact_db.get('messages', [])

    return render_template('admin_contacts.html', messages=messages)


@app.route("/events")
def public_events():
    with shelve.open('events.db') as db:
        events = db.get('Events', {})

    return render_template("events.html", events=events)


@app.route('/admin/events', methods=['GET', 'POST'])
def admin_events():
    if not check_admin():
        return redirect(url_for('home'))  # Redirect non-admins

    with shelve.open('events.db', writeback=True) as db:
        if 'Events' not in db:
            db['Events'] = {}

        events = db['Events']

        if request.method == 'POST':
            title = request.form.get('title')
            author = request.form.get('author')
            description = request.form.get('description')

            if not title or not author or not description:
                flash("Please fill in all required fields.", "danger")
                return redirect(url_for('admin_events'))

            if len(description) > 5000:
                flash("Description is too long. Please shorten it.", "danger")
                return redirect(url_for('admin_events'))

            image = request.files.get('image')
            image_filename = None
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = app.config["EVENTS_UPLOAD_FOLDER"]
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(upload_folder, filename)):
                    filename = f"{base}_{counter}{ext}"
                    counter += 1
                image.save(os.path.join(app.config["EVENTS_UPLOAD_FOLDER"], filename))
                image_filename = filename

            event_id = str(len(events) + 1)
            while event_id in events:
                event_id = str(int(event_id) + 1)

            events[event_id] = {
                'title': title,
                'author': author,
                'description': description,
                'image': image_filename
            }

            db['Events'] = events
            flash('Event added successfully!', 'success')

            return redirect(url_for('admin_events'))

    return render_template("admin_events.html", events=events)


@app.route('/updateEvent/<event_id>', methods=['POST'])
def update_event(event_id):
    with shelve.open('events.db', writeback=True) as db:
        events = db.get('Events', {})

        if event_id in events:
            event = events[event_id]
            event['title'] = request.form.get('title', event['title'])
            event['author'] = request.form.get('author', event['author'])
            event['description'] = request.form.get('description', event['description'])

            image = request.files.get('image')
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                upload_folder = app.config["EVENTS_UPLOAD_FOLDER"]
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(upload_folder, filename)):
                    filename = f"{base}_{counter}{ext}"
                    counter += 1
                image.save(os.path.join(upload_folder, filename))
                event['image'] = filename

            db['Events'] = events
            flash('Event updated successfully!', 'success')

    return redirect(url_for('admin_events'))


@app.route('/deleteEvent/<event_id>', methods=['POST'])
def delete_event(event_id):
    with shelve.open('events.db', writeback=True) as db:
        events = db.get('Events', {})

        if event_id in events:
            del events[event_id]
            db['Events'] = events
            flash('Event deleted successfully!', 'success')
        else:
            flash('Event not found.', 'danger')

    return redirect(url_for('admin_events'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Please fill out all the required fields.', 'danger')
            return render_template('login.html')

        with shelve.open('users.db') as db:
            if 'Users' in db:
                users = db['Users']
                if email in users and users[email]['password'] == password:
                    session['email'] = email
                    return redirect(url_for('home'))
                else:
                    flash('Invalid email or password', 'danger')
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('home'))


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template("sign_up.html")

        with shelve.open('users.db', writeback=True) as db:
            if 'Users' not in db:
                db['Users'] = {}

            users = db['Users']

            if any(user['email'] == email for user in users.values()):
                flash('Email already registered!', 'danger')
            else:
                is_admin = 1 if email == "bookattiLibrary@gmail.com" else 0
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

        with shelve.open('users.db') as db:
            if 'Users' in db:
                users = db['Users']
                if username in users:
                    users[username]['password'] = new_password
                    db['Users'] = users
                    flash('Password successfully updated!', 'success')
                    return redirect(url_for('login'))
        flash('User not found!', 'danger')
        return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', username=username)


@app.route("/admin/book-loanv2", methods=["GET", "POST"])
def book_loanv2():
    if not check_admin():
        return redirect(url_for('home'))

    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')
        current_user = users.get(user_email, {})
        is_admin = current_user.get('admin', 0) == 1

    if not is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == "POST" and "addBook" in request.form:
        title = request.form["title"]
        author = request.form["author"]
        isbn = request.form["isbn"]
        category = request.form["category"]
        description = request.form["description"]
        copies = int(request.form["copies"])
        image = request.files.get("image")

        image_filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            upload_folder = app.config["IMAGE_UPLOAD_FOLDER"]
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(upload_folder, filename)):
                filename = f"{base}_{counter}{ext}"
                counter += 1
            image.save(os.path.join(app.config["IMAGE_UPLOAD_FOLDER"], filename))
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
                upload_folder = app.config["IMAGE_UPLOAD_FOLDER"]
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(upload_folder, filename)):
                    filename = f"{base}_{counter}{ext}"
                    counter += 1
                image.save(os.path.join(upload_folder, filename))
                book.image = filename

            db[isbn] = book
            flash(f"Book with ISBN {isbn} has been updated.", "success")
        else:
            flash(f"Book with ISBN {isbn} not found.", "danger")
    return redirect(url_for("book_loanv2"))


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

def read_book_metadata(offset, length, file_path='books.db.dat'):
    try:
        with open(file_path, 'rb') as file:
            file.seek(offset)
            metadata = file.read(length).decode('utf-8', errors='ignore')
            print(f"Metadata for offset {offset}: {metadata}")  # Debugging line
            return metadata
    except Exception as e:
        print(f"Error reading metadata at offset {offset}: {e}")
        return None

def read_books_db(file_path='books.db.dat'):
    books = []
    try:
        with open(file_path, 'rb') as file:
            while True:
                isbn = file.read(13).decode('utf-8').strip()
                if not isbn:
                    break

                offset, length = struct.unpack('ii', file.read(8))


                metadata = read_book_metadata(offset, length)
                if metadata:
                    title, author, category = metadata.split('|')
                    category = category.strip() if category else 'uncategorized'
                    books.append({
                        'isbn': isbn,
                        'title': title,
                        'author': author,
                        'category': category,
                        'offset': offset,
                        'length': length
                    })
    except Exception as e:
        print(f"Error reading books: {e}")
    return books


@app.route('/books_loan', methods=['GET', 'POST'])
def books_loan():
    books = read_books_db()
    for book in books:
        print(f"Book {book['title']} has category: {book['category']}")

    if request.method == 'POST':
        category_filter = request.form.get('category')
        print(f"Category filter selected: {category_filter}")
        if category_filter and category_filter != 'all':
            books = [book for book in books if book['category'] == category_filter]

    return render_template('book_loan.html', books=books)

@app.route("/admin/bookstore-management", methods=["GET", "POST"])
def bookstore_management():
    if not check_admin():
        return redirect(url_for('home'))

    with shelve.open('users.db') as db:
        users = db.get('Users', {})
        user_email = session.get('email')
        current_user = users.get(user_email, {})
        is_admin = current_user.get('admin', 0) == 1

    if not is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))

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
                add_bookBS(db, title, author, isbn, category, description, price, stock)
                flash("Book added successfully!", "success")
        return redirect(url_for("bookstore_management"))

    with shelve.open("bs_books.db") as db:
        books = {isbn: vars(book) for isbn, book in db.items()}
    return render_template("bookstore_management.html", books=books, is_admin=is_admin)


@app.route("/deletebsBook/<isbn>", methods=["POST"])
def delete_bs_book_route(isbn):
    with shelve.open("bs_books.db", writeback=True) as db:
        delete_bs_bookBS(db, isbn)
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
