import spacy
from flask import Flask, render_template, request, jsonify
from rapidfuzz import fuzz
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Suggested prompts for the chatbot
SUGGESTED_PROMPTS = [
    '- "Do you have [book name]?"',
    '- "Who is the author of [book name]?"',
    '- "What is the price of [book name]?"',
    '- "Show all information about [book name]."'
]

# Load Spacy NLP model
nlp = spacy.load("en_core_web_sm")

# Book inventory
book_inventory = {
    "Harry Potter": {"author": "J.K. Rowling", "price": "$20.00", "availability": "available", "location": "Shelf A1"},
    "The Hobbit": {"author": "J.R.R. Tolkien", "price": "$15.00", "availability": "available", "location": "Shelf B2"},
    "1984": {"author": "George Orwell", "price": "$18.00", "availability": "out of stock", "location": None},
    "To Kill a Mockingbird": {"author": "Harper Lee", "price": "$10.00", "availability": "available", "location": "Shelf C3"},
    "Pride and Prejudice": {"author": "Jane Austen", "price": "$12.50", "availability": "available", "location": "Shelf D4"},
}

# Query map for detecting user queries
query_map = {
    "price": ["price", "cost", "how much"],
    "author": ["author", "writer", "who wrote"],
    "availability": ["available", "in stock", "do you have"],
    "location": ["location", "where", "find"],
    "all_information": ["all information", "details", "show all"]
}

# Detect book titles using Spacy NER and fuzzy matching


def extract_book_titles(user_input):
    doc = nlp(user_input)
    titles = []

    # NER for detecting book-like entities
    for ent in doc.ents:
        if ent.label_ in ["WORK_OF_ART", "PRODUCT"]:
            titles.append(ent.text)

    # Add fuzzy matches for backup
    for title in book_inventory.keys():
        if fuzz.partial_ratio(title.lower(), user_input.lower()) > 80:
            titles.append(title)

    # Remove duplicates
    return list(set(titles))

# Detect query types with improved matching


def detect_query_types(user_input):
    detected_queries = []
    user_input = user_input.lower()

    for query_type, keywords in query_map.items():
        if any(keyword in user_input for keyword in keywords):
            detected_queries.append(query_type)

    return detected_queries

# Generate appropriate responses


def generate_response(query_types, book_details):
    responses = []
    response_templates = {
        "price": f"The price of '{book_details['title']}' is {book_details['price']}.",
        "author": f"The author of '{book_details['title']}' is {book_details['author']}.",
        "availability": f"'{book_details['title']}' is {book_details['availability']}.",
        "location": f"You can find '{book_details['title']}' at {book_details['location'] or 'an unknown location'}.",
        "all_information": f"'{book_details['title']}' by {book_details['author']} costs {book_details['price']}. "
                           f"It is currently {book_details['availability']} and located at {book_details['location'] or 'N/A'}."
    }
    for query in query_types:
        if query in response_templates:
            responses.append(response_templates[query])
    return " ".join(responses)

# Process user input and respond accurately


def precise_response(user_input):
    book_titles = extract_book_titles(user_input)
    if not book_titles:
        return "Sorry, I couldn't find any books or understand your question."

    # Split user input into separate query phrases
    query_phrases = re.split(r'[.,;]|and', user_input.lower())  # Split by commas, semicolons, or 'and'

    responses = []
    last_title = None  # To handle pronoun references like 'it'

    # Process each query phrase independently
    for phrase in query_phrases:
        phrase = phrase.strip()
        if not phrase:
            continue

        matched_title = None
        for title in book_titles:
            if title.lower() in phrase:
                matched_title = title
                last_title = title  # Update last title reference
                break

        # Use the last matched title if 'it' or similar is used
        if not matched_title and "it" in phrase and last_title:
            matched_title = last_title

        if matched_title:
            query_types = detect_query_types(phrase)
            details = {**book_inventory[matched_title], "title": matched_title}
            if query_types:
                responses.append(generate_response(query_types, details))
            else:
                responses.append(f"I couldn't determine what you want to know about '{matched_title}'.")
        else:
            responses.append("Sorry, I couldn't determine what book you're referring to.")

    return " ".join(responses)


# Placeholder function for fetching book details from an external API
def fetch_book_details_from_api(book_title):
    # Simulate an API call (can be replaced with real implementation)
    return {"title": book_title, "author": "Unknown", "price": "Unknown", "availability": "Unknown", "location": "Unknown"}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    api_result = None
    if request.method == "POST":
        book_title = request.form.get("search_title", "").strip()
        api_result = fetch_book_details_from_api(book_title)
    return render_template("inventory.html", inventory=book_inventory, api_result=api_result)


@app.route("/shop")
def shop():
    return render_template("shop.html")


@app.route("/library")
def library_home():
    return render_template("library_home.html")


@app.route("/book-loan")
def book_loan():
    return render_template("book_loan.html")


@app.route("/audiobooks")
def audiobooks():
    return render_template("audiobooks.html")


@app.route("/enquiries")
def enquiries():
    return render_template("enquiries.html")


@app.route("/events")
def events():
    return render_template("events.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        # Send a clear JSON response with suggested prompts
        return jsonify({
            "response": "How may I help you? Here are some things you can ask me:",
            "suggested_prompts": SUGGESTED_PROMPTS
        })
    response = precise_response(user_input)
    return jsonify({"response": response})


@app.route("/chatbot")
def chatbot():
    # Pass the prompts as a list to the template
    return render_template("chatbot.html", suggested_prompts=SUGGESTED_PROMPTS)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/sign-up")
def sign_up():
    return render_template("sign_up.html")


@app.route("/chatbot1")
def chatbot1():
    # Pass the prompts as a list to the template
    return render_template("chatbot1.html", suggested_prompts=SUGGESTED_PROMPTS)


@app.route("/chatbot2")
def chatbot2():
    # Pass the prompts as a list to the template
    return render_template("chatbot2.html", suggested_prompts=SUGGESTED_PROMPTS)


if __name__ == "__main__":
    app.run(debug=True)
