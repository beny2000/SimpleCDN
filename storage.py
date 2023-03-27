import os
import shutil
import logging


class FileObjectStorage:
    """ Basic interface for storing and retrieving files"""

    def __init__(self, base_dir):
        """
        Initializes base directory and logger
        
        :param base_dir: The directory where the data is stored
        """
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)

    def put(self, key, value):
        """
        Writes file to local storage. It takes a key and a value, and writes the value to a file with the given key
        
        :param key: The key of the object to be stored
        :param value: The value to be stored. This can be a string or binary data
        """
        try:
            file_path = os.path.join(self.base_dir, key)
            if isinstance(value, str):  # value is a path to a file
                shutil.copyfile(value, file_path)
            else:  # value is binary data
                with open(file_path, 'wb') as f:
                    f.write(value)
        except Exception as e:
            self.logger.error(f"Error putting object with key {key}: {str(e)}")
            raise e

    def get(self, key):
        """
        Returns the file contents as binary data.
        
        :param key: The key of the object to get.
        :return: The file contents as binary data.
        """
        try:
            file_path = os.path.join(self.base_dir, key)
            with open(file_path, 'rb') as f:
                value = f.read()
            return value
        except Exception as e:
            self.logger.error(f"Error getting object with key {key}: {str(e)}")
            raise e
