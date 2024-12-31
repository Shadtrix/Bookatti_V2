import spacy  # SpaCy for natural language processing (NLP)
from flask import Flask, render_template, request, jsonify  # Flask for creating the web application
from rapidfuzz import fuzz  # RapidFuzz for fuzzy string matching to handle approximate text matches
import re  # Regular expressions for advanced pattern matching in user input

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Secret key for securely managing sessions in Flask

# Predefined prompts for users to guide interactions with the chatbot
BOOKSTORE_PROMPTS = [
    '"How much does [book name] cost?"',
    '"Is [book name] available?"',
    '"Who wrote [book name]?"',
    '"What is the ISBN of [book name]?"',
    '"Show all information about [book name]."',
]

# Load SpaCy's small English model for processing user input
nlp = spacy.load("en_core_web_sm")

# Static dictionary of books with details like author, price, stock levels, and ISBN
bookstore_inventory = {
    "Harry Potter": [{"author": "J.K. Rowling", "price": "$20.00", "stock": 10, "isbn": "9780439554930"}],
    "The Hobbit": [{"author": "J.R.R. Tolkien", "price": "$15.00", "stock": 5, "isbn": "9780547928227"}],
    "1984": [{"author": "George Orwell", "price": "$18.00", "stock": 0, "isbn": "9780451524935"}],
    "Pride and Prejudice": [{"author": "Jane Austen", "price": "$12.00", "stock": 7, "isbn": "9781503290563"}],
    "To Kill a Mockingbird": [{"author": "Harper Lee", "price": "$14.00", "stock": 4, "isbn": "9780061120084"}],
    "The Great Gatsby": [{"author": "F. Scott Fitzgerald", "price": "$13.00", "stock": 8, "isbn": "9780743273565"}],
    "Moby Dick": [{"author": "Herman Melville", "price": "$17.00", "stock": 3, "isbn": "9781503280786"}],
    "The Catcher in the Rye": [{"author": "J.D. Salinger", "price": "$16.00", "stock": 6, "isbn": "9780316769488"}],
    "Little Women": [{"author": "Louisa May Alcott", "price": "$11.00", "stock": 5, "isbn": "9781503280298"}],
    "The Lord of the Rings": [{"author": "J.R.R. Tolkien", "price": "$25.00", "stock": 2, "isbn": "9780544003415"}],
    "Joyland": [
        {"author": "Stephen King", "price": "$18.00", "stock": 12, "isbn": "9781781162644"},
        {"author": "Emily Schultz", "price": "$15.00", "stock": 8, "isbn": "9781550227215"}
    ],
}

# Mapping of user query types (e.g., price, availability) to related keywords
bookstore_query_map = {
    "price": ["price", "cost", "how much"],
    "availability": ["available", "in stock", "do you have"],
    "author": ["author", "writer", "who wrote"],
    "isbn": ["isbn", "identifier", "book number"],
}

# Function to extract book titles from user input
def extract_book_titles(user_input):
    """
    Extract book titles from user input and check for ambiguity (multiple authors).
    """
    doc = nlp(user_input)
    titles = []

    # Identify named entities in the input that might represent book titles
    for ent in doc.ents:
        if ent.label_ in ["WORK_OF_ART", "PRODUCT"]:
            titles.append(ent.text)

    # Fuzzy match against known book titles in the inventory
    for title in bookstore_inventory.keys():
        if fuzz.partial_ratio(title.lower(), user_input.lower()) > 70:
            titles.append(title)

    return list(set(titles))  # Return a unique list of titles

# Function to detect the type of query (e.g., price, availability) from user input
def detect_bookstore_query_types(user_input):
    """
    Detect the type(s) of query in user input, such as asking for price or availability.
    """
    detected_queries = []
    user_input = user_input.lower()

    if "show all information about" in user_input:
        return ["price", "author", "availability", "isbn"]

    for query_type, keywords in bookstore_query_map.items():
        if any(keyword in user_input for keyword in keywords):
            detected_queries.append(query_type)

    if re.search(r"do you have\s+.+", user_input):
        detected_queries.append("availability")

    return detected_queries

# Function to generate chatbot responses based on detected queries and book details
def generate_bookstore_response(query_types, book_details, show_all=False):
    """
    Generate a response for the user's query based on detected query types and book information.
    """
    title = book_details.get("title", "Unknown")
    author = book_details.get("author", "Unknown")
    stock = book_details.get("stock", 0)
    availability_status = "available" if stock > 0 else "out of stock"

    response_templates = {
        "price": f"The price of '{title}' by {author} is {book_details.get('price', 'unavailable')}.",
        "author": f"The author of '{title}' is {author}.",
        "availability": f"'{title}' by {author} is currently {availability_status}. Stock available: {stock}.",
        "isbn": f"The ISBN of '{title}' by {author} is {book_details.get('isbn', 'unavailable')}.",
    }

    responses = []
    availability_added = False

    for query in query_types:
        if query in response_templates:
            if query == "availability" and availability_added:
                continue
            if query == "availability":
                availability_added = True
            responses.append(response_templates[query])

    return " ".join(responses)

# Flask route for the chatbot's home page
@app.route("/")
def home():
    return render_template("bookstore_chatbot.html", suggested_prompts=BOOKSTORE_PROMPTS)

# Flask route for handling chatbot queries
@app.route("/chat", methods=["POST"])
def bookstore_chat():
    """
    Handle user input, process the query, and return a chatbot response.
    """
    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        return jsonify({
            "response": "How may I help you? Here are some things you can ask me:",
            "suggested_prompts": BOOKSTORE_PROMPTS,
        })

    # Check for invalid inputs (e.g., single digits or special characters)
    if user_input.isdigit() or len(user_input) < 2:
        return jsonify({
            "response": "I'm sorry, I couldn't understand your input. Please try asking about a book, such as its price or availability.",
        })

    book_titles = extract_book_titles(user_input)
    if not book_titles:
        return jsonify({
            "response": "Sorry, I couldn't find any books matching your query. Can you rephrase or provide more details?"
        })

    responses = []
    for title in book_titles:
        books = bookstore_inventory.get(title, [])
        if len(books) > 1:  # Handle ambiguous titles with multiple authors
            if "by" in user_input.lower():  # User specified an author
                specified_author = user_input.split("by")[-1].strip().lower()
                matching_books = [
                    book for book in books if fuzz.partial_ratio(book["author"].lower(), specified_author) > 70
                ]
                if matching_books:
                    book_details = matching_books[0]
                    book_details["title"] = title
                    query_types = detect_bookstore_query_types(user_input)
                    show_all = "show all information about" in user_input.lower()

                    if not query_types:
                        query_types = ["availability"]

                    response = generate_bookstore_response(query_types, book_details, show_all=show_all)
                    return jsonify({"response": response})

            # If no author is specified, ask the user to clarify
            authors = [book["author"] for book in books]
            return jsonify({
                "response": f"There are multiple books with the title '{title}'. Please specify the author: by {', '.join(authors)}.",
                "authors": authors,
                "title": title,
            })

        query_types = detect_bookstore_query_types(user_input)
        show_all = "show all information about" in user_input.lower()

        if not query_types:
            query_types = ["availability"]

        book_details = books[0]
        book_details["title"] = title

        response = generate_bookstore_response(query_types, book_details, show_all=show_all)
        responses.append(response)

    return jsonify({"response": " ".join(set(responses))})

# Flask route for handling author selection
@app.route("/choose_author", methods=["POST"])
def choose_author():
    """
    Handle the user's selection of an author for ambiguous titles.
    """
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()

    books = bookstore_inventory.get(title, [])
    for book in books:
        if book["author"].lower() == author.lower():
            query_types = detect_bookstore_query_types(request.form.get("user_input", "").strip())
            show_all = "show all information about" in request.form.get("user_input", "").lower()

            if not query_types:
                query_types = ["availability"]

            book["title"] = title
            response = generate_bookstore_response(query_types, book, show_all=show_all)
            return jsonify({"response": response})

    return jsonify({"response": f"Sorry, I couldn't find the author '{author}' for the title '{title}'. Please try again."})

if __name__ == "__main__":
    app.run(debug=True)