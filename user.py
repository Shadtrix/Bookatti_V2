import shelve


class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return f"Book(username={self.username}, email={self.email}, password={self.password})"
