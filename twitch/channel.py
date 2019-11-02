class Channel:
    def __init__(self, channel_name, *, session):
        self._name = channel_name
        self._session = session

    @property
    def name(self):
        return self._name

    async def send(self, message):
        await self._session.send_message(self.name, message)
