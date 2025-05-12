#!/usr/bin/python3

import mysql.connector

# Database connection parameters - make sure these match your MySQL setup
# !!! IMPORTANT: Replace with your actual MySQL credentials and host !!!
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Divinity:100"
DB_NAME = "ALX_prodev"

def stream_users():
    """
    Generator function to stream rows from the user_data table one by one.
    Connects to the ALX_prodev database and yields rows as dictionaries.
    Uses a single loop as required.
    """
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
        # print("Connected to database for streaming.") # Optional debug print

        # Create a cursor. buffered=False is crucial for streaming large datasets.
        # dictionary=True makes rows dictionaries.
        cursor = connection.cursor(dictionary=True, buffered=False)

        # Execute the query to select all users
        query = "SELECT user_id, name, email, age FROM user_data"
        cursor.execute(query)

        # Iterate directly over the cursor to yield rows one by one
        # This is the single required loop
        for row in cursor:
            yield row

    except mysql.connector.Error as err:
        print(f"Database error during streaming: {err}")
        # The generator will implicitly stop if an error occurs here
    except Exception as e:
        print(f"An unexpected error occurred during streaming: {e}")
        # Catch other potential errors
    finally:
        # Ensure cursor and connection are closed in the finally block
        if cursor is not None:
            cursor.close()
            # print("Database cursor closed.") # Optional debug print
        if connection is not None and connection.is_connected():
            connection.close()
            # print("Database connection closed.") # Optional debug print
