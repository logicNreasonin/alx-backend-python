#!/usr/bin/python3

import stream_users  # Importing the generator function from 0-stream_users.py

if __name__ == "__main__":
    print("--- Streaming users from the database ---")
    
    # Get the generator object
    user_stream = stream_users.stream_users()

    # Iterate through the generator to fetch and display user records one by one
    try:
        for user in user_stream:
            print(user)  # Displaying each row from user_data table

    except Exception as e:
        print(f"An error occurred while consuming the generator: {e}")

    print("\n--- Stream Users Test Complete ---")