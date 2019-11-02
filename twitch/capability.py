import enum


class Capability(enum.Enum):
    TAGS = 0
    COMMANDS = 1
    MEMBERSHIP = 2
    CHAT_ROOMS = 3


class CapabilityConfig:
    def __init__(self, tags=True, membership=True, commands=True,
                 chat_rooms=True):
        self._tags = tags
        self._membership = membership
        self._commands = commands
        self._chat_rooms = chat_rooms

    @property
    def tags(self):
        return self._tags

    @property
    def membership(self):
        return self._membership

    @property
    def commands(self):
        return self._commands

    @property
    def chat_rooms(self):
        return self._chat_rooms
