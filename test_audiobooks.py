import audiobooks

print("Testing Audiobooks Backend...\n")

# Test 1: Load audiobooks (should be empty at first)
print("Loaded audiobooks:", audiobooks.load_audiobooks())

# Test 2: Add an audiobook
audiobook_id = audiobooks.add_audiobook("Test Title", "Test Author", "test.mp3")
print(f"Audiobook Added! ID: {audiobook_id}")

# Test 3: Load again to check if it was saved
print("Audiobooks after adding one:", audiobooks.load_audiobooks())

# Test 4: Delete the audiobook
deleted = audiobooks.delete_audiobook(audiobook_id)
print("Deleted:", deleted)

# Test 5: Load again to see if it's gone
print("Audiobooks after deletion:", audiobooks.load_audiobooks())

print("\nBackend Test Complete ✅")