import shelve

DB_NAME = "users.db"


class User:
    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.password = password  # In a real app, use hashed passwords!
        self.is_admin = is_admin

    def to_dict(self):
        """Convert the object to a dictionary for database storage."""
        return {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "is_admin": self.is_admin
        }

    def __repr__(self):
        return f"User(username={self.username}, email={self.email}, admin={self.is_admin})"


def save_user(user):
    """Saves a User object to the database."""
    with shelve.open(DB_NAME, writeback=True) as db:
        if 'Users' not in db:
            db['Users'] = {}

        users = db['Users']

        if user.email in users:
            return False  # Email already registered

        users[user.email] = user.to_dict()
        db['Users'] = users
        return True  # Registration successful


def user_exists(email):
    """Checks if a user with the given email already exists."""
    with shelve.open(DB_NAME) as db:
        users = db.get('Users', {})
        return email in users


def get_user(email):
    """Retrieves a user by email."""
    with shelve.open(DB_NAME) as db:
        users = db.get('Users', {})
        return users.get(email, None)
    