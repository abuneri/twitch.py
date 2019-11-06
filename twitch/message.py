from datetime import datetime

from .tags import Tags, Emote


class Message:
    def __init__(self, content, user, channel, *, session, tags_data):
        self._content = content
        self._author = user
        self._channel = channel
        self._session = session
        # below are properties only set by tags
        self._emotes = None
        self._id = None
        self._time_sent = None

        if tags_data:
            emotes = tags_data.get(Tags.EMOTES)
            if emotes:
                emote_parts = emotes.split('/')
                self._emotes = [Emote(emote) for emote in emote_parts]

            tmi_time_sent = tags_data.get(Tags.TMI_SENT_TS)
            if tmi_time_sent:
                unix_epoch = float(tmi_time_sent) / 1000
                self._time_sent = datetime.utcfromtimestamp(unix_epoch)

    @property
    def content(self):
        return self._content

    @property
    def author(self):
        return self._author

    @property
    def channel(self):
        return self._channel

    @property
    def emotes(self):
        return self._emotes

    @property
    def id(self):
        return self._id

    @property
    def time_sent(self):
        return self._time_sent
