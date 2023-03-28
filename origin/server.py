import grpc
import ops_pb2_grpc
import ops_pb2
from concurrent import futures
import os


CHUNK_SIZE = 1024 * 1024  # 1MB

class OriginServer(ops_pb2_grpc.FileServerServicer):

      def __init__(self):
         self.origin_files = './files/'
      
      def save_chunks_to_file(self, chunks, filename):
         with open(self.origin_files + filename, 'wb') as f:
            for chunk in chunks:
                  f.write(chunk.buffer)
      
      def get_file_chunks(self, filename):
         with open(self.origin_files + filename, 'rb') as f:
            while True:
               piece = f.read(CHUNK_SIZE)
               if len(piece) == 0:
                     return
               yield ops_pb2.Chunk(buffer=piece)

      def put(self, request_iterator, context):
         self.save_chunks_to_file(request_iterator, self.origin_files)
         return ops_pb2.Reply(length=os.path.getsize(self.origin_files))

      def get(self, request, context):
         print("GET")
         if request.name:
            return self.get_file_chunks(request.name)

def serve():
   PORT = os.environ.get('PORT', 8001)
   server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
   ops_pb2_grpc.add_FileServerServicer_to_server(OriginServer(), server)
   server.add_insecure_port(f'[::]:{PORT}')
   print("Server start on port", PORT)
   server.start()
   server.wait_for_termination()
      
if __name__ == "__main__":
   print("Server starting")
   serve()