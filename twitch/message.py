class Message:
    def __init__(self, text, user, channel, *, state):
        self.content = text
        self.author = user
        self.channel = channel
        self._state = state
