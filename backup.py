import grpc
import ops_pb2_grpc
import ops_pb2
import threading
from concurrent import futures
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("port", default=None, nargs="?", help="The port to start the server on. Will use the ports in the 'location' file if not specified")
parser.add_argument("--location", default='location', help="The name of the location file. Defaults to 'location'")
args = parser.parse_args()

class BackupService(ops_pb2_grpc.PrimaryBackupServiceServicer):
    """
    Implements a Backup Service of a Primary N-Backups Model. It assumes the backup will not fail
    """

    def __init__(self):
        """
        Initializes the sequence number and datastore of the backup.
        """
        self.seq_num = 0
        self.datastore = dict() # Instance variables are not thread safe, if no backup fails data will remain consistent

    def getRequestOperation(self, request, context):
        """
        Retrieves value for given key from the backups datastore
        
        :param request: The request object that was sent from the client
        :param context: The context object that is passed to the server.
        :return: A replyGetRequest object with the retrieved value.
        """
        if request.key in self.datastore.keys():
            value = self.datastore[request.key]
        else:
            value = "not found"

        return ops_pb2.replyGetRequest(response=value)

    def putRequestOperation(self, request, context):
        """
        Updates the datastore with the key-value pair and returns a successful response. 
        Otherwise, it returns an unsuccessful response
        
        :param request: The request object that was sent by the client
        :param context: The context object that is passed to the server.
        :return: The response to the put request.
        """
        try:
            self.datastore[request.key] = request.value
        except Exception:
            return ops_pb2.replyPutRequest(response="unsuccessful")
        
        return ops_pb2.replyPutRequest(response="successful")


def start_backup_server(port):
    """
    It starts a gRPC server on the given port
    
    :param port: The port number that the server will listen on
    """
    backup = BackupService()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    ops_pb2_grpc.add_PrimaryBackupServiceServicer_to_server(backup, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f'Started server on localhost at port {port}.')
    server.wait_for_termination()

if args.port:
    # Start a single backup on given port
    try:
        start_backup_server(args.port)
    except KeyboardInterrupt:
        print("Stopping Backup Server")

else:
    # Read the ports from the location file and start a thread for each server
    try:
        ports = []
        threads = []

        # Read the n backup ports from the location file
        with open(args.location, 'r') as f:
            i = 0
            for line in f:
                if i == 0: #skip first port as it is the primary's port
                    i+=1 
                    continue
                ports.append(line.strip("\n"))
                
        print(f"Starting {len(ports)} backups")

        # Start a separate thread for each server
        for port in ports:
            t = threading.Thread(target=start_backup_server, args=(port,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    except KeyboardInterrupt:
        print("\nPress Ctrl+C again to stop all Backups.")

  







