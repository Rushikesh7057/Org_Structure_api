# Base image: lightweight Python
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1  # Prevents .pyc files
ENV PYTHONUNBUFFERED 1         # Ensures logs show immediately

# Set working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the project
COPY . /app/

# Expose Django default port
EXPOSE 8000

# Command to run Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
