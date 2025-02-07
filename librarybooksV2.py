import shelve


class Book:
    def __init__(self, title, author, isbn, category, description, copies):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.category = category
        self.description = description
        self.copies = copies

    def __repr__(self):
        return f"Book(title={self.title}, author={self.author}, isbn={self.isbn}, category={self.category}, description={self.description}, copies={self.copies})"


def add_book(db, title, author, isbn, category, description, copies):
    book = Book(title, author, isbn, category, description, copies)
    db[isbn] = book
    print(f"Book '{title}' added successfully!")


def get_book(db, isbn):
    return db.get(isbn, None)


def list_books(db):
    if db:
        print("\nBooks in the database:")
        for book in db.values():
            print(book)
    else:
        print("No books in the database.")


def delete_book(db, isbn):
    if isbn in db:
        del db[isbn]
        print(f"Book with ISBN {isbn} has been deleted.")
    else:
        print(f"Book with ISBN {isbn} not found in the database.")


def update_book(db, isbn):
    if isbn in db:
        print(f"Updating book with ISBN {isbn}.")
        book = db[isbn]

        new_title = input(f"Enter new title (leave blank to keep '{book.title}'): ")
        new_author = input(f"Enter new author (leave blank to keep '{book.author}'): ")
        new_category = input(f"Enter new category (leave blank to keep '{book.category}'): ")
        new_description = input(f"Enter new description (leave blank to keep '{book.description}'): ")
        new_copies = input(f"Enter new number of copies (leave blank to keep {book.copies}): ")
        new_copies = int(new_copies) if new_copies else book.copies

        book.title = new_title
        book.author = new_author
        book.category = new_category
        book.description = new_description
        book.copies = new_copies

        db[isbn] = book
        print(f"Book with ISBN {isbn} has been updated.")
    else:
        print(f"Book with ISBN {isbn} not found in the database.")


def input_book_details(db):
    while True:
        title = input("Enter book title: ")
        author = input("Enter author name: ")
        isbn = input("Enter ISBN: ")
        category = input("Enter category (e.g., Fiction, Non-Fiction, etc.): ").lower()
        description = input("Enter a short description of the book: ")
        copies = int(input("Enter number of copies available: "))
        add_book(db, title, author, isbn, category, description, copies)
        continue_adding = input("Do you want to add another book? (y/n): ").strip().lower()
        if continue_adding != 'y':
            break


def main_screen(db):
    while True:
        print("\n--- Main Menu ---")
        print("1. Add a Book")
        print("2. List All Books")
        print("3. Delete a Book")
        print("4. Update a Book")
        print("5. Exit")
        choice = input("Choose an option (1-5): ")

        if choice == '1':
            input_book_details(db)
        elif choice == '2':
            list_books(db)
        elif choice == '3':
            isbn = input("Enter ISBN of the book to delete: ")
            delete_book(db, isbn)
        elif choice == '4':
            isbn = input("Enter ISBN of the book to update: ")
            update_book(db, isbn)
        elif choice == '5':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please select a valid option.")


def main():
    with shelve.open('books.db') as db:
        main_screen(db)


if __name__ == "__main__":
    main()
