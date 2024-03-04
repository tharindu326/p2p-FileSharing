import uuid
import datetime


class Query:
    def __init__(self, filename, hash) -> None:
        self.id = uuid.uuid4()
        self.filename = filename
        self.hash = hash
        self.timestamp = datetime.datetime.now()
        self.responses = []

    def addResponse(self, response):
        self.responses.append(response)

    def getResponses(self):
        return self.responses