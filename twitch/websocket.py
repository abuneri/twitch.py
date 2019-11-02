import asyncio
import json
import logging
import time

import websockets

from .exception import TwitchException
from .event import Event
from .utils import split_skip_empty_parts
from .http import HTTPClient
from .message import Message
from .channel import Channel

log = logging.getLogger()

LF = '\n'
CRLF = '\r' + LF


class TwitchBackoff:
    """
    Using the algorithm recommended by twitch:
    https://dev.twitch.tv/docs/irc/guide#re-connecting-to-twitch-irc
    """
    def __init__(self):
        self._sleep_period = 1
        self._last_attempt = time.monotonic()
        self._first = True

    def sleep_for(self):
        # first attempt we do an immediate retry
        if self._first:
            self._first = False
            return 0
        else:
            self._sleep_period = self._sleep_period * 2
            return self._sleep_period


class WebSocketException(TwitchException):
    def __init__(self, original):
        super().__init__(str(original))


class WebSocketConnectionClosed(WebSocketException):
    pass


class WebSocketLoginFailure(WebSocketException):
    pass


class TwitchWebSocket(websockets.client.WebSocketClientProtocol):
    WSS_URL = 'wss://irc-ws.chat.twitch.tv:443'
    TMI_URL = 'tmi.twitch.tv'

    CHANNEL_PREFIX = '#'

    # connection management opcodes
    PING = 'PING'
    PONG = 'PONG'
    NICK = 'NICK'
    PASS = 'PASS'

    # general opcodes
    PRIVMSG = 'PRIVMSG'

    # membership opcodes
    JOIN = 'JOIN'
    PART = 'PART'
    MODE = 'MODE'
    NAMES = 'NAMES'

    # commands opcodes
    CLEARCHAT = 'CLEARCHAT'
    CLEARMSG = 'CLEARMSG'
    HOSTTARGET = 'HOSTTARGET'
    NOTICE = 'NOTICE'
    RECONNECT = 'RECONNECT'
    ROOMSTATE = 'ROOMSTATE'
    USERNOTICE = 'USERNOTICE'
    USERSTATE = 'USERSTATE'

    _glhf_parts = [
        ('001', ':Welcome, GLHF!'),
        ('002', f':Your host is {TMI_URL}'),
        ('003', ':This server is rather new'),
        ('004', ':-'),
        ('375', ':-'),
        ('372', ':You are in a maze of twisty passages, all alike.'),
        ('376', ':>')
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._emit = lambda *args: None
        self.authenticated = False

    @classmethod
    async def create_client(cls, client):
        ws = await websockets.connect(TwitchWebSocket.WSS_URL,
                                      loop=client.loop, klass=cls,
                                      compression=None)

        # add attributes to TwitchWebSocket
        ws._session = client
        ws.username = client.username
        token = client.http.access_token
        ws.access_token = token if token.startswith(
            HTTPClient.TOKEN_PREFIX) else f'{HTTPClient.TOKEN_PREFIX}{token}'
        ws._emit = client.event_handler.emit

        log.info(f'websocket created. connected to {TwitchWebSocket.WSS_URL}')

        # establish a valid connection to websocket
        await ws.send_authenticate()

        # poll for GLHF
        await ws.poll_event()

        if not ws.authenticated:
            raise WebSocketLoginFailure

        return ws

    # outgoing message management

    async def close(self, code=1000, reason=''):
        self.authenticated = False
        super().close(code=code, reason=reason)

    async def send(self, data):
        # TODO: Implement message 'rate-limiting' here, as specified
        #  in https://dev.twitch.tv/docs/irc/guide#command--message-limits
        await super().send(data)
        self._emit(Event.SOCKET_SEND, data)

    async def send_authenticate(self):
        pass_msg = f'{TwitchWebSocket.PASS} {self.access_token}'
        nick_msg = f'{TwitchWebSocket.NICK} {self.username}'

        await self.send(pass_msg)
        await self.send(nick_msg)

    async def send_pong(self):
        pong_msg = f'{TwitchWebSocket.PONG} :{TwitchWebSocket.TMI_URL}'
        await self.send(pong_msg)
        self._emit(Event.PONGED)

    async def send_join(self, channel_name):
        join_msg = \
            f'{TwitchWebSocket.JOIN} {TwitchWebSocket.CHANNEL_PREFIX}' \
            f'{channel_name}'
        await self.send(join_msg)

    async def send_message(self, channel_name, message):
        priv_msg = f'{TwitchWebSocket.PRIVMSG} ' \
                   f'{TwitchWebSocket.CHANNEL_PREFIX}{channel_name} :{message}'
        await self.send(priv_msg)

    # incoming message management

    async def poll_event(self):
        try:
            msg = await self.recv()
            await self.incoming_message(msg)
        except websockets.exceptions.ConnectionClosed as e:
            raise WebSocketConnectionClosed(e)

    async def incoming_message(self, msg):
        self._emit(Event.SOCKET_RECEIVE, msg)

        new_line = CRLF if CRLF in msg else LF
        msg_parts = split_skip_empty_parts(msg, new_line)
        msg_parts = self._handle_glhf(msg_parts)
        if msg_parts:
            if len(msg_parts) == 1:
                await self._handle_single_line_opcode(msg_parts[0])
            else:
                await self._handle_multi_line_opcode(msg_parts)

    async def _handle_single_line_opcode(self, msg):
        if TwitchWebSocket.PING in msg:
            self._emit(Event.PINGED)
            await self.send_pong()
        elif TwitchWebSocket.NOTICE in msg:
            if msg.endswith('Login authentication failed'):
                raise WebSocketLoginFailure(
                    'login authentication failed. ensure the username and '
                    'access token is valid')

        elif TwitchWebSocket.MODE in msg:
            msg_parts = split_skip_empty_parts(msg)
            if len(msg_parts) == 5:
                channel_name = msg_parts[2]
                gained = '+' in msg_parts[3]
                username = msg_parts[4]
                user = await self._session.get_user(login=username)
                self._emit(Event.MOD_STATUS_CHANGED, user, channel_name,
                           gained)

        else:
            # msg format is always this for these opcodes
            # :<user>!<user>@<user>.tmi.twitch.tv <opcode>\
            # #<channel> [optional additional]*
            msg_dict = TwitchWebSocket._parse_msg(msg)
            if msg_dict:
                opcode = msg_dict['opcode']
                channel_name = msg_dict['channel_name']
                username = msg_dict['username']
                user = await self._session.get_user(login=username)

                if opcode == TwitchWebSocket.PRIVMSG:
                    text = TwitchWebSocket._get_args(msg_dict)
                    if text:
                        text = ' '.join(text).lstrip(':')
                        channel = Channel(channel_name, session=self._session)
                        message = Message(text, user, channel,
                                          session=self._session)

                        self._emit(Event.MESSAGE, message)

                elif opcode == TwitchWebSocket.JOIN:
                    self._emit(Event.CHANNEL_JOINED, user, channel_name)

                elif opcode == TwitchWebSocket.PART:
                    self._emit(Event.CHANNEL_LEFT, user, channel_name)

                # TODO: handle remaining op codes

                else:
                    self._emit(Event.UNKNOWN, msg)

    async def _handle_multi_line_opcode(self, msg_parts):
        if TwitchWebSocket.NAMES in msg_parts:
            final_line = ':End of /NAMES list'
            usernames = []
            channel_name = None
            for names in msg_parts:
                if final_line not in names:
                    usernames.append(TwitchWebSocket._parse_names(names))
                else:
                    final_line_parts = split_skip_empty_parts(names)
                    channel_name = final_line_parts[3] if len(
                        final_line_parts) == 8 else None

            if usernames and None not in usernames and channel_name:
                users = await self._session.get_users(logins=usernames)
                self._emit(Event.LIST_CHATTERS, users, channel_name)

    def _handle_glhf(self, msg_parts):
        glhf = [f':{TwitchWebSocket.TMI_URL} {k} {self.username} {v}' for k, v
                in TwitchWebSocket._glhf_parts]
        if msg_parts == glhf:
            self.authenticated = True
            return None
        else:
            return msg_parts

    @staticmethod
    def _get_args(msg_dict):
        if 'args' in msg_dict:
            return msg_dict['args']
        return None

    @staticmethod
    def _parse_msg(msg):
        msg_parts = split_skip_empty_parts(msg)
        msg_dict = {}
        num_parts = len(msg_parts)
        if num_parts > 2:
            msg_dict['username'] = TwitchWebSocket._parse_tmi(msg_parts[0])
            msg_dict['opcode'] = msg_parts[1]
            msg_dict['channel_name'] = msg_parts[2].lstrip(
                TwitchWebSocket.CHANNEL_PREFIX)
        if num_parts > 3:
            msg_dict['args'] = msg_parts[3:]
        return msg_dict

    @staticmethod
    def _parse_tmi(tmi):
        tmi_suffix = f'.{TwitchWebSocket.TMI_URL}'
        if tmi.endswith(tmi_suffix):
            tmi_len = len(tmi_suffix)
            user_str = tmi[:-tmi_len]
            user_parts = user_str.split('@')
            if len(user_parts) == 2:
                return user_parts[1]
        return None

    @staticmethod
    def _parse_names(names_msg):
        msg_parts = split_skip_empty_parts(names_msg, ':')
        if len(msg_parts) == 2:
            return split_skip_empty_parts(msg_parts[1])
