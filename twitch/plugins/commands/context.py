class Context:
    def __init__(self, message):
        self._author = message.author
        self._channel = message.channel
        self._raw_message = message

    @property
    def author(self):
        return self._author

    @property
    def channel(self):
        return self._channel

    @property
    def raw_message(self):
        return self._raw_message

    async def send(self, content):
        await self.channel.send(content)
