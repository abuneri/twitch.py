class Context:
    def __init__(self, message):
        self.author = message.author
        self.channel = message.channel
        self.raw_message = message

    async def send(self, content):
        await self.channel.send(content)
