import shelve


class Book:
    def __init__(self, title, author, isbn, category, description, price, stock):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.category = category
        self.description = description
        self.price = float(price)
        self.stock = int(stock)

    def __repr__(self):
        return f"Book(title={self.title}, author={self.author}, isbn={self.isbn}, category={self.category}, description={self.description}, price={self.price}, stock={self.stock})"


def add_book(db, title, author, isbn, category, description, price, stock):
    book = Book(title, author, isbn, category, description, price, stock)
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


def delete_bs_book(db, isbn):
    if isbn in db:
        del db[isbn]
        print(f"Book with ISBN {isbn} has been deleted.")
    else:
        print(f"Book with ISBN {isbn} not found in the database.")


def update_bs_book(db, isbn, quantity_purchased=None):
    if isbn in db:
        book = db[isbn]

        if quantity_purchased is not None:  # If reducing stock
            if book.stock >= quantity_purchased:
                book.stock -= quantity_purchased
                db[isbn] = book  # Ensure stock update is saved
                print(f"Stock updated: {book.stock} remaining for ISBN {isbn}.")
                return True
            else:
                print(f"Not enough stock for ISBN {isbn}. Available: {book.stock}, Required: {quantity_purchased}")
                return False

        new_title = input(f"Enter new title (leave blank to keep '{book.title}'): ")
        new_author = input(f"Enter new author (leave blank to keep '{book.author}'): ")
        new_category = input(f"Enter new category (leave blank to keep '{book.category}'): ")
        new_description = input(f"Enter new description (leave blank to keep '{book.description}'): ")
        new_price = input(f"Enter new price (leave blank to keep '{book.price}'): ")
        new_stock = input(f"Enter new number of stock (leave blank to keep {book.stock}): ")
        new_stock = int(new_stock) if new_stock else book.stock

        book.title = new_title
        book.author = new_author
        book.category = new_category
        book.description = new_description
        book.price = new_price
        book.stock = new_stock

        db[isbn] = book  # Save changes
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
        price = input("Enter the price of the book: ")
        stock = int(input("Enter number of stock available: "))
        add_book(db, title, author, isbn, category, description, price, stock)
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
            delete_bs_book(db, isbn)
        elif choice == '4':
            isbn = input("Enter ISBN of the book to update: ")
            update_bs_book(db, isbn)
        elif choice == '5':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please select a valid option.")


def main():
    with shelve.open('bs_books') as db:
        main_screen(db)


if __name__ == "__main__":
    main()