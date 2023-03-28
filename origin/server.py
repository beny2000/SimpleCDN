import grpc
import ops_pb2_grpc
import ops_pb2
from concurrent import futures
import os


CHUNK_SIZE = 1024 * 1024  # 1MB

class OriginServer(ops_pb2_grpc.FileServerServicer):

      def __init__(self):
         self.origin_files = 'files/'
      
      def save_chunks_to_file(self, chunks):
         chunks_iter = [chunk for chunk in chunks]
         filename = chunks_iter[0].name
         with open(self.origin_files + filename, 'wb') as f:
            for chunk in chunks_iter:
                  f.write(chunk.buffer)

         return self.origin_files + filename
      
      def get_file_chunks(self, filename):
         try:
            with open(self.origin_files + filename, 'rb') as f:
               while True:
                  piece = f.read(CHUNK_SIZE)
                  if len(piece) == 0:
                        return
                  yield ops_pb2.Chunk(buffer=piece, name=filename)
         except Exception as e:
             print("Error: ", self.origin_files + filename, str(e))

      def put(self, request_iterator, context):
         location = self.save_chunks_to_file(request_iterator)
         return ops_pb2.Reply(length=os.path.getsize(location))

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