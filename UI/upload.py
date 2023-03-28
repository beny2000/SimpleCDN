import grpc
import tkinter as tk
from tkinter import filedialog
import ops_pb2_grpc
import ops_pb2
import os


CHUNK_SIZE = 1024 * 1024




class FileClient:
    def __init__(self, address):
        channel = grpc.insecure_channel(address)
        self.stub = ops_pb2_grpc.FileServerStub(channel)

    def get_file_chunks(self, filename):
        with open(filename, 'rb') as f:
            while True:
                piece = f.read(CHUNK_SIZE)
                if len(piece) == 0:
                    return
                yield ops_pb2.Chunk(buffer=piece, name=filename.split('/')[-1])

    def upload(self, in_file_name):
        chunks_generator = self.get_file_chunks(in_file_name)
        response = self.stub.put(chunks_generator)
        assert response.length == os.path.getsize(in_file_name)

class UploadGUI:
    def __init__(self, channel):
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
        self.window.mainloop()

    def select_file(self):
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            self.upload_button.configure(state=tk.NORMAL)
            self.status_label.configure(text=f"Selected file: {self.file_path}")
        else:
            self.upload_button.configure(state=tk.DISABLED)
            self.status_label.configure(text="No file selected")

    def upload_file(self):
        try:
            FileClient('localhost:8001').upload(self.file_path)
        except grpc.RpcError as e:
            self.status_label.configure(text=f"Error uploading file: {e.details()}")
            raise e
            return

        self.status_label.configure(text=f"File uploaded successfully")

if __name__ == "__main__":
    channel = grpc.insecure_channel("localhost:50051")
    upload_gui = UploadGUI(channel)
    upload_gui.run()
