#!/usr/bin/python3

import seed  # Importing all functions from seed.py

csv_filepath = "C:/Users/HP/Documents/Github/alx-backend-python/python-generators-0x00/data.csv"  # Replace with the actual CSV file path

if __name__ == "__main__":
    # Step 1: Connect to MySQL server
    db_connection = seed.connect_db()

    # Step 2: Create the database if it doesn't exist
    seed.create_database(db_connection)

    # Step 3: Connect to the specific database
    prodev_connection = seed.connect_to_prodev()

    # Step 4: Create the table if it doesn't exist
    seed.create_table(prodev_connection)

    # Step 5: Insert data into the table from CSV
    seed.insert_data(prodev_connection, csv_filepath)

    # Step 6: Stream and display data from the database using the generator
    print("\n--- Streaming users from the database ---")
    user_stream = seed.stream_users_from_db()
    for user in user_stream:
        print(user)

    # Step 7: Close database connection
    if prodev_connection and prodev_connection.is_connected():
        prodev_connection.close()
        print("Database connection closed.")