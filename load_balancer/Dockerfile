FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the application code to the container
COPY load_balancer /app

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start the Flask server when the container starts
CMD ["python", "server.py"]
