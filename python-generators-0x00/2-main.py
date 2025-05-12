#!/usr/bin/python3

import batch_processing  # Importing the batch processing function from 1-batch_processing.py

BATCH_SIZE = 5  # Define the batch size for processing

if __name__ == "__main__":
    print(f"--- Streaming users in batches of {BATCH_SIZE} ---")

    # Get the generator object
    user_batch_stream = batch_processing.batch_processing(BATCH_SIZE)

    # Iterate through the generator to fetch and display user records one by one
    try:
        for user in user_batch_stream:
            print(user)  # Display each filtered user record

    except Exception as e:
        print(f"An error occurred while consuming the batch processor: {e}")

    print("\n--- Batch Processing Test Complete ---")