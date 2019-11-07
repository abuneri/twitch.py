import enum
from datetime import timedelta

from .tags import Tags


class Channel:
    class FollowersOnly(enum.Enum):
        DISABLED = 0
        ALL = 1
        LIMITED = 2

    def __init__(self, channel_name, *, session, tags_data):
        self._name = channel_name
        self._session = session
        # below are properties only set by tags
        self._id = None
        self._emote_only = None
        self._followers_only = None
        self._followers_only_limit = None
        self._r9k = None
        self._slow_duration = None
        self._sub_only = None

        if tags_data:
            room_id = tags_data.get(Tags.ROOM_ID)
            if room_id:
                self._id = int(room_id)

            emote_only = tags_data.get(Tags.EMOTE_ONLY)
            if emote_only:
                self._emote_only = int(emote_only) == 1

            followers_only = tags_data.get(Tags.FOLLOWERS_ONLY)
            if followers_only:
                followers_only = int(followers_only)
                if followers_only > 0:
                    self._followers_only = Channel.FollowersOnly.LIMITED
                elif followers_only == 0:
                    self._followers_only = Channel.FollowersOnly.ALL
                else:
                    self._followers_only = Channel.FollowersOnly.DISABLED

                if self._followers_only == Channel.FollowersOnly.LIMITED:
                    self._followers_only_limit = timedelta(
                        minutes=followers_only)

            r9k = tags_data.get(Tags.R9K)
            if r9k:
                r9k = int(r9k)
                self._r9k = r9k == 1

            slow = tags_data.get(Tags.SLOW)
            if slow:
                slow = int(slow)
                self._slow_duration = timedelta(seconds=slow)

            sub_only = tags_data.get(Tags.SUBS_ONLY)
            if sub_only:
                sub_only = int(sub_only)
                self._sub_only = sub_only == 1

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def emote_only(self):
        return self._emote_only

    @property
    def followers_only(self):
        return self._followers_only

    @property
    def followers_only_limit(self):
        return self._followers_only_limit

    @property
    def r9k(self):
        return self._r9k

    @property
    def slow_duration(self):
        return self._slow_duration

    @property
    def sub_only(self):
        return self._sub_only

    async def send(self, message):
        await self._session.send_message(self.name, message)
