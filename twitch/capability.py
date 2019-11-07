import enum


class Capability(enum.Enum):
    TAGS = 0
    COMMANDS = 1
    MEMBERSHIP = 2
    CHAT_ROOMS = 3


class CapabilityConfig:
    """
    Capabilities are IRC data or events that will only be sent to the
    :class:`Client` if specificly requested by the client.

    Parameters
    -----------

    tags: Optional[:class:`bool`]
        If true, the client will request the tags
        (https://dev.twitch.tv/docs/irc/tags) capability from the server.
        Defaults to ``true``
    membership: Optional[:class:`bool`]
        If true, the client will request the membership
        (https://dev.twitch.tv/docs/irc/membership) capability from the server.
        Defaults to ``true``
    commands: Optional[:class:`bool`]
        If true, the client will request the commands
        (https://dev.twitch.tv/docs/irc/commands) capability from the server.
        Defaults to ``true``

    chat_rooms: Optional[:class:`bool`]
        If true, the client will request the chat-rooms
        (https://dev.twitch.tv/docs/irc/chat-rooms) capability from the server.
        Defaults to ``true``
    """
    def __init__(self, tags=True, membership=True, commands=True,
                 chat_rooms=True):
        self._tags = tags
        self._membership = membership
        self._commands = commands
        self._chat_rooms = chat_rooms

    @property
    def tags(self):
        """
        Whether or not to request the tags capability

        :type: :class:`bool`
        """
        return self._tags

    @property
    def membership(self):
        """
        Whether or not to request the membership capability

        :type: :class:`bool`
        """
        return self._membership

    @property
    def commands(self):
        """
        Whether or not to request the commands capability

        :type: :class:`bool`
        """
        return self._commands

    @property
    def chat_rooms(self):
        """
        Whether or not to request the chat rooms capability

        :type: :class:`bool`
        """
        return self._chat_rooms
