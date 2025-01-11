# Use the official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy all project files to the working directory
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for local testing (not needed in Lambda but useful locally)
EXPOSE 8080

# Start the Flask app
CMD ["python", "app.py"]
