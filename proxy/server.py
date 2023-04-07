import os
import grpc
import random
import logging
from datetime import datetime, timedelta
from concurrent import futures
from threading import Thread
from flask import Flask

import ops_pb2_grpc
import ops_pb2

CHUNK_SIZE = 1024 * 1024  # 1MB
PORT = os.environ.get("PORT", 5000)
ORIGIN_PORT = os.environ.get("ORIGIN_PORT", 8001)
ORIGIN_BACKUPS = [port for port in os.environ.get('ORIGIN_BACKUPS').split(",")]
CACHE_DIR = os.environ.get("CACHE_DIR", "cache/")
TTL = float(os.environ.get("TTL", 120))
BASE_LATENCY = float(os.environ.get("BASE_LATENCY", 1))
IN_SCALE = float(os.environ.get("IN_SCALE", 1))
OUT_SCALE = float(os.environ.get("OUT_SCALE", 1))
TIME_FORMAT = '%Y-%m-%d-%H:%M:%S.%f'
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])

def introduce_latency(self, request_area_id=None):
    """
    Introduces the latency based on the area and request area ID.
    
    :param request_area_id: The ID of the area from which the request is being made. It is an optional
    parameter and if it is not provided, the latency will be calculated based on the current object's
    area
    :return: the calculated latency based on the input parameters.
    """
    if self.area == request_area_id:
        latency = BASE_LATENCY * IN_SCALE
    else:
        latency = BASE_LATENCY * OUT_SCALE

    return latency

class FileStore:
    def __init__(self, cache_location=CACHE_DIR):
        self.cache = cache_location

    def get_file_chunks(self, filename):
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


    def save_chunks_to_file(self, chunks, filename):
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
        
    def is_expired(self, key):
        """
        Checks if a cache key has expired based on its time-to-live (TTL) attribute.
        
        :param key: key of the cached item that we want to check for expiration
        :return: If the cache entry has expired, it returns True, otherwise it returns False.
        """
        try:
            ttl = os.getxattr(self.cache+key, 'user.ttl').decode()

            return datetime.strptime(ttl, TIME_FORMAT) < datetime.now()
        except Exception as e:
            return True
    
    def set_TTL(self, key):
        """
        Sets a time-to-live (TTL) attribute for a given key in a cache using the current time
        plus a specified TTL value.
        
        :param key: key of the cached item that we want to check for expiration
        """
        try:
            timestamp = datetime.now() + timedelta(seconds=TTL)
            os.setxattr(self.cache+key, 'user.ttl', timestamp.strftime(TIME_FORMAT).encode())
        except Exception as e:
            pass


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
        chunks_generator = self.storage.get_file_chunks(in_file_name)
        response = self.stub.put(chunks_generator)

        assert response.length == os.path.getsize(in_file_name)


    def download(self, target_name):
        """
        It sends a request to the server to download a file, and then saves the chunks of data it receives
        to a file
        
        :param target_name: The name of the file you want to download
        """
        response = self.stub.get(ops_pb2.Request(name=target_name))
        self.storage.save_chunks_to_file(response, target_name)
        self.storage.set_TTL(target_name)

liveliness = {f'origin_backup{i+1}:{ORIGIN_BACKUPS[i]}': False for i in range(len(ORIGIN_BACKUPS))}
liveliness.update({f'origin:{ORIGIN_PORT}': False})

def check_liveliness(liveliness):
    while True:
        for addr in liveliness.keys():
            try:
                with grpc.insecure_channel(addr) as channel:
                    stub = ops_pb2_grpc.FileServerStub(channel)
                    res = stub.heartbeat(ops_pb2.HeartbeatRequest(message="hello"))
                    liveliness[addr] = True if res.message == 'acknowledged' else False
            except Exception:
                liveliness[addr] = False

    
app = Flask(__name__)
file_store = FileStore()
client = FileClient(f'origin:{ORIGIN_PORT}', file_store) # hostname must be docker service name since the origin server is in the same network

@app.route('/heartbeat')
def heartbeat():
    """
    Responds to heartbeat with 'OK'.
    :return: 'OK'
    """
    return 'OK'

@app.route('/<path:path>')
def serve_GET(path):
    """
    Serves the requested file by checking if it is in the cache and returning it, otherwise
    downloading it from the origin server or a live backup if the primary origin is dead.
    
    :param path: The path of the file to be served
    :return: The file is being returned.
    """
    
    file = file_store.get(path)

    if file and not file_store.is_expired(path):
        logging.info(f"Served file {path}. Request was a cache hit")
        return file
    
    # If primary origin is dead, request file from a live backup
    if liveliness[f'origin:{ORIGIN_PORT}']:
        client.download(path) 
    else:
        logging.warning(f"Primary Origin on port {ORIGIN_PORT} is dead")
        backups = list(liveliness.keys())
        random.shuffle(backups)
        
        for backup in backups:
            if liveliness[backup]:
                FileClient(backup, file_store).download(path)

    logging.info(f"Served file {path}. Request was a cache miss")
    return file_store.get(path)


if __name__ == "__main__":
    th = Thread(target=check_liveliness, args=(liveliness,))
    th.start()

    app.run(debug=False, host="0.0.0.0", port=PORT)


