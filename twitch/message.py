class Message:
    def __init__(self, text, user, channel, *, session):
        self.content = text
        self.author = user
        self.channel = channel
        self._session = session
