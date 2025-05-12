#!/usr/bin/python3

import mysql.connector
# No need for itertools or sys in this specific file, they are used by 2-main.py

# Database connection parameters - make sure these match your MySQL setup
# !!! IMPORTANT: Replace with your actual MySQL credentials and host !!!
DB_HOST = "localhost"
DB_USER = "your_mysql_user"
DB_PASSWORD = "your_mysql_password"
DB_NAME = "ALX_prodev"

def stream_users_in_batches(batch_size):
    """
    Generator function to stream rows from the user_data table in batches.
    Connects to the ALX_prodev database and yields lists of rows (batches).
    Uses 1 loop.
    """
    if not isinstance(batch_size, int) or batch_size <= 0:
        print("Batch size must be a positive integer.")
        return # Exit the generator if batch_size is invalid

    connection = None # Initialize connection
    cursor = None     # Initialize cursor

    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        # print("Connected to database for batch streaming.") # Optional debug print

        # Create a cursor. buffered=False is good practice for potentially large results.
        # dictionary=True makes rows dictionaries.
        cursor = connection.cursor(dictionary=True, buffered=False)

        # Execute the query to select all users
        query = "SELECT user_id, name, email, age FROM user_data"
        cursor.execute(query)

        # Loop 1: Fetch and yield batches
        while True:
            batch = cursor.fetchmany(batch_size) # Fetch batch_size rows
            if not batch: # fetchmany returns an empty list when no more rows
                break
            yield batch # Yield the current batch (a list of dictionaries)

    except mysql.connector.Error as err:
        print(f"Database error during batch streaming: {err}")
        # The generator will implicitly stop if an error occurs here
    except Exception as e:
        print(f"An unexpected error occurred during batch streaming: {e}")
        # Catch other potential errors
    finally:
        # Ensure cursor and connection are closed
        if cursor is not None:
            cursor.close()
            # print("Database cursor closed.") # Optional debug print
        if connection is not None and connection.is_connected():
            connection.close()
            # print("Database connection closed.") # Optional debug print


def batch_processing(batch_size):
    """
    Generator function that uses stream_users_in_batches to fetch data,
    processes each batch to filter users over the age of 25,
    and yields the filtered user dictionaries one by one.
    Uses 2 loops internally (nested).
    Total loops in this script (including stream_users_in_batches) is 1 + 2 = 3.
    """
    # Loop 2: Iterate over batches provided by the stream_users_in_batches generator
    for batch in stream_users_in_batches(batch_size):
        # Loop 3: Iterate over individual user dictionaries within the current batch
        for user in batch:
            # Process/Filter the user: check if age is greater than 25
            # Ensure 'age' exists and is comparable (mysql.connector usually handles DECIMAL)
            if user.get('age') is not None and user['age'] > 25:
                yield user # Yield the single, filtered user dictionary

# Note: The 2-main.py script will import and use the batch_processing function.
# No __main__ block needed in this file for the specified task structure.
