import hashlib
import os


class SharedFile:
    def __init__(self, filename) -> None:
        self.filename = filename
        self.hash = self.getHash()


    def getHash(self):
        with open(os.path.join('../shared', self.filename), 'rb') as f:
            # Create a SHA256 hash object
            hasher = hashlib.sha256()

            # Read the file content in chunks (efficient for large files)
            chunk_size = 4096
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)

            # Get the hash value in hexadecimal format
            hash_value = hasher.hexdigest()

            return hash_value