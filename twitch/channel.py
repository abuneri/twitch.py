from .tags import Tags


class Channel:
    def __init__(self, channel_name, *, session, tags_data):
        self._name = channel_name
        self._session = session
        # below are properties only set by tags
        self._id = None

        if tags_data:
            room_id = tags_data.get(Tags.ROOM_ID)
            if room_id:
                self._id = int(room_id)

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    async def send(self, message):
        await self._session.send_message(self.name, message)
