import grpc
import os
import logging
from concurrent import futures

import ops_pb2
import ops_pb2_grpc

PORT = os.environ.get('PORT')
BACKUP_PORTS = [port for port in enumerate(os.environ.get('BACKUP_PORTS').split(","))]


STORAGE_DIR = os.environ.get('STORAGE_DIR', 'files/')
CHUNK_SIZE = 1024 * 1024  # 1MB
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])


class OriginServer(ops_pb2_grpc.FileServerServicer):

      def __init__(self):
         self.origin_files = STORAGE_DIR
      
      def _save_chunks_to_file(self, chunks):
         """
         Takes a list of chunks, and writes them to a file
         
         :param chunks: The chunks of the file that were uploaded
         :return: The file name of the file that was just saved.
         """
         chunks_iter = [chunk for chunk in chunks]
         filename = chunks_iter[0].name

         with open(self.origin_files + filename, 'wb') as f:
            for chunk in chunks_iter:
                  f.write(chunk.buffer)

         return filename
      
      def _get_file_chunks(self, filename):
         """
         Reads the file in chunks of CHUNK_SIZE, and yields each chunk as a Chunk message
         
         :param filename: The name of the file to be sent to the server
         :return: A generator object.
         """
         try:
            with open(self.origin_files + filename, 'rb') as f:
               while True:
                  piece = f.read(CHUNK_SIZE)

                  if len(piece) == 0:
                        return
                  yield ops_pb2.Chunk(buffer=piece, name=filename)

         except Exception as e:
            logging.error(f"Error: {self.origin_files + filename}. {str(e)}")

      def put(self, request_iterator, context):
         """
         Takes a stream of chunks, saves them to a file, and returns the size of the file
         
         :param request_iterator: Iterator that will be used to iterate over the chunks of data
         that are sent by the client
         :param context: This is the context object that is passed to the server.
         :return: The size of the file that was saved.
         """
         filename = self._save_chunks_to_file(request_iterator)
         # Send the file to the backup server

         for i in range(len(BACKUP_PORTS)):
             with grpc.insecure_channel(f'origin_backup{i+1}:{BACKUP_PORTS[i]}') as channel:
                 stub = ops_pb2_grpc.FileServerStub(channel)
                 stub.put(self._get_file_chunks(filename))

         logging.info(f"Stored file {filename}")
         return ops_pb2.Reply(length=os.path.getsize(self.origin_files + filename))

      def get(self, request, context):
         """
         It takes a request object, and returns a response object
         
         :param request: The request object that was sent from the client
         :param context: The context is a value passed in by the server and contains RPC-specific information
         :return: The file chunks
         """
         if request.name:
            logging.info(f"Served file {request.name}")
            return self._get_file_chunks(request.name)

def run_origin_server():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
  ops_pb2_grpc.add_FileServerServicer_to_server(OriginServer(), server)
  server.add_insecure_port(f'[::]:{PORT}')

  logging.info(f"Origin Server start on port {PORT}")
  server.start()
  server.wait_for_termination()

if __name__ == "__main__":
    run_origin_server()