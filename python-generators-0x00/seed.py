#!/usr/bin/python3

import mysql.connector
import csv
import uuid # Though we read UUIDs from CSV, useful for general handling

# Database connection parameters
# !!! IMPORTANT: Replace with your actual MySQL credentials !!!
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Divinity:100"
DB_NAME = "ALX_prodev"

def connect_db():
    """Connects to the MySQL database server (no specific DB selected initially)."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Connected to MySQL server.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL server: {err}")
        return None

def create_database(connection):
    """Creates the database ALX_prodev if it does not exist."""
    if connection is None:
        print("Database connection is not valid.")
        return

    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        # Check if database was actually created (optional but good practice)
        cursor.execute(f"USE {DB_NAME}") # Try to use it
        print(f"Database {DB_NAME} checked/created successfully.")
    except mysql.connector.Error as err:
        print(f"Error creating database {DB_NAME}: {err}")
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

def connect_to_prodev():
    """Connects to the ALX_prodev database in MySQL."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME # Specify the database
        )
        print(f"Connected to database {DB_NAME}.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to database {DB_NAME}: {err}")
        return None

def create_table(connection):
    """Creates a table user_data if it does not exist with the required fields."""
    if connection is None:
        print("Database connection is not valid.")
        return

    table_sql = """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id VARCHAR(36) PRIMARY KEY, -- UUIDs are typically stored as VARCHAR(36)
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        age DECIMAL(5,0) NOT NULL -- DECIMAL(5,0) means up to 99999, no decimal places
    )
    """
    # PRIMARY KEY automatically creates an index, so no explicit index needed for user_id

    try:
        cursor = connection.cursor()
        cursor.execute(table_sql)
        connection.commit() # COMMIT is important for DDL in some scenarios
        print("Table user_data checked/created successfully.")
    except mysql.connector.Error as err:
        print(f"Error creating table user_data: {err}")
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()

def insert_data(connection, csv_filepath):
    """Inserts data from a CSV file into the user_data table."""
    if connection is None:
        print("Database connection is not valid.")
        return

    insert_sql = "INSERT IGNORE INTO user_data (user_id, name, email, age) VALUES (%s, %s, %s, %s)"
    # Use INSERT IGNORE to skip rows that have a user_id that already exists (based on PRIMARY KEY)

    data_to_insert = []
    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader) # Skip the header row

            for row in reader:
                # Basic validation/conversion
                try:
                    # Ensure UUID string is valid format if needed, here assuming CSV is correct
                    # Convert age to appropriate type (DECIMAL)
                    processed_row = (row[0], row[1], row[2], int(row[3])) # MySQL Connector handles Python int to DECIMAL
                    data_to_insert.append(processed_row)
                except ValueError as e:
                    print(f"Skipping row due to data error: {row} - {e}")
                    continue

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if not data_to_insert:
        print("No data to insert from CSV.")
        return

    try:
        cursor = connection.cursor()
        # Use executemany for efficient bulk insertion
        cursor.executemany(insert_sql, data_to_insert)
        connection.commit()
        print(f"Inserted/Ignored {len(data_to_insert)} rows from {csv_filepath}.")
    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")
        connection.rollback() # Rollback changes if insertion fails
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()


# --- Generator Function ---

def stream_users_from_db():
    """
    Generator function to stream rows from the user_data table one by one.
    Connects to the ALX_prodev database and yields rows as dictionaries.
    """
    connection = None # Initialize connection outside try block
    try:
        # Connect to the database
        connection = connect_to_prodev()
        if connection is None:
            print("Failed to connect to database for streaming.")
            return # Exit the generator if connection fails

        # Use a cursor with buffered=False (default for large queries)
        # Dictionary=True to get results as dictionaries
        # Use context managers for cursor and connection for reliable cleanup
        with connection.cursor(dictionary=True, buffered=False) as cursor:
            # Execute the query
            query = "SELECT user_id, name, email, age FROM user_data"
            cursor.execute(query)

            # Iterate over the cursor, yielding rows one by one
            # The MySQL Connector cursor object acts as an iterator
            print("Starting data stream from user_data table...")
            for row in cursor:
                yield row # Yield the current row (as a dictionary)

            print("Finished streaming data.")

    except mysql.connector.Error as err:
        print(f"Database error during streaming: {err}")
        # The generator will stop if an error occurs here
    except Exception as e:
        print(f"An unexpected error occurred during streaming: {e}")
        # Catch other potential errors
    finally:
        # Ensure the connection is closed
        if connection is not None and connection.is_connected():
            connection.close()
            print("Database connection closed.")


if __name__ == "__main__":
    # Example usage of the generator
    print("--- Testing the Generator ---")

    # Get the generator object
    user_stream = stream_users_from_db()

    # Iterate through the generator to retrieve rows one by one
    try:
        print("Fetching first 3 rows using the generator:")
        for i, user_row in enumerate(user_stream):
            print(user_row)
            if i >= 2: # Just fetch a few for the example
                break
        # If the loop finishes early, the generator is not exhausted, but the connection might still be open
        # until the generator object is garbage collected or explicitly closed/exhausted.
        # Using 'with' around the generator call is not standard, manual close in finally is typical.
        # However, the 'with' statements *inside* the generator for cursor/connection are robust.

        print("\nFetching next 2 rows:")
        # The generator remembers its state, so we continue from where we left off
        for i, user_row in enumerate(user_stream):
             print(user_row)
             if i >= 1: # Fetch 2 more (index 0 and 1)
                 break

    except Exception as e:
        print(f"An error occurred while consuming the generator: {e}")

    print("\n--- Generator Test Complete ---")

    # Note: Running the seeding part __again__ here would re-create the database/table
    # and try to insert data, which INSERT IGNORE would handle.
    # The original 0-main.py logic is better separated.
