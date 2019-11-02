class Message:
    def __init__(self, text, user, channel_name):
        self.content = text
        self.author = user
        self._channel_name = channel_name

    @property
    def channel(self):
        # future proofing in-case they ever add GET /channels endpoint.
        # This can then just be changed to return a channel object
        return self._channel_name
