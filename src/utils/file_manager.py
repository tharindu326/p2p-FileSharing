from src.file import SharedFile
import requests
import os
from src.config import cfg
from src.logger import get_debug_logger
file_logger = get_debug_logger('file', f'logs/file.log')


class FileManager:
    def __init__(self):
        self.shared_directory = cfg.file.shared_directory
        self.save_directory = cfg.file.save_directory
        self.shared_files = []

    def update_shared_files(self):
        """Update the list of shared files from the shared directory."""
        self.shared_files = [SharedFile(file) for file in os.listdir(self.shared_directory)]
        file_logger.info(f"Shared files list updated:{[file.filename for file in self.shared_files]}")

    def initiate_file_download(self, peer_host, peer_port, filename):
        download_url = f"http://{peer_host}:{peer_port}/download/{filename}"
        try:
            response = requests.get(download_url)
            if response.status_code == 200:
                with open(f'{self.save_directory}{filename}', 'wb') as f:
                    f.write(response.content)
                file_logger.info(f"File {filename} downloaded successfully.")
            else:
                file_logger.error(f"Failed to download file {filename}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as err:
            file_logger.error(f"Error occurred while downloading file {filename}: {err}")

    def getSharedFile(self, filename, hash):
        for file in self.shared_files:
            if file.filename == filename or file.hash == hash:
                return True, file
        return False, None

    def addSharedFile(self, file):
        self.shared_files.append(file)
