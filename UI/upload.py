import os
import grpc
import tkinter as tk
from tkinter import filedialog
import ops_pb2_grpc
import ops_pb2

CHUNK_SIZE = 1024 * 1024
ORIGIN_PORT = "8001"

class FileClient:
    def __init__(self, address):
        """
        Creates a connection to the server
        
        :param address: The address of the server
        """
        channel = grpc.insecure_channel(address)
        self.stub = ops_pb2_grpc.FileServerStub(channel)

    def get_file_chunks(self, filename):
        """
        Reads the file in chunks of size CHUNK_SIZE and yields a Chunk message for each chunk
        
        :param filename: The name of the file to be sent to the server
        :return: A generator object.
        """
        with open(filename, 'rb') as f:
            while True:
                piece = f.read(CHUNK_SIZE)
                if len(piece) == 0:
                    return
                yield ops_pb2.Chunk(buffer=piece, name=filename.split('/')[-1])

    def upload(self, in_file_name):
        """
        It takes a file name, splits it into chunks, and sends those chunks to the server
        
        :param in_file_name: The name of the file to upload
        """
        chunks_generator = self.get_file_chunks(in_file_name)
        response = self.stub.put(chunks_generator)
        assert response.length == os.path.getsize(in_file_name)

class UploadGUI:
    def __init__(self, channel):
        """
        It creates a window with two buttons, one to select a file and one to upload it
        
        :param channel: The channel to upload the file to
        """
        self.channel = channel

        self.window = tk.Tk()
        self.window.title("Upload Files")

        self.select_button = tk.Button(self.window, text="Select File", command=self.select_file)
        self.select_button.pack()

        self.upload_button = tk.Button(self.window, text="Upload File", command=self.upload_file, state=tk.DISABLED)
        self.upload_button.pack()

        self.status_label = tk.Label(self.window, text="")
        self.status_label.pack()

        self.file_path = None

    def run(self):
        """
        Runs the GUI. 
        """
        self.window.mainloop()

    def select_file(self):
        """
        It opens a file dialog, and if the user selects a file, it enables the upload button and displays
        the file path in the status label
        """
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            self.upload_button.configure(state=tk.NORMAL)
            self.status_label.configure(text=f"Selected file: {self.file_path}")
        else:
            self.upload_button.configure(state=tk.DISABLED)
            self.status_label.configure(text="No file selected")

    def upload_file(self):
        """
        It uploads the file to the server
        """
        try:
            self.channel.upload(self.file_path)
        except grpc.RpcError as e:
            self.status_label.configure(text=f"Error uploading file: {e.details()}")
            raise e

        self.status_label.configure(text=f"File uploaded successfully")

if __name__ == "__main__":
    client = FileClient(f'localhost:{ORIGIN_PORT}')
    upload_gui = UploadGUI(client)
    upload_gui.run()
