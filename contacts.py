import shelve


class Contact:
    def __init__(self, first_name, last_name, email, message):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.message = message

    def __repr__(self):
        return f"Book(first_name={self.first_name}, last_name={self.last_name}, email={self.email}, message={self.message})"
