import shelve
import json
import os
from bookstore_management import update_bs_bookBS


def process_checkout(cart_data):
    try:
        with shelve.open('bs_books.db', writeback=True) as db:
            for item in cart_data:
                isbn = item["isbn"]
                quantity = int(item["quantity"])
                if update_bs_bookBS(db, isbn, quantity):
                    print(f"Stock updated for {isbn}.")
                else:
                    print(f"Not enough stock for {isbn}.")
    except Exception as e:
        print(f"Error processing checkout: {str(e)}")
