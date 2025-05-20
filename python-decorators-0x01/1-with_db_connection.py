import sqlite3
import functools

def with_db_connection(func):
    """Decorator to handle opening and closing a database connection."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('my_database.db')
        try:
            result = func(conn, *args, **kwargs)
        finally:
            conn.close()
        return result
    return wrapper

@with_db_connection
def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

# Fetch user by ID with automatic connection handling
user = get_user_by_id(user_id=1)
print(user)