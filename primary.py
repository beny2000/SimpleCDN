import grpc
import ops_pb2_grpc
import ops_pb2
import threading
from concurrent import futures
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--port", default=None, help="The port to start the server on. Will use 1st line in the 'location' file if not specified")
parser.add_argument("--location", default='location', help="The name of the location file. Defaults to 'location'")
parser.add_argument("--operations", default='operations', help="The name of the operations file. Defaults to 'operations'")
parser.add_argument("--log", default='log', help="The name of the log file. Defaults to 'log'")
args = parser.parse_args()


class PrimaryService(ops_pb2_grpc.PrimaryBackupServiceServicer):
    """
    Implements the Primary Service of a Primary N-Backups Model. Operation and backups are read from file
    """

    def __init__(self, ops_file='operations', ports_file='location', backup_hostname='localhost', log_file='log'):
        """
        Reads the setup files and initializes the backup ports.
        
        :param ops_file: The file that contains the operations to be performed, defaults to operations
        (optional)
        :param ports_file: This is the file that contains the ports that the backup server is listening on,
        defaults to location (optional)
        :param backup_hostname: The hostname of the backup server, defaults to localhost (optional)
        :param log_file: The name of the file where the log will be written, defaults to log (optional)
        """
        self.operations_file = ops_file
        self.location_file = ports_file
        self.backup_hostname = backup_hostname
        self.log_file =log_file
        self.backup_ports = []
        self.seq_num = 0
        self._read_setup_file()

    def putRequestOperation(self, request, context):
        res = self._send_backups(request.key, request.value)
        return ops_pb2.replyPutRequest(response=res)

    def getRequestOperation(self, request, context):
        res = self._send_backups(request.key)
        return ops_pb2.replyGetRequest(response=res)

    def run(self):
        """
        Reads and runs the operations from the operations file
        """
        self._read_operations()

    def _read_setup_file(self):
        """
        Reads the file that contains the backup ports and adds them to backup ports list
        """
        print("Setting up backups")
        with open(self.location_file, 'r') as f:
            i = 0
            for line in f:
                if i == 0: #skip first port as it is the primary's port
                    i+=1 
                    continue
                self.backup_ports.append(line.strip("\n"))

    def _read_operations(self):
        """
        Reads the operations file, and for each operation, calls the _send_backups function to issue the operations to the backups
        """
        print("Reading operations")
        with open(self.operations_file, 'r') as f:
            for line in f:
                op = line.strip("\n").split(" ")
                print(f"Doing: {' '.join(op)}")

                if op[0] == 'get':
                    val = self._send_backups(op[1])
                    print(f"Got: {val}")

                elif op[0] == 'put':
                    val = self._send_backups(op[1], op[2])
                    print(f"Put: {op[1]}:{op[2]}. {val}")

                else:
                    print("Skipping invalid operation")

    def _send_backups(self, key, value=None):
        """
        Issues request/operation to backups. Spins up a thread for each backup, waits for all threads to finish, and returns the response if
        all backups agree
        
        :param key: the key to be stored
        :param value: the value to be stored in the key-value store
        :return: The value of the key if it exists, or None if it does not.
        """

        # Set operation
        if value:
            worker = self._send_put
            self.seq_num +=1
        else:
            worker = self._send_get

        # Spin up thread for each backup
        threads = [None] * len(self.backup_ports)
        responses = [None] * len(self.backup_ports)
        for i in range(len(self.backup_ports)):
            threads[i] = threading.Thread(target=worker, args=(i, key, value, responses))
            threads[i].start()

        # Wait for all threads to finish
        for t in threads:
            t.join()

        # Fail if all backups do not agree on response
        if not all(res == responses[0] for res in responses):
            return "Inconstant response, operation failed"
        
        return responses[0]
            
    def _log_operation(self, op, key, value, backup):
        """
        Writes operation, key, and value to the log file
        
        :param op: The operation being performed
        :param key: The key to be stored in the dict
        :param value: The value to be stored in the dict
        """
        print("Logged operation")
        with open(self.log_file, 'a') as f:
            f.write(f"{self.backup_hostname}:{self.backup_ports[backup]} {op} {key} {value}\n")

    def _send_get(self, backup, key, v=None, responses=[None]):
        """
        Sends a get request to the backup server and stores the response
        
        :param backup: the index of the backup to send the request to
        :param key: The key to be stored
        :param v: None
        :param responses: a list of responses from the backups
        :return: The response from the backup.
        """

        with grpc.insecure_channel(f"{self.backup_hostname}:{self.backup_ports[backup]}") as channel:
            stub = ops_pb2_grpc.PrimaryBackupServiceStub(channel)
            response = stub.getRequestOperation(ops_pb2.getRequest(key=key))
            responses[backup] = response.response
        self._log_operation('get', key, responses[backup], backup)
        return

    def _send_put(self, backup, key, value, responses=[None]):
        """
        Sends a put request to the backup server and stores the response
        
        :param backup: the index of the backup to send the request to
        :param key: The key to be put
        :param value: The value to be stored in the key-value store
        :param responses: This is a list of responses from the backups. The index of the list corresponds to
        the backup number
        :return: The response from the backup.
        """

        with grpc.insecure_channel(f"{self.backup_hostname}:{self.backup_ports[backup]}") as channel:
            stub = ops_pb2_grpc.PrimaryBackupServiceStub(channel)
            response = stub.putRequestOperation(
                ops_pb2.putRequest(key=key, value=value, sequenceNumber=self.seq_num))
            responses[backup] = response.response
        self._log_operation('put', key, value, backup)
        return


# If port is specified use it otherwise use first port from location file
if args.port:
    port = args.port
else:
    with open(args.location, 'r') as f:
        for line in f:
            port = line.strip("\n")
            break

# Start up Primary Service as script reading operations from file
primary_server = PrimaryService(
    ops_file=args.operations,
    ports_file=args.location,
    log_file=args.log)

try:
    primary_server.run()
    print("Completed Operations")
except KeyboardInterrupt:
    print("\nStopped Primary.")
except Exception as e:
    print("Primary failed, please check that backups are running on specified port", str(e))

# Start up Primary Service Server
try:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    ops_pb2_grpc.add_PrimaryBackupServiceServicer_to_server(primary_server, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f'Started server on localhost at port {port}.')
    server.wait_for_termination()
except KeyboardInterrupt:
    print("\nStopped Primary.")
except Exception as e:
    print("Primary Server failed, please check that backups are running on specified port", str(e))