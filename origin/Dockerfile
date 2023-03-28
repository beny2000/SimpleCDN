# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container and install dependencies
COPY origin/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code, proto file and content files into the container
COPY origin/server.py ./
COPY proto/ops.proto ./proto/
COPY origin/files ./files/

# Generate the gRPC stub code from the proto file
RUN python -m grpc_tools.protoc --proto_path=./proto --python_out=. --grpc_python_out=. ops.proto

# Expose port 8001 for the server to listen on
EXPOSE 8001

# Run the server
CMD ["python", "server.py"]
