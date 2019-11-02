class Channel:
    def __init__(self, channel_name, *, state):
        self.name = channel_name
        self._state = state

    async def send(self, message):
        await self._state.send_message(self.name, message)
