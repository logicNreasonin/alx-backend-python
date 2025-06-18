# alx-backend-python/messaging_app/Dockerfile

# Use a base Python image python:3.10.
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies needed for mysqlclient and potentially other packages
# Also install build-essential for compiling, and pkg-config
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    # Add any other system dependencies your project might need here
    && apt-get clean && rm -rf /var/lib/apt/lists/* # Clean up to reduce image size

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install necessary Python dependencies from the requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code into the container.
COPY . .

# Expose the port your Django app runs on (default is 8000).
EXPOSE 8000

# The CMD will be overridden by docker-compose.yml if you use that to run,
# but it's good practice to have a default CMD in the Dockerfile.
CMD ["gunicorn", "messaging_app.wsgi:application", "--bind", "0.0.0.0:8000"]