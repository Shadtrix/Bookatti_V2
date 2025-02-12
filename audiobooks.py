import json
import os

AUDIOBOOKS_FILE = "audiobooks.json"
UPLOAD_FOLDER = "static/uploads/audio"


class Audiobook:
    def __init__(self, title, author, audio_file):
        self.title = title
        self.author = author
        self.audio_file = audio_file


def load_audiobooks():
    """Load audiobooks from JSON file."""
    if not os.path.exists(AUDIOBOOKS_FILE):
        return {}
    with open(AUDIOBOOKS_FILE, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}

def save_audiobooks(audiobooks):
    """Save audiobooks to JSON file."""
    with open(AUDIOBOOKS_FILE, "w", encoding="utf-8") as file:
        json.dump(audiobooks, file, indent=4)

def add_audiobook(title, author, audio_file):
    """Add a new audiobook."""
    audiobooks = load_audiobooks()
    audiobook_id = str(len(audiobooks) + 1)
    while audiobook_id in audiobooks:
        audiobook_id = str(int(audiobook_id) + 1)
    audiobooks[audiobook_id] = {
        "title": title,
        "author": author,
        "audio_file": audio_file
    }
    save_audiobooks(audiobooks)
    return audiobook_id

def delete_audiobook(audiobook_id):
    """Delete an audiobook."""
    audiobooks = load_audiobooks()
    if audiobook_id in audiobooks:
        del audiobooks[audiobook_id]
        save_audiobooks(audiobooks)
        return True
    return False