class Channel:
    def __init__(self, channel_name, *, session):
        self.name = channel_name
        self._session = session

    async def send(self, message):
        await self._session.send_message(self.name, message)
