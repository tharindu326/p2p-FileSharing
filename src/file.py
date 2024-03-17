import hashlib
import os

class SharedFile:
    def __init__(self, cfg, filename):
        self.filename = filename
        self.cfg = cfg
        self.hash = self._get_hash()

    def _get_hash(self):
        """Generate a SHA256 hash for the contents of the file."""
        filepath = os.path.join(self.cfg.file.shared_directory, self.filename)
        hasher = hashlib.sha256()

        with open(filepath, 'rb') as file:
            for chunk in iter(lambda: file.read(self.cfg.file.chunk_size), b''):
                hasher.update(chunk)
        hash_value = hasher.hexdigest()  # hash value in hexadecimal format
        return hash_value

    def exists(self) -> bool:
        """Check if the file exists in the shared directory."""
        filepath = os.path.join(self.cfg.file.shared_directory, self.filename)
        return os.path.exists(filepath)

    def get_size(self) -> int:
        """Return the size of the file in bytes."""
        filepath = os.path.join(self.cfg.file.shared_directory, self.filename)
        return os.path.getsize(filepath)

    def update_hash(self) -> None:
        """Update the stored hash value for the file."""
        self.hash = self._get_hash()
