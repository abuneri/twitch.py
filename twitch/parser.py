import abc

from .opcodes import OpCode
from .events import Event
from .exception import WebSocketLoginFailure
from .utils import split_skip_empty_parts
from .message import Message
from .channel import Channel

CHANNEL_PREFIX = '#'
TAG_IDENTIFIER = '@'
TAG_SEPARATOR = ';'

TMI_URL = 'tmi.twitch.tv'
BASE_URL = 'twitch.tv'


class IMessageParser:
    @abc.abstractmethod
    async def parse(self, message):
        raise NotImplementedError


class MessageParserHandler:
    def __init__(self, *, ws):
        self._ws = ws


class SingleLineMessageParser(MessageParserHandler, IMessageParser):
    def __init__(self, *, ws):
        super().__init__(ws=ws)

    async def parse(self, msg):
        if OpCode.PING in msg:
            self._ws._emit(Event.PINGED)
            await self._ws.send_pong()
        elif OpCode.NOTICE in msg:
            if msg.endswith('Login authentication failed'):
                raise WebSocketLoginFailure(
                    'login authentication failed. ensure the username and '
                    'access token is valid')

        elif OpCode.MODE in msg:
            msg_parts = split_skip_empty_parts(msg)
            if len(msg_parts) == 5:
                channel_name = msg_parts[2]
                gained = '+' in msg_parts[3]
                username = msg_parts[4]
                user = await self._ws._session.get_user(login=username)
                self._ws._emit(Event.MOD_STATUS_CHANGED, user, channel_name,
                               gained)

        elif OpCode.CAP in msg:
            if OpCode.ACK in msg:
                if msg.endswith(f':{BASE_URL}/tags'):
                    self._ws._emit(Event.TAG_REQUEST_ACKED)

        else:
            """
            msg format is always this for these OpCode:

            [options tags]* :[<user>!<user>@<user>.]tmi.twitch.tv <opcode>
            #<channel> [optional args]*
            """
            msg_parts = split_skip_empty_parts(msg)
            if not msg_parts:
                return

            have_tags = msg_parts[0].startswith(TAG_IDENTIFIER)
            tags_msg = msg_parts.pop(0) if have_tags else None
            if tags_msg:
                tags_msg = tags_msg.lstrip(TAG_IDENTIFIER)
            tags_dict = _parse_tags(tags_msg)
            # TODO: used the parsed tag dictionary to set data on models

            msg_dict = _parse_msg(msg_parts)
            if msg_dict:
                opcode = msg_dict['opcode']
                channel_name = msg_dict['channel_name']
                username = msg_dict['username']
                user = await self._ws._session.get_user(login=username)

                if opcode == OpCode.PRIVMSG:
                    text = _get_args(msg_dict)
                    if text:
                        text = ' '.join(text).lstrip(':')
                        channel = Channel(channel_name,
                                          session=self._ws._session)
                        message = Message(text, user, channel,
                                          session=self._ws._session)

                        self._ws._emit(Event.MESSAGE, message)

                elif opcode == OpCode.JOIN:
                    self._ws._emit(Event.USER_JOIN_CHANNEL, user, channel_name)

                elif opcode == OpCode.PART:
                    self._ws._emit(Event.USER_LEFT_CHANNEL, user, channel_name)

                # TODO: handle remaining op codes

                else:
                    self._ws._emit(Event.UNKNOWN, msg)


class MultiLineMessageParser(MessageParserHandler, IMessageParser):
    def __init__(self, *, ws):
        super().__init__(ws=ws)

    async def parse(self, msg_parts):
        # TODO: fix parsing of multi-line messages
        if OpCode.NAMES in msg_parts:
            final_line = ':End of /NAMES list'
            usernames = []
            channel_name = None
            for names in msg_parts:
                if final_line not in names:
                    usernames.append(_parse_names(names))
                else:
                    final_line_parts = split_skip_empty_parts(names)
                    channel_name = final_line_parts[3] if len(
                        final_line_parts) == 8 else None

            if usernames and None not in usernames and channel_name:
                users = await self._ws._session.get_users(logins=usernames)
                self._ws._emit(Event.LIST_CHATTERS, users, channel_name)


def _get_args(msg_dict):
    if 'args' in msg_dict:
        return msg_dict['args']
    return None


def _parse_msg(msg_parts):
    msg_dict = {}
    num_parts = len(msg_parts)
    if num_parts > 2:
        msg_dict['username'] = _parse_tmi(msg_parts[0])
        msg_dict['opcode'] = msg_parts[1]
        msg_dict['channel_name'] = msg_parts[2].lstrip(CHANNEL_PREFIX)
    if num_parts > 3:
        msg_dict['args'] = msg_parts[3:]
    return msg_dict


def _parse_tmi(tmi):
    tmi_suffix = f'.{TMI_URL}'
    if tmi.endswith(tmi_suffix):
        tmi_len = len(tmi_suffix)
        user_str = tmi[:-tmi_len]
        user_parts = user_str.split('@')
        if len(user_parts) == 2:
            return user_parts[1]
    return None


def _parse_names(names_msg):
    msg_parts = split_skip_empty_parts(names_msg, ':')
    if len(msg_parts) == 2:
        return split_skip_empty_parts(msg_parts[1])


def _parse_tags(tags_msg):
    if not tags_msg:
        return None

    tag_parts = split_skip_empty_parts(tags_msg, TAG_SEPARATOR)

    def extract_kv(tag):
        return tag[0], tag[1]

    tags_dict = {extract_kv(tag) for tag in tag_parts if len(tag) == 2}
    return tags_dict
