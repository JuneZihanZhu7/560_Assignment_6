"""
INLS 560 - Assignment 6: Managing Collections
Zihan Zhu
"""

# The number of items shown at a time when a whole collection is displayed.
PAGE_SIZE = 10

# The fields that a query searches for each type of item.
BOOK_QUERY_FIELDS = ["Title", "Author", "Publisher"]
MOVIE_QUERY_FIELDS = ["Title", "Director", "Genre"]

# The text fields the user enters for each type of new item, in the same order as the columns of the data files.
BOOK_TEXT_FIELDS = ["Title", "Author", "Publisher", "Pages", "Year"]
MOVIE_TEXT_FIELDS = ["Title", "Director", "Length", "Genre", "Year"]


# Loads data for both books and movies, returning a dictionary with two keys, 'books' and 'movies', one for
# each subset of the collection.
def load_collections():
    # Load the two collections.
    book_collection, max_book_id = load_collection("books.csv")
    movie_collection, max_movie_id = load_collection("movies.csv")

    # Check for error.
    if book_collection is None or movie_collection is None:
        return None, None

    # Return the composite dictionary.
    return {"books": book_collection, "movies": movie_collection}, max(max_book_id, max_movie_id)


# Loads a single collection and returns the data as a dictionary.  Upon error, None is returned.
def load_collection(file_name):
    max_id = -1
    try:
        # Create an empty collection.
        collection = {}

        # Open the file and read the field names
        collection_file = open(file_name, "r")
        field_names = collection_file.readline().rstrip().split(",")

        # Read the remaining lines, splitting on commas, and creating dictionaries (one for each item)
        for item in collection_file:
            field_values = item.rstrip().split(",")
            collection_item = {}
            for index in range(len(field_values)):
                if (field_names[index] == "Available") or (field_names[index] == "Copies") or (field_names[index] == "ID"):
                    collection_item[field_names[index]] = int(field_values[index])
                else:
                    collection_item[field_names[index]] = field_values[index]
            # Add the full item to the collection.
            collection[collection_item["ID"]] = collection_item
            # Update the max ID value
            max_id = max(max_id, collection_item["ID"])

        # Close the file now that we are done reading all of the lines.
        collection_file.close()

    # Catch IO Errors, with the File Not Found error the primary possible problem to detect.
    except FileNotFoundError:
        print("File not found when attempting to read", file_name)
        return None
    except IOError:
        print("Error in data file when reading", file_name)
        return None

    # Return the collection.
    return collection, max_id


# Prints each field of an item on its own line, with the ID first when the item has one, followed by a blank line.
def display_item(item):
    # A new item that has not been added to a collection yet does not have an ID to show.
    if "ID" in item:
        print(f"ID: {item['ID']}")

    # The ID was already printed above, so it is skipped here.
    for field_name in item:
        if field_name != "ID":
            print(f"{field_name}: {item[field_name]}")

    print()


# Displays a whole collection ten items at a time until every item is shown or the user types 'm' to return to the menu.
def display_collection(collection):
    items = list(collection.values())
    index = 0
    response = ""

    # Keep showing items until the collection runs out or the user asks for the menu.
    while index < len(items) and response != "m":
        display_item(items[index])
        index += 1

        # Pause after each full group of ten, but only when there are more items left to show.
        if index % PAGE_SIZE == 0 and index < len(items):
            response = input("Press enter to show more items, or type 'm' to return to the menu: ")


# Returns True if the lower case query appears anywhere in one of the given fields of the item, and False otherwise.
def item_matches(item, query, query_fields):
    match_found = False

    # Both strings are compared in lower case so that the search ignores upper and lower case.
    for field_name in query_fields:
        if query in item[field_name].lower():
            match_found = True

    return match_found


# Asks for a query string and displays every item in the collection that contains it in one of the given fields.
def query_collection(collection, query_fields):
    query = input("Enter a query string to use for the search: ").lower()
    match_count = 0

    # Check every item so that all of the matches are displayed, not just the first one.
    for item in collection.values():
        if item_matches(item, query, query_fields):
            display_item(item)
            match_count += 1

    # Tell the user when nothing matched instead of leaving the screen empty.
    if match_count == 0:
        print("No items matched your query.")


# Asks for an ID with the given prompt and returns the matching item, or None after explaining why the ID is not valid.
def get_item_by_id(library_collections, prompt):
    item = None

    # The int function raises a ValueError when the user types something other than a whole number.
    try:
        item_id = int(input(prompt))

        # IDs are unique across both collections, so the item could be in either one.
        if item_id in library_collections["books"]:
            item = library_collections["books"][item_id]
        elif item_id in library_collections["movies"]:
            item = library_collections["movies"][item_id]
        else:
            print(f"There is no item with the ID {item_id} in the collection.")
    except ValueError:
        print("That is not a valid ID.  An ID must be a whole number.")

    return item


# Checks out one copy of the item chosen by the user as long as a copy is available.
def check_out(library_collections):
    item = get_item_by_id(library_collections, "Enter the ID for the item you wish to check out: ")

    # An invalid ID has already been reported, so there is nothing left to do when no item was found.
    if item is not None:
        if item["Available"] > 0:
            item["Available"] -= 1
            print("Your check out has succeeded.")
            display_item(item)
        else:
            print("No copies of the item are available for check out.")


# Checks in one copy of the item chosen by the user as long as a copy is currently checked out.
def check_in(library_collections):
    item = get_item_by_id(library_collections, "Enter the ID for the item you wish to check in: ")

    # A copy is checked out only when fewer copies are available than the collection owns.
    if item is not None:
        if item["Available"] < item["Copies"]:
            item["Available"] += 1
            print("Your check in has succeeded.")
            display_item(item)
        else:
            print("All copies are already available, so this item can not be checked in.")


# Asks for the number of copies of a new item until the user enters a whole number above zero, then returns it.
def get_copy_count():
    copies = None

    # Repeat until a valid number of copies has been provided.
    while copies is None:
        try:
            copies = int(input("Copies: "))
            if copies < 1:
                print("The number of copies must be a whole number above zero.")
                copies = None
        except ValueError:
            print("The number of copies must be a whole number above zero.")

    return copies


# Asks for the fields of a new item, adds it unless the user cancels, and returns the largest ID in use.
def add_item(collection, max_existing_id, item_type, text_fields):
    print(f"Please enter the following attributes for the new {item_type}.")
    new_item = {}

    # These fields are stored as text, which matches how the starter code loads them from the data files.
    for field_name in text_fields:
        new_item[field_name] = input(f"{field_name}: ")

    # Every copy of a new item starts out available.
    new_item["Copies"] = get_copy_count()
    new_item["Available"] = new_item["Copies"]

    print("You have entered the following data:")
    display_item(new_item)
    response = input("Press enter to add this item to the collection.  Enter 'x' to cancel.")

    # The next ID after the largest one in use is guaranteed to be unique.
    if response != "x":
        max_existing_id += 1
        new_item["ID"] = max_existing_id
        collection[max_existing_id] = new_item

    return max_existing_id


# Adds a new book entered by the user to the book collection and returns the largest ID in use.
def add_book(book_collection, max_existing_id):
    return add_item(book_collection, max_existing_id, "book", BOOK_TEXT_FIELDS)


# Adds a new movie entered by the user to the movie collection and returns the largest ID in use.
def add_movie(movie_collection, max_existing_id):
    return add_item(movie_collection, max_existing_id, "movie", MOVIE_TEXT_FIELDS)


# Display the menu of commands and get user's selection.  Returns a string with  the user's reauexted command.
# No validation is performed.
def prompt_user_with_menu():
    print("\n\n********** Welcome to the Collection Manager. **********")
    print("COMMAND    FUNCTION")
    print("  ci         Check in an item")
    print("  co         Check out an item")
    print("  ab         Add a new book")
    print("  am         Add a new movie")
    print("  db         Display books")
    print("  dm         Display movies")
    print("  qb         Query for books")
    print("  qm         Query for movies")
    print("  x          Exit")
    return input("Please enter a command to proceed: ")


# This is the main program function.  It runs the main loop which prompts the user and performs the requested actions.
def main():
    # Load the collections, and check for an error.
    library_collections, max_existing_id = load_collections()

    if library_collections is None:
        print("The collections could not be loaded. Exiting.")
        return

    # No error, so print out a success message with the number of items.
    total_item_count = len(library_collections['books']) + len(library_collections['movies'])
    print(f"The collections have loaded successfully with {total_item_count} items. ")

    # Display the error and get the operation code entered by the user.  We perform this continuously until the
    # user enters "x" to exit the program.  Calls the appropriate function that corresponds to the requested operation.
    operation = prompt_user_with_menu()
    while operation != "x":
        if operation == "ci":
            check_in(library_collections)
        elif operation == "co":
            check_out(library_collections)
        elif operation == "ab":
            max_existing_id = add_book(library_collections["books"], max_existing_id)
        elif operation == "am":
            max_existing_id = add_movie(library_collections["movies"], max_existing_id)
        elif operation == "db":
            display_collection(library_collections["books"])
        elif operation == "dm":
            display_collection(library_collections["movies"])
        elif operation == "qb":
            query_collection(library_collections["books"], BOOK_QUERY_FIELDS)
        elif operation == "qm":
            query_collection(library_collections["movies"], MOVIE_QUERY_FIELDS)
        else:
            print("Unknown command.  Please try again.")

        operation = prompt_user_with_menu()


# Kick off the execution of the program.
main()
