# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the application code to the container
COPY proxy /app
COPY proto/ops.proto ./proto/

# Install required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Generate the gRPC stub code from the proto file
RUN python -m grpc_tools.protoc --proto_path=./proto --python_out=. --grpc_python_out=. ops.proto

# Run the server
CMD ["python", "server.py"]
