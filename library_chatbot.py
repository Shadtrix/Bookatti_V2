import spacy
from flask import Flask, render_template, request, jsonify
from rapidfuzz import fuzz
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"

LIBRARY_PROMPTS = [
    '"Is [book name] available for borrowing?"',
    '"Who wrote [book name]?"',
    '"What is the ISBN of [book name]?"',
    '"How many copies of [book name] are available?"',
    '"Can I reserve [book name]?"',
    '"What is the borrowing limit?"',
    '"What are the due dates for my borrowed books?"',
    '"Show all information about [book name]."',
]

nlp = spacy.load("en_core_web_sm")

library_inventory = {
    "Harry Potter": [{"author": "J.K. Rowling", "copies": 5, "isbn": "9780439554930", "availability": "available"}],
    "The Hobbit": [{"author": "J.R.R. Tolkien", "copies": 3, "isbn": "9780547928227", "availability": "available"}],
    "1984": [{"author": "George Orwell", "copies": 0, "isbn": "9780451524935", "availability": "unavailable"}],
    "Pride and Prejudice": [{"author": "Jane Austen", "copies": 7, "isbn": "9781503290563", "availability": "available"}],
    "To Kill a Mockingbird": [{"author": "Harper Lee", "copies": 4, "isbn": "9780061120084", "availability": "available"}],
    "The Great Gatsby": [{"author": "F. Scott Fitzgerald", "copies": 6, "isbn": "9780743273565", "availability": "available"}],
    "Moby Dick": [{"author": "Herman Melville", "copies": 2, "isbn": "9781503280786", "availability": "available"}],
    "The Catcher in the Rye": [{"author": "J.D. Salinger", "copies": 5, "isbn": "9780316769488", "availability": "available"}],
    "Little Women": [{"author": "Louisa May Alcott", "copies": 4, "isbn": "9781503280298", "availability": "available"}],
    "The Lord of the Rings": [{"author": "J.R.R. Tolkien", "copies": 1, "isbn": "9780544003415", "availability": "available"}],
    "Joyland": [
        {"author": "Stephen King", "copies": 6, "isbn": "9781781162644", "availability": "available"},
        {"author": "Emily Schultz", "copies": 3, "isbn": "9781550227215", "availability": "available"}
    ],
}

library_query_map = {
    "availability": ["available", "in stock", "do you have", "borrow"],
    "author": ["author", "writer", "who wrote"],
    "isbn": ["isbn", "identifier", "book number"],
    "copies": ["copies", "how many", "number of copies"],
    "reserve": ["reserve", "hold"],
    "due_date": ["due date", "return date", "deadline"],
    "borrowing_limit": ["borrowing limit", "how many books can I borrow"],
    "return": ["return", "how to return"],
}

def extract_book_titles(user_input):
    doc = nlp(user_input)
    titles = []

    for ent in doc.ents:
        if ent.label_ in ["WORK_OF_ART", "PRODUCT"]:
            titles.append(ent.text)

    for title in library_inventory.keys():
        if fuzz.partial_ratio(title.lower(), user_input.lower()) > 70:
            titles.append(title)

    return list(set(titles))

def detect_library_query_types(user_input):
    detected_queries = []
    user_input = user_input.lower()

    if "show all information about" in user_input:
        return ["availability", "author", "isbn", "copies"]

    for query_type, keywords in library_query_map.items():
        if any(keyword in user_input for keyword in keywords):
            detected_queries.append(query_type)

    if re.search(r"do you have\s+.+", user_input):
        detected_queries.append("availability")

    if "borrowing limit" in user_input or "how many books can i borrow" in user_input:
        detected_queries.append("borrowing_limit")

    if "due date" in user_input or "return date" in user_input or "deadline" in user_input:
        detected_queries.append("due_date")

    return detected_queries

def generate_library_response(query_types, book_details=None):
    responses = []

    # Handle general queries like borrowing limit or due dates
    if "borrowing_limit" in query_types:
        responses.append("You can borrow up to 5 books at a time from the library.")
    if "due_date" in query_types:
        responses.append("Please log in to your library account to check the due dates for your borrowed books.")

    # Handle book-specific queries
    if book_details:
        title = book_details.get("title", "Unknown")
        author = book_details.get("author", "Unknown")
        copies = book_details.get("copies", 0)
        availability = book_details.get("availability", "unknown")
        isbn = book_details.get("isbn", "unavailable")

        if "availability" in query_types and "copies" not in query_types:
            if availability == "available":
                responses.append(f"'{title}' by {author} is available for borrowing.")
            else:
                responses.append(f"'{title}' by {author} is unavailable.")
        if "copies" in query_types:
            responses.append(f"There are {copies} copies of '{title}' available for borrowing.")
        if "author" in query_types:
            responses.append(f"The author of '{title}' is {author}.")
        if "isbn" in query_types:
            responses.append(f"The ISBN of '{title}' is {isbn}.")
        if "reserve" in query_types:
            if availability == "available":
                responses.append(f"You can reserve '{title}' by {author}. Please visit the library or use the online reservation system.")
            else:
                responses.append(f"'{title}' by {author} is unavailable, so reservation may not be possible.")

    return " ".join(responses) if responses else "I'm sorry, I couldn't understand your query. Please try rephrasing it."

@app.route("/")
def home():
    return render_template("library_chatbot.html", suggested_prompts=LIBRARY_PROMPTS)

@app.route("/chat", methods=["POST"])
def library_chat():
    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        return jsonify({
            "response": "How may I assist you? Here are some things you can ask me:",
            "suggested_prompts": LIBRARY_PROMPTS,
        })

    if user_input.isdigit() or len(user_input) < 2:
        return jsonify({
            "response": "I'm sorry, I couldn't understand your input. Please try asking about a book, such as its availability or author.",
        })

    query_types = detect_library_query_types(user_input)

    general_queries = ["borrowing_limit", "due_date"]
    responses = []

    # Handle general queries
    if any(query in query_types for query in general_queries):
        if "borrowing_limit" in query_types:
            responses.append("You can borrow up to 5 books at a time from the library.")
        if "due_date" in query_types:
            responses.append("Please log in to your library account to check the due dates for your borrowed books.")

    # Handle book-specific queries
    book_titles = extract_book_titles(user_input)
    if book_titles:
        for title in book_titles:
            books = library_inventory.get(title, [])
            if len(books) > 1:  # Multiple authors for the same title
                if "by" in user_input.lower():  # Check if the user specified an author
                    specified_author = user_input.split("by")[-1].strip().lower()
                    matching_books = [
                        book for book in books if fuzz.partial_ratio(book["author"].lower(), specified_author) > 70
                    ]
                    if matching_books:
                        book_details = matching_books[0]
                        book_details["title"] = title
                        responses.append(generate_library_response(query_types, book_details=book_details))
                    else:
                        responses.append(f"Sorry, I couldn't find '{title}' by {specified_author}. Please try again.")
                else:
                    authors = [book["author"] for book in books]
                    responses.append(f"There are multiple books with the title '{title}'. Please specify the author: by {', '.join(authors)}.")
            else:
                book_details = books[0]
                book_details["title"] = title
                responses.append(generate_library_response(query_types, book_details=book_details))

    if not responses:
        responses.append("Sorry, I couldn't find any books matching your query. Can you rephrase or provide more details?")

    return jsonify({"response": " ".join(responses)})

if __name__ == "__main__":
    app.run(debug=True, port=5002)
