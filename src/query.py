import uuid
import datetime


class Query:
    def __init__(self, filename, hash) -> None:
        self.id = uuid.uuid4()
        self.filename = filename
        self.hash = hash
        self.timestamp = datetime.datetime.now()
        self.responses = []

    def isSaved(self, response):
        for resp in self.responses:
            if (resp['host'] == response['host']) and (resp['port'] == response['port']) and (resp['filename'] == response['filename']) and (resp['filehash'] == response['filehash']):
                return True
        return False

    def addResponse(self, response):
        if not self.isSaved(response):
            self.responses.append(response)

    def getResponses(self):
        return self.responses