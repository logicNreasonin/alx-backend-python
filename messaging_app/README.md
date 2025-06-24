# Messaging App

A simple messaging application built with Python, designed to facilitate real-time communication between users. This project demonstrates core backend concepts such as RESTful APIs, authentication, and message persistence.

## Features

- User registration and authentication
- Sending and receiving messages
- Real-time message updates (via WebSockets or polling)
- Message history and persistence
- RESTful API endpoints

## Technologies Used

- Python 3.x
- Flask or FastAPI (backend framework)
- SQLite or PostgreSQL (database)
- SQLAlchemy (ORM)
- WebSockets (for real-time features)
- JWT (for authentication)

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/messaging_app.git
    cd messaging_app
    ```

2. **Create a virtual environment and activate it:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the database:**
    ```bash
    flask db upgrade
    ```

5. **Run the application:**
    ```bash
    flask run
    ```

## API Endpoints

| Method | Endpoint              | Description                |
|--------|----------------------|----------------------------|
| POST   | `/register`          | Register a new user        |
| POST   | `/login`             | Authenticate user          |
| GET    | `/messages`          | Get message history        |
| POST   | `/messages`          | Send a new message         |
| GET    | `/ws`                | WebSocket for real-time    |

## Usage

- Register a new user and log in to receive a JWT token.
- Use the token to authenticate API requests.
- Send and receive messages in real time.

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License.
