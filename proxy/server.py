import os
import grpc
import logging
from concurrent import futures
from flask import Flask

import ops_pb2_grpc
import ops_pb2

CHUNK_SIZE = 1024 * 1024  # 1MB
PORT = os.environ.get("PORT", 5000)
ORIGIN_PORT = os.environ.get("ORIGIN_PORT", 8001)
CACHE_DIR = os.environ.get("CACHE_DIR", "cache/")
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])


class FileStore:
    def __init__(self, cache_location=CACHE_DIR):
        self.cache = cache_location

    def _get_file_chunks(self, filename):
        """
        Reads the file in chunks of size CHUNK_SIZE, and yields each chunk as a Chunk message
        message
        
        :param filename: The name of the file to be sent
        :return: A generator object.
        """
        with open(self.cache+filename, 'rb') as f:
            while True:
                piece = f.read(CHUNK_SIZE)
                if len(piece) == 0:
                    return
                yield ops_pb2.Chunk(buffer=piece)


    def _save_chunks_to_file(self, chunks, filename):
        """
        It takes a list of chunks and a filename, and writes the chunks to the file
        
        :param chunks: The chunks of data that are being downloaded
        :param filename: The name of the file to be downloaded
        """
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
            file_path = os.path.join(CACHE_DIR, key)
            with open(file_path, 'rb') as f:
                value = f.read()
            return value
        except Exception as e:
            return False

class FileClient:
    def __init__(self, address, file_store):
        """
        Initializes the file store interface, creates a gRPC channel to the origin server and server stub
        
        :param address: The address of the origin server
        :param file_store: The path to the directory where the files will be stored
        """
        channel = grpc.insecure_channel(address)
        self.stub = ops_pb2_grpc.FileServerStub(channel)
        self.storage = file_store

    def upload(self, in_file_name):
        """
        It takes a file name, splits it into chunks, and sends those chunks to the server
        
        :param in_file_name: The name of the file to be uploaded
        """
        chunks_generator = self.storage._get_file_chunks(in_file_name)
        response = self.stub.put(chunks_generator)

        assert response.length == os.path.getsize(in_file_name)


    def download(self, target_name):
        """
        It sends a request to the server to download a file, and then saves the chunks of data it receives
        to a file
        
        :param target_name: The name of the file you want to download
        """
        response = self.stub.get(ops_pb2.Request(name=target_name))
        self.storage._save_chunks_to_file(response, target_name)

    
app = Flask(__name__)
file_store = FileStore()
client = FileClient(f'origin:{ORIGIN_PORT}', file_store) # hostname must be docker service name since the origin server is in the same network

@app.route('/<path:path>')
def serve_GET(path):
    """
    If the file is in the cache, return it, otherwise download it from the origin server and return it
    
    :param path: The path of the file to be served
    :return: The file is being returned
    """
    file = file_store.get(path)

    if file:
        logging.info(f"Served file {path}. Request was a cache hit")
        return file
    
    client.download(path)
    logging.info(f"Served file {path}. Request was a cache miss")
    return file_store.get(path)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=PORT)


