# Set the base image to use for the container
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the application code to the container
COPY load_balancer /app

# Install any required dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for Flask
ENV FLASK_APP=app.py

# Expose the port the application will listen on
EXPOSE 8000

# Start the Flask server when the container starts
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
