# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container and install dependencies
COPY backup/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code, proto file into the container
COPY backup/app.py ./
COPY proto/ops.proto ./proto/
COPY backup/cache ./cache/

# Generate the gRPC stub code from the proto file
RUN python -m grpc_tools.protoc --proto_path=./proto --python_out=. --grpc_python_out=. ops.proto

# Run the server
CMD ["python", "app.py"]
