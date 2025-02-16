import shelve

DB_NAME = "contacts.db"

class User:
    def __init__(self, first_name, last_name, email, message):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.message = message

    def to_dict(self):
        """Convert the object to a dictionary for easy storage."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "message": self.message
        }

    def __repr__(self):
        return f"User(first_name={self.first_name}, last_name={self.last_name}, email={self.email}, message={self.message})"


def save_user(user):
    """Saves a User object to the shelve database."""
    with shelve.open(DB_NAME) as db:
        messages = db.get('messages', [])
        messages.append(user.to_dict())  # Convert object to dictionary
        db['messages'] = messages  # Update database

def get_all_users():
    """Retrieves all users/messages from the database."""
    with shelve.open(DB_NAME) as db:
        return db.get('messages', [])