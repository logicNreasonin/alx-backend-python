#!/usr/bin/python3

# We need the seed script to get the database connection function
seed = __import__('seed')

def paginate_users(page_size, offset):
    """
    Fetches a single page of user data from the database.
    This function is provided as a helper.
    """
    connection = None # Initialize connection
    cursor = None     # Initialize cursor
    rows = []         # Initialize result list

    try:
        # Connect to the database using the function from seed.py
        connection = seed.connect_to_prodev()
        if connection is None:
            print("Failed to connect to database for pagination.")
            return [] # Return empty list if connection fails

        # Create a cursor
        cursor = connection.cursor(dictionary=True)

        # Execute the query with LIMIT and OFFSET
        # Basic validation for page_size and offset for safety
        safe_page_size = max(1, int(page_size)) # Ensure page_size is at least 1
        safe_offset = max(0, int(offset))       # Ensure offset is not negative

        query = f"SELECT user_id, name, email, age FROM user_data LIMIT {safe_page_size} OFFSET {safe_offset}"
        cursor.execute(query)

        # Fetch all rows for the current page
        rows = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Database error during pagination: {err}")
        # Return empty list on error
        rows = []
    except Exception as e:
        print(f"An unexpected error occurred during pagination: {e}")
        rows = []
    finally:
        # Ensure cursor and connection are closed
        if cursor is not None:
            cursor.close()
            # print("Database cursor closed.") # Optional debug print
        if connection is not None and connection.is_connected():
            connection.close()
            # print("Database connection closed.") # Optional debug print

    return rows

def lazy_pagination(page_size):
    """
    Generator function to fetch and yield database pages lazily.
    Fetches the next page only when requested by the caller.
    Uses only one loop and the yield generator.
    """
    if not isinstance(page_size, int) or page_size <= 0:
        print("Page size must be a positive integer.")
        return # Exit the generator if page_size is invalid

    offset = 0 # Start at the beginning

    # This is the ONLY loop allowed in this generator function
    while True:
        # Fetch the current page using the helper function
        current_page = paginate_users(page_size, offset)

        # If the fetched page is empty, it means there are no more pages
        if not current_page:
            break # Exit the loop (and thus the generator)

        # Yield the fetched page (which is a list of user dictionaries)
        yield current_page

        # Increment the offset for the next potential page fetch
        offset += page_size

# Note: The 3-main.py script will import and use the lazy_pagination function.
# No __main__ block needed in this file for the specified task structure.
