import shelve


class Article:
    def __init__(self, title, author, image, description):
        self.title = title
        self.author = author
        self.image = image
        self.description = description

    def __repr__(self):
        return f"Article(title={self.title}, author={self.author}, image={self.image}, description={self.description})"


def add_article(db, title, author, image, description):
    article_id = str(len(db) + 1)  # Generating a simple ID
    article = Article(title, author, image, description)
    db[article_id] = article
    print(f"Article '{title}' added successfully!")


def get_article(db, article_id):
    return db.get(article_id, None)


def list_articles(db):
    if db:
        print("\nArticles in the database:")
        for key, article in db.items():
            print(f"ID: {key} - {article}")
    else:
        print("No articles in the database.")


def delete_article(db, article_id):
    if article_id in db:
        del db[article_id]
        print(f"Article with ID {article_id} has been deleted.")
    else:
        print(f"Article with ID {article_id} not found in the database.")


def update_article(db, article_id):
    if article_id in db:
        print(f"Updating article with ID {article_id}.")
        article = db[article_id]

        new_title = input(f"Enter new title (leave blank to keep '{article.title}'): ") or article.title
        new_author = input(f"Enter new author (leave blank to keep '{article.author}'): ") or article.author
        new_image = input(f"Enter new image URL (leave blank to keep '{article.image}'): ") or article.image
        new_description = input(f"Enter new description (leave blank to keep existing one): ") or article.description

        article.title = new_title
        article.author = new_author
        article.image = new_image
        article.description = new_description

        db[article_id] = article
        print(f"Article with ID {article_id} has been updated.")
    else:
        print(f"Article with ID {article_id} not found in the database.")


def input_article_details(db):
    while True:
        title = input("Enter article title: ")
        author = input("Enter author name: ")
        image = input("Enter image URL (or path): ")
        description = input("Enter article description/content: ")
        add_article(db, title, author, image, description)
        continue_adding = input("Do you want to add another article? (y/n): ").strip().lower()
        if continue_adding != 'y':
            break


def main_screen(db):
    while True:
        print("\n--- Article Management ---")
        print("1. Add an Article")
        print("2. List All Articles")
        print("3. Delete an Article")
        print("4. Update an Article")
        print("5. Exit")
        choice = input("Choose an option (1-5): ")

        if choice == '1':
            input_article_details(db)
        elif choice == '2':
            list_articles(db)
        elif choice == '3':
            article_id = input("Enter Article ID to delete: ")
            delete_article(db, article_id)
        elif choice == '4':
            article_id = input("Enter Article ID to update: ")
            update_article(db, article_id)
        elif choice == '5':
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please select a valid option.")


def main():
    with shelve.open('articles.db') as db:
        main_screen(db)


if __name__ == "__main__":
    main()
