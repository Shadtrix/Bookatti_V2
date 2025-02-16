import shelve
import spacy  # for natural language processing (NLP)
from flask import Flask, render_template, request, jsonify
from rapidfuzz import fuzz  # fuzzy string matching to handle approximate text matches
import re  # for pattern
import logging
from bookstore_management import *

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Secret key for securely managing sessions in Flask

# Load SpaCy's small English model for processing user input
nlp = spacy.load("en_core_web_sm")

BOOKSTORE_PROMPTS = [
    "How much does [book name] cost?",
    "Is [book name] available?",
    "Who wrote [book name]?",
    "What is the ISBN of [book name]?",
    "Show all information about [book name].",
]


def get_books():
    """Retrieve all books from the shelve database without modifying it."""
    books = {}
    with shelve.open('bs_books.db', flag='r') as db:  # Open in read-only mode
        books = dict(db)  # Convert to dictionary to avoid reference issues
    logging.debug(f"Books retrieved from shelve: {books}")
    return books


def extract_book_title(user_input):
    """Try to extract a book title from the user input."""
    books = get_books()
    if not books:
        logging.debug("No books found in database.")
        return None

    best_match = None
    best_score = 0
    for isbn, book in books.items():
        score = fuzz.partial_ratio(book.title.lower(), user_input.lower())
        logging.debug(f"Matching '{user_input}' against '{book.title}' - Score: {score}")
        if score > best_score:
            best_match = book
            best_score = score

    if best_match and best_score > 70:
        logging.debug(f"Best match found: {best_match.title} with score {best_score}")
        return best_match
    else:
        logging.debug("No suitable book match found.")
        return None


def detect_bookstore_query_types(user_input):
    """Detect the type(s) of query in user input, such as asking for price or availability."""
    detected_queries = []
    user_input = user_input.lower()

    if "show all information about" in user_input:
        return ["price", "author", "availability", "isbn"]

    for query_type, keywords in {
        "price": ["price", "cost", "how much"],
        "availability": ["available", "in stock", "do you have"],
        "author": ["author", "writer", "who wrote"],
        "isbn": ["isbn", "identifier", "book number"]
    }.items():
        if any(keyword in user_input for keyword in keywords):
            detected_queries.append(query_type)

    if re.search(r"do you have\s+.+", user_input):
        detected_queries.append("availability")

    return detected_queries


def generate_bookstore_response(query_types, book):
    """Generate a response for the user's query based on detected query types and book information."""
    title = book.title
    author = book.author
    stock = book.stock
    availability_status = "available" if stock > 0 else "out of stock"

    response_templates = {
        "price": f"The price of '{title}' by {author} is ${book.price}.",
        "author": f"The author of '{title}' is {author}.",
        "availability": f"'{title}' by {author} is currently {availability_status}. Stock available: {stock}.",
        "isbn": f"The ISBN of '{title}' by {author} is {book.isbn}.",
    }

    responses = [response_templates[query] for query in query_types if query in response_templates]
    return " ".join(responses)


@app.route("/")
def home():
    return render_template("bookstore_chatbot.html", suggested_prompts=BOOKSTORE_PROMPTS)


@app.route("/chat", methods=["POST"])
def bookstore_chat():
    """Handle user input, process the query, and return a chatbot response."""
    user_input = request.form.get("user_input", "").strip()
    logging.debug(f"User input received: {user_input}")

    if not user_input:
        return jsonify({
            "response": "How may I help you? Here are some things you can ask me:",
            "suggested_prompts": BOOKSTORE_PROMPTS,
        })

    # Check for invalid inputs
    if user_input.isdigit() or len(user_input) < 8:
        return jsonify({
            "response": "I'm sorry, I couldn't understand your input. "
                        "Please try asking about a book, such as its price or availability.",
        })

    # Extract book title from user input
    book = extract_book_title(user_input)
    logging.debug(f"Extracted book: {book}")

    if not book:
        return jsonify({
            "response": "Sorry, I couldn't find any books matching your query. "
                        "Can you rephrase or provide more details?"
        })

    query_types = detect_bookstore_query_types(user_input)
    if not query_types:
        query_types = ["availability"]

    response = generate_bookstore_response(query_types, book)
    logging.debug(f"Generated response: {response}")
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
