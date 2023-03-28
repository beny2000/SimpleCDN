import grpc
import ops_pb2_grpc
import ops_pb2
from concurrent import futures
from flask import Flask, redirect
import random
import os
import grpc
import ops_pb2_grpc
import ops_pb2

CHUNK_SIZE = 1024 * 1024  # 1MB
app = Flask(__name__)

class FileStore:
    def __init__(self, cache_location='cache/'):
        self.cache = cache_location

    def get_file_chunks(self, filename):
        with open(self.cache+filename, 'rb') as f:
            while True:
                piece = f.read(CHUNK_SIZE)
                if len(piece) == 0:
                    return
                yield ops_pb2.Chunk(buffer=piece)


    def save_chunks_to_file(self, chunks, filename):
        with open(self.cache+filename, 'wb') as f:
            for chunk in chunks:
                f.write(chunk.buffer)

    def get(self, key):
        """
        Returns the file contents as binary data.
        
        :param key: The key of the object to get.
        :return: The file contents as binary data.
        """
        try:
            file_path = os.path.join('cache/', key)
            with open(file_path, 'rb') as f:
                value = f.read()
            return value
        except Exception as e:
            print(f"Error getting object with key {key}: {str(e)}")
            return False

class FileClient:
    def __init__(self, address, storage):
        channel = grpc.insecure_channel(address)
        self.stub = ops_pb2_grpc.FileServerStub(channel)
        self.storage = storage

    def upload(self, in_file_name):
        chunks_generator = self.storage.get_file_chunks(in_file_name)
        response = self.stub.put(chunks_generator)
        assert response.length == os.path.getsize(in_file_name)

    def download(self, target_name):
        response = self.stub.get(ops_pb2.Request(name=target_name))
        print('iiii', response)
        self.storage.save_chunks_to_file(response, target_name)

    
@app.route('/<path:path>')
def serve_GET(path):
    # Check if requested file is stored, if so return it other request file from origin server
    
    store = FileStore()
    client = FileClient('origin:8001', store)
    file = store.get(path)

    if file:
        return file
    
    client.download(path)
    return store.get(path)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=os.environ.get("PORT", 5000))


