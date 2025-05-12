#!/usr/bin/python3

import lazy_paginate  # Importing functions from 2-lazy_paginate.py

PAGE_SIZE = 5  # Define the number of users per page

if __name__ == "__main__":
    print(f"--- Fetching users lazily with page size {PAGE_SIZE} ---")

    # Get the lazy pagination generator
    user_pages = lazy_paginate.lazy_pagination(PAGE_SIZE)

    # Iterate through the generator to fetch and display pages of users
    try:
        for page_num, user_page in enumerate(user_pages):
            print(f"\n--- Page {page_num + 1} ---")
            for user in user_page:
                print(user)

    except Exception as e:
        print(f"An error occurred while consuming the lazy pagination generator: {e}")

    print("\n--- Lazy Pagination Test Complete ---")