import logging
import time

import websockets

from .opcodes import OpCode
from .events import Event
from .exception import WebSocketConnectionClosed
from .http import HTTPClient
from .parser import MessageParserHandler, TMI_URL, \
    CHANNEL_PREFIX, TAGS_CAPABILITY, MEMBERSHIP_CAPABILITY, COMMANDS_CAPABILITY

log = logging.getLogger()


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


class WebSocketClient(websockets.client.WebSocketClientProtocol):
    WSS_URL = 'wss://irc-ws.chat.twitch.tv:443'
    CAPABILITY_REQUEST = f'{OpCode.CAP} {OpCode.REQ} :'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._emit = lambda *args: None
        self._authenticated = False

    @staticmethod
    def _normalize_access_token(access_token):
        return access_token if access_token.startswith(
            HTTPClient.TOKEN_PREFIX) else \
            f'{HTTPClient.TOKEN_PREFIX}{access_token}'

    @classmethod
    async def create_client(cls, client):
        ws = await websockets.connect(WebSocketClient.WSS_URL,
                                      loop=client.loop, klass=cls,
                                      compression=None)

        # add attributes to TwitchWebSocket
        ws._session = client
        ws.username = client.username
        ws.capability = client.capability
        ws.access_token = WebSocketClient._normalize_access_token(
            client.http.access_token)
        ws._emit = client.event_handler.emit

        log.info(f'websocket created. connected to {WebSocketClient.WSS_URL}')

        # register internal helper handlers
        client.event_handler.register(Event.AUTHENTICATED,
                                      ws._authenticated_handler)

        # establish a valid connection to websocket
        await ws.send_authenticate()

        # poll for GLHF
        await ws.poll_event()

        return ws

    # outgoing message management

    async def close(self, code=1000, reason=''):
        super().close(code=code, reason=reason)

    async def send(self, data):
        # TODO: Implement message 'rate-limiting' here, as specified
        #  in https://dev.twitch.tv/docs/irc/guide#command--message-limits
        await super().send(data)
        self._emit(Event.SOCKET_SEND, data)

    async def send_authenticate(self):
        pass_msg = f'{OpCode.PASS} {self.access_token}'
        nick_msg = f'{OpCode.NICK} {self.username}'

        await self.send(pass_msg)
        await self.send(nick_msg)

    async def send_pong(self):
        msg = f'{OpCode.PONG} :{TMI_URL}'
        await self.send(msg)
        self._emit(Event.PONGED)

    async def send_join(self, channel_name):
        channel_name = channel_name if channel_name.startswith(
            CHANNEL_PREFIX) else CHANNEL_PREFIX + channel_name
        channel_name = channel_name.lower()
        msg = f'{OpCode.JOIN} {channel_name}'
        await self.send(msg)

    async def send_message(self, channel_name, message):
        msg = f'{OpCode.PRIVMSG} {CHANNEL_PREFIX}{channel_name} :{message}'
        await self.send(msg)

    async def send_tags_request(self):
        msg = f'{WebSocketClient.CAPABILITY_REQUEST}{TAGS_CAPABILITY}'
        await self.send(msg)

    async def send_membership_request(self):
        msg = f'{WebSocketClient.CAPABILITY_REQUEST}{MEMBERSHIP_CAPABILITY}'
        await self.send(msg)

    async def send_commands_request(self):
        msg = f'{WebSocketClient.CAPABILITY_REQUEST}{COMMANDS_CAPABILITY}'
        await self.send(msg)

    async def send_chat_rooms_request(self):
        msg = f'{OpCode.CAP} {OpCode.REQ} :{TAGS_CAPABILITY} ' \
              f'{COMMANDS_CAPABILITY}'
        await self.send(msg)

    # incoming message management

    async def poll_event(self):
        try:
            msg = await self.recv()
            await self.receive(msg)
        except websockets.exceptions.ConnectionClosed as e:
            raise WebSocketConnectionClosed(e)

    async def receive(self, msg):
        self._emit(Event.SOCKET_RECEIVE, msg)

        msg_handled = await MessageParserHandler.parse_irc_message(msg, self)
        if not msg_handled:
            log.info('following message from the server was not handled:\n'
                     f'{msg}')

    async def _authenticated_handler(self):
        if self.capability.tags:
            await self.send_tags_request()
        if self.capability.membership:
            await self.send_membership_request()
        if self.capability.commands:
            await self.send_commands_request()
        if self.capability.chat_rooms:
            await self.send_chat_rooms_request()
