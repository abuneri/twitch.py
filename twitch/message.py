class Message:
    def __init__(self, text, user, channel, *, session):
        self._content = text
        self._author = user
        self._channel = channel
        self._session = session

    @property
    def content(self):
        return self._content

    @property
    def author(self):
        return self._author

    @property
    def channel(self):
        return self._channel
