import abc
from datetime import timedelta

from .opcodes import OpCode
from .events import Event
from .exception import WebSocketLoginFailure
from .utils import split_skip_empty_parts
from .message import Message
from .channel import Channel
from .tags import Tags
from.capability import Capability, CapabilityConfig

LF = '\n'
CRLF = '\r' + LF

CHANNEL_PREFIX = '#'
TAG_IDENTIFIER = '@'
TAG_SEPARATOR = ';'

TMI_URL = 'tmi.twitch.tv'
BASE_URL = 'twitch.tv'

TAGS_CAPABILITY = f'{BASE_URL}/tags'
MEMBERSHIP_CAPABILITY = f'{BASE_URL}/membership'
COMMANDS_CAPABILITY = f'{BASE_URL}/commands'
CHAT_ROOMS_CAPABILITY = f':{TAGS_CAPABILITY} {COMMANDS_CAPABILITY}'

CAPABILITY_ACK_PREFIX = f':{TMI_URL} {OpCode.CAP} * {OpCode.ACK}'

NAMES_LIST_END = ':End of /NAMES list'

GLHF_PARTS = [
    ('001', ':Welcome, GLHF!'),
    ('002', f':Your host is {TMI_URL}'),
    ('003', ':This server is rather new'),
    ('004', ':-'),
    ('375', ':-'),
    ('372', ':You are in a maze of twisty passages, all alike.'),
    ('376', ':>')
]


class IMessageParser:
    @abc.abstractmethod
    async def parse(self, message):
        raise NotImplementedError


class MessageParserHandler:
    def __init__(self, *, ws):
        self._ws = ws
        self._message_handled = False

    def emit(self, event, *args):
        self._message_handled = True
        self._ws._emit(event, *args)

    @staticmethod
    async def parse_irc_message(msg, ws):
        # IRC spec (https://tools.ietf.org/html/rfc2812)
        # says new lines will always be CRLF
        msg_parts = split_skip_empty_parts(msg, CRLF)
        msg_parts = _handle_glhf(msg_parts, ws)
        if msg_parts:
            if len(msg_parts) == 1:
                parser = SingleLineMessageParser(ws=ws)
                return await parser.parse(msg_parts[0])
            else:
                parser = MultiLineMessageParser(ws=ws)
                return await parser.parse(msg_parts)
        else:
            ws._authenticated = True
            ws._emit(Event._AUTHENTICATED)
            return True


class SingleLineMessageParser(MessageParserHandler, IMessageParser):
    def __init__(self, *, ws):
        super().__init__(ws=ws)
        self._message_handled = False
        self._tags_data = None

    @property
    def tags_data(self):
        return self._tags_data

    async def parse(self, msg):
        self._message_handled = False

        have_tags = msg.startswith(TAG_IDENTIFIER)
        tags_dict, remaining_msg = _parse_whole_msg(msg, have_tags)
        msg = remaining_msg

        self._tags_data = tags_dict

        if OpCode.PING in msg:
            self.emit(Event.PINGED)
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
                self.emit(Event.MOD_STATUS_CHANGED, user, channel_name,
                          gained)

        elif CAPABILITY_ACK_PREFIX in msg:
            capability = _get_capability_ack_single(msg)
            if not capability:
                return
            if capability == Capability.TAGS:
                self.emit(Event.TAG_REQUEST_ACKED)
            elif capability == Capability.MEMBERSHIP:
                self.emit(Event.MEMBERSHIP_REQUEST_ACKED)
            elif capability == Capability.COMMANDS:
                self.emit(Event.COMMANDS_REQUEST_ACKED)
            elif capability == Capability.CHAT_ROOMS:
                self.emit(Event.CHAT_ROOMS_REQUEST_ACKED)

        elif OpCode.GLOBALUSERSTATE in msg:
            user_id = tags_dict.get(Tags.USER_ID)
            user = await self._ws._session.get_user(user_id=user_id)
            user.add_tags_data(tags_dict)
            self.emit(Event.GLOBAL_USERSTATE_RECEIVED, user)

        else:
            """
            msg format is always this for these OpCode:

            [options tags]* :[<user>!<user>@<user>.]tmi.twitch.tv <opcode>
            #<channel> [optional args]*
            """
            msg_parts = split_skip_empty_parts(msg)
            if not msg_parts:
                return False

            msg_dict = _parse_msg(msg_parts)
            if msg_dict:
                opcode = msg_dict['opcode']
                channel_name = msg_dict['channel_name']
                username = msg_dict['username']

                user = await self._ws._session.get_user(login=username)
                if user:
                    user.add_tags_data(tags_dict)
                channel = Channel(channel_name,
                                  session=self._ws._session,
                                  tags_data=tags_dict)

                if opcode == OpCode.PRIVMSG:
                    content = _get_args(msg_dict)
                    if content:
                        text = ' '.join(content).lstrip(':')
                        message = Message(text, user, channel,
                                          session=self._ws._session,
                                          tags_data=tags_dict)
                        self.emit(Event.MESSAGE, message)

                elif opcode == OpCode.CLEARCHAT:
                    banned_user = _get_args(msg_dict)
                    if banned_user:
                        banned_user = banned_user[0].lstrip(':')
                        banned_user = await self._ws._session.get_user(
                            login=banned_user)

                    if Tags.BAN_DURATION in tags_dict:
                        delta = timedelta(
                            seconds=int(tags_dict[Tags.BAN_DURATION]))
                        self.emit(Event.USER_BANNED, banned_user, delta)
                    else:
                        if banned_user:
                            self.emit(Event.USER_PERMANENT_BANNED, banned_user)
                        else:
                            self.emit(Event.CHAT_CLEARED, channel)

                elif opcode == OpCode.CLEARMSG:
                    try:
                        username = tags_dict[Tags.LOGIN]
                        content = _get_args(msg_dict)[0]

                        user = await self._ws._session.get_user(login=username)
                        message = Message(content, user, content,
                                          session=self._ws._session,
                                          tags_data=tags_dict)
                        self.emit(Event.MESSAGE_CLEARED, message)
                    except (KeyError, IndexError):
                        # meh
                        pass

                elif opcode == OpCode.ROOMSTATE:
                    self.emit(Event.ROOMSTATE_RECEIVED, channel)

                elif opcode == OpCode.USERSTATE:
                    self.emit(Event.USER_JOIN_CHANNEL, user, channel)

                elif opcode == OpCode.JOIN:
                    self.emit(Event.USER_JOIN_CHANNEL, user, channel)

                elif opcode == OpCode.PART:
                    self.emit(Event.USER_LEFT_CHANNEL, user, channel)

                elif opcode == OpCode.USERNOTICE:
                    # TODO: handle this at some point,
                    #  can't be bothered right now
                    pass

                else:
                    self.emit(Event.UNKNOWN, msg)

        return self._message_handled


class MultiLineMessageParser(MessageParserHandler, IMessageParser):
    def __init__(self, *, ws):
        super().__init__(ws=ws)
        self._sl_parser = SingleLineMessageParser(ws=ws)

    async def parse(self, msg_parts):
        self._message_handled = False

        cap_ack = all([CAPABILITY_ACK_PREFIX in msg for msg in msg_parts])

        if cap_ack:
            cap_config = _get_capability_ack_multi(msg_parts)
            if cap_config.tags:
                self.emit(Event.TAG_REQUEST_ACKED)
            if cap_config.membership:
                self.emit(Event.MEMBERSHIP_REQUEST_ACKED)
            if cap_config.commands:
                self.emit(Event.COMMANDS_REQUEST_ACKED)
            if cap_config.chat_rooms:
                # although the doc says chat rooms doesn't have an ack, it
                # actually does...
                self.emit(Event.CHAT_ROOMS_REQUEST_ACKED)
        else:
            usernames = []
            channel = None
            for message in msg_parts:
                if any(
                        [getattr(OpCode, opcode) in message for opcode in
                         OpCode._fields]):
                    self._message_handled = await self._sl_parser.parse(
                        message)
                else:
                    # We must have received part of a /NAMES list
                    if NAMES_LIST_END not in message:
                        usernames += _parse_names(message)
                    else:
                        final_line_parts = split_skip_empty_parts(message)
                        channel_name = final_line_parts[3].lstrip(
                            CHANNEL_PREFIX) if len(
                            final_line_parts) == 8 else None

                        if channel_name:
                            channel = \
                                Channel(channel_name,
                                        session=self._ws._session,
                                        tags_data=self._sl_parser.tags_data)

            if usernames and channel:
                users = await self._ws._session.get_users(logins=usernames)
                self.emit(Event.LIST_USERS, users, channel)

        return self._message_handled


def _handle_glhf(msg_parts, ws):
    glhf = [f':{TMI_URL} {k} {ws.username} {v}' for k, v in GLHF_PARTS]
    return None if msg_parts == glhf else msg_parts


def _get_args(msg_dict):
    if 'args' in msg_dict:
        return msg_dict['args']
    return None


def _parse_whole_msg(msg, have_tags):
    tags_dict = None
    if have_tags:
        tags_msg = msg.lstrip(TAG_IDENTIFIER)
        tags_msg = tags_msg.split(' ', 1)[0]
        tags_dict = _parse_tags(tags_msg)
    non_tags_msg = msg.split(' ', 1)
    remaining_msg = ' '.join(non_tags_msg) if not have_tags else non_tags_msg[
        1]
    return tags_dict, remaining_msg


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


def _parse_names(name_msg):
    msg_parts = split_skip_empty_parts(name_msg, ':')
    if len(msg_parts) == 2:
        names = msg_parts[1]
        return split_skip_empty_parts(names)


def _parse_tags(tags_msg):
    if not tags_msg:
        return None

    tag_parts = [tag_part.split('=') for tag_part in
                 split_skip_empty_parts(tags_msg, TAG_SEPARATOR)]

    tags_dict = {kv[0]: kv[1] for kv in tag_parts if len(kv) == 2}
    return tags_dict


def _get_capability_ack_single(msg):
    if msg.endswith(f':{TAGS_CAPABILITY}'):
        return Capability.TAGS
    elif msg.endswith(f':{MEMBERSHIP_CAPABILITY}'):
        return Capability.MEMBERSHIP
    elif msg.endswith(f':{COMMANDS_CAPABILITY}'):
        return Capability.COMMANDS
    elif msg.endswith(f'{CHAT_ROOMS_CAPABILITY}'):
        return Capability.CHAT_ROOMS
    return None


def _get_capability_ack_multi(msg_parts):
    tags = any(
        [msg.endswith(f':{TAGS_CAPABILITY}') for msg in msg_parts]
    )
    membership = any(
        [msg.endswith(f':{MEMBERSHIP_CAPABILITY}') for msg in msg_parts]
    )
    commands = any(
        [msg.endswith(f':{COMMANDS_CAPABILITY}') for msg in msg_parts]
    )
    chat_rooms = any(
        [msg.endswith(f'{CHAT_ROOMS_CAPABILITY}') for msg in msg_parts]
    )

    return CapabilityConfig(tags, membership, commands, chat_rooms)
