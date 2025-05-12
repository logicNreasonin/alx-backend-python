#!/usr/bin/python3

import mysql.connector
# Assuming seed.py contains connect_to_prodev() and database credentials
# We try to import it, providing a fallback if it's missing or incomplete.
try:
    seed = __import__('seed')
    connect_to_prodev = seed.connect_to_prodev
except ImportError:
    print("Error: seed.py not found. Please ensure seed.py exists and contains connect_to_prodev function.")
    # Define a dummy function or exit if seed is essential
    def connect_to_prodev():
        print("Dummy connection function called (seed.py not found). Cannot connect.")
        return None
    # exit(1) # Uncomment this line if the script must exit if seed.py is missing
except AttributeError:
    print("Error: connect_to_prodev function not found in seed.py.")
    # Define a dummy function or exit if connect_to_prodev is missing
    def connect_to_prodev():
        print("Dummy connection function called (connect_to_prodev not found). Cannot connect.")
        return None
    # exit(1) # Uncomment this line if the script must exit


def stream_user_ages():
    """
    Generator function to stream user ages one by one from the database.
    Connects to the ALX_prodev database and yields individual age values.
    Uses 1 loop.
    """
    connection = None
    cursor = None

    try:
        # Connect to the database using the function from seed.py
        connection = connect_to_prodev()
        if connection is None:
            # The dummy function will print an error, just return to exit the generator
            return

        # Create a cursor. buffered=False is crucial for streaming large datasets.
        # dictionary=True makes rows dictionaries, easy to access by column name.
        cursor = connection.cursor(dictionary=True, buffered=False)

        # Execute the query to select ONLY the age column
        query = "SELECT age FROM user_data"
        cursor.execute(query)

        # Loop 1 (within this function): Iterate over the cursor to yield ages
        # The cursor iterates row by row from the database result set
        for row in cursor:
            # Extract the age from the dictionary row
            age = row.get('age') # Use .get() for safety, though age is NOT NULL

            # Ensure age is not None and attempt conversion to float for summation
            if age is not None:
                 try:
                      # MySQL DECIMAL often comes as Decimal type, float() handles it
                      yield float(age)
                 except (ValueError, TypeError):
                      # Handle cases where age might not be a valid number (shouldn't happen with DECIMAL NOT NULL but good practice)
                      print(f"Warning: Could not convert age '{age}' to number. Skipping row.")


    except mysql.connector.Error as err:
        print(f"Database error during age streaming: {err}")
        # The generator will implicitly stop if an error occurs here
    except Exception as e:
        print(f"An unexpected error occurred during age streaming: {e}")
        # Catch other potential errors
    finally:
        # Ensure cursor and connection are closed in the finally block
        if cursor is not None:
            cursor.close()
            # print("Database cursor closed.") # Optional debug print
        if connection is not None and connection.is_connected():
            connection.close()
            # print("Database connection closed.") # Optional debug print


def calculate_average_age():
    """
    Calculates the average age of users by consuming the stream_user_ages
    generator without loading all ages into memory.
    Uses 1 loop. Total loops in script: 1 (in stream_user_ages) + 1 (here) = 2.
    """
    total_age_sum = 0.0 # Use float for sum to ensure float division later
    user_count = 0

    # Loop 2 (within this function): Consume the generator stream_user_ages
    # This loop iterates over the individual age values yielded by the generator
    for age in stream_user_ages():
        total_age_sum += age
        user_count += 1

    # Avoid division by zero in case no users were found or streamed
    if user_count == 0:
        return 0.0 # Return 0.0 or handle as appropriate if no data

    # Calculate the average
    return total_age_sum / user_count


# Main execution block to call the calculation and print the result
if __name__ == "__main__":
    average_age = calculate_average_age()

    # Print the result formatted as required
    # Using :.2f to format the float to 2 decimal places
    print(f"Average age of users: {average_age:.2f}")
