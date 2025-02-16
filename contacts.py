import shelve

DB_NAME = "contacts.db"


class Contacts:
    def __init__(self, first_name, last_name, email, message):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.message = message

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "message": self.message
        }

    def __repr__(self):
        return f"User(first_name={self.first_name}, last_name={self.last_name}, email={self.email}, message={self.message})"


def save_contact(user):
    with shelve.open(DB_NAME) as db:
        messages = db.get('messages', [])
        messages.append(user.to_dict())
        db['messages'] = messages


def get_all_contacts():
    with shelve.open(DB_NAME) as db:
        return db.get('messages', [])
