import asyncio
import json
import logging
import time

import websockets

from .exception import TwitchException
from .event import Event
from .utils import split_skip_empty_parts
from .http import HTTPClient

log = logging.getLogger()

LF = '\n'
CRLF = '\r' + LF


class TwitchBackoff:
    """
    Using the algorithm recommended by twitch https://dev.twitch.tv/docs/irc/guide#re-connecting-to-twitch-irc
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

    PING = 'PING'
    PONG = 'PONG'
    NICK = 'NICK'
    PASS = 'PASS'
    JOIN = 'JOIN'
    PART = 'PART'
    PRIVMSG = 'PRIVMSG'
    NOTICE = 'NOTICE'

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
        ws = await websockets.connect(TwitchWebSocket.WSS_URL, loop=client.loop, klass=cls, compression=None)

        # add attributes to TwitchWebSocket
        ws.username = client.username
        token = client.http.access_token
        ws.access_token = token if token.startswith(HTTPClient.TOKEN_PREFIX) else f'{HTTPClient.TOKEN_PREFIX}{token}'
        ws._emit = client.event_handler.emit

        log.info(f'websocket created. connected to {TwitchWebSocket.WSS_URL}')

        # establish a valid connection to websocket
        await ws.send_authenticate()

        # poll for GLHF
        await ws.poll_event()

        if not ws.authenticated:
            raise WebSocketLoginFailure

        return ws

    async def incoming_message(self, msg):
        self._emit(Event.SOCKET_RECEIVE, msg)

        new_line = CRLF if CRLF in msg else LF
        msg_parts = split_skip_empty_parts(msg, new_line)
        msg_parts = self._handle_glhf(msg_parts)
        if msg_parts:
            if len(msg_parts) == 1:
                await self._handle_opcode(msg_parts[0])

    async def poll_event(self):
        try:
            msg = await self.recv()
            await self.incoming_message(msg)
        except websockets.exceptions.ConnectionClosed as e:
            raise WebSocketConnectionClosed(e)

    async def close(self, code=1000, reason=''):
        self.authenticated = False
        super().close(code=code, reason=reason)

    async def send(self, data):
        # TODO: Implement message 'rate-limiting' here, as specified
        #  in https://dev.twitch.tv/docs/irc/guide#command--message-limits
        self._emit(Event.SOCKET_SEND, data)
        await super().send(data)

    async def send_authenticate(self):
        pass_msg = f'{TwitchWebSocket.PASS} {self.access_token}'
        nick_msg = f'{TwitchWebSocket.NICK} {self.username}'

        await self.send(pass_msg)
        await self.send(nick_msg)

    async def send_pong(self):
        self._emit(TwitchWebSocket.PING)
        pong_msg = f'{TwitchWebSocket.PONG} :{TwitchWebSocket.TMI_URL}'
        await self.send(pong_msg)

    async def _handle_opcode(self, msg):
        if TwitchWebSocket.PING in msg:
            self._emit(TwitchWebSocket.PING)
            await self.send_pong()
        elif TwitchWebSocket.NOTICE in msg:
            if msg.endswith('Login authentication failed'):
                raise WebSocketLoginFailure(
                    'login authentication failed. ensure the username and access token is valid')

        # TODO: handle remaining op codes

    def _handle_glhf(self, msg_parts):
        if msg_parts == self._get_glhf():
            self.authenticated = True
            return None
        else:
            return msg_parts

    def _get_glhf(self):
        return [f':{TwitchWebSocket.TMI_URL} {k} {self.username} {v}' for k, v in TwitchWebSocket._glhf_parts]
