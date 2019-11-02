import asyncio
import logging
import signal
import aiohttp
import websockets

from .event import EventHandler, Event
from .http import HTTPClient, HTTPException
from .websocket import TwitchWebSocket, TwitchBackoff, \
    WebSocketConnectionClosed
from .exception import TwitchException
from .user import User

log = logging.getLogger(__name__)


class ClientException(TwitchException):
    pass


class Client:
    def __init__(self, *, loop=None, **kwargs):
        self.ws = None
        self.username = None
        self.loop = loop if loop else asyncio.get_event_loop()
        self.event_handler = EventHandler(self.loop)

        connector = kwargs.pop('connector', None)
        self.http = HTTPClient(connector=connector, loop=self.loop)
        self._closed = False

    # ================ #
    # event management #
    # ================ #

    def event(self, **kwargs):
        def decorator(client):
            def wrapper(coro):
                event_name = kwargs.get('name')
                if not asyncio.iscoroutinefunction(coro):
                    raise TypeError(
                        f'{coro.__name__} '
                        f'must be a coroutine function to be registered')

                real_name = event_name if event_name else coro.__name__
                alias = f' (with the alias ' \
                        f'{coro.__name__})' if event_name else ''

                client.event_handler.register(real_name, coro)
                log.debug(
                    f'{real_name}{alias} '
                    f'has successfully been registered as an event')
                return coro
            return wrapper
        return decorator(self)

    def wait_for(self, event, *, check=None, timeout=None):
        future = self.loop.create_future()
        if not check:
            def _c(*args):
                return True
            check = _c

        listener = self.event_handler[event]
        listener.append((future, check))
        return asyncio.wait_for(future, timeout=timeout, loop=self.loop)

    # ============== #
    # http utilities #
    # ============== #

    async def get_user(self, *, user_id=None, login=None):
        user_ids = [user_id] if user_id else None
        logins = [login] if login else None
        users = await self.get_users(user_ids=user_ids, logins=logins)
        for user in users:
            if user_id == user.user_id or login == user.login:
                return user

    async def get_users(self, *, user_ids=None, logins=None):
        resp = await self.http.get_users(user_ids=user_ids, logins=logins)
        users = [User(data, session=self) for data in resp['data'] if
                 resp and resp['data']]
        return users

    # =================== #
    # websocket utilities #
    # =================== #

    async def join_channel(self, channel_name):
        await self.ws.send_join(channel_name)

    async def send_message(self, channel_name, message):
        await self.ws.send_message(channel_name, message)

    # ===================== #
    # connection management #
    # ===================== #

    def is_connected(self):
        return self.event_handler.connected.is_set()

    async def wait_until_connected(self):
        await self.event_handler.connected.wait()

    async def _connect(self):
        ws = TwitchWebSocket.create_client(self)
        user = await self.get_user(login=self.username)
        self.ws = await asyncio.wait_for(ws, timeout=120.0, loop=self.loop)
        self.event_handler.emit(Event.CONNECTED, user)
        while True:
            await self.ws.poll_event()

    async def connect(self, *, reconnect=True):
        backoff = TwitchBackoff()
        while not self._closed:
            try:
                await self._connect()
            except (OSError,
                    HTTPException,
                    WebSocketConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                    websockets.InvalidHandshake,
                    websockets.WebSocketProtocolError) as e:

                self.event_handler.emit(Event.DISCONNECT)
                if not reconnect:
                    await self.close()
                    if isinstance(e,
                                  WebSocketConnectionClosed) and \
                            e.code == 1000:
                        # websocket was closed cleanly, no need to raise here
                        return
                    raise

                if self._closed:
                    return

                retry = backoff.sleep_for()
                log.exception(f'attemping to reconnect in {retry}s')
                await asyncio.sleep(retry, loop=self.loop)

    async def close(self):
        if self._closed:
            return
        await self.http.close_session()
        self._closed = True

        if self.ws and self.ws.open:
            await self.ws.close()

        self.event_handler.clear_connected()

    async def clear(self):
        self._closed = False
        self.event_handler.clear_connected()
        self.http.recreate_session()

    async def login(self, username, access_token):
        log.info('logging in with static username and access token')
        self.username = username
        await self.http.create_session(access_token)

    async def logout(self):
        await self.close()

    async def start(self, username, access_token, *, reconnect=True):
        await self.login(username, access_token)
        await self.connect(reconnect=reconnect)

    def run(self, username, access_token, *, reconnect=True):
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
        except NotImplementedError:
            pass

        async def launch():
            try:
                await self.start(username, access_token, reconnect=reconnect)
            finally:
                await self.close()

        def cb(*args):
            loop.stop()

        future = asyncio.ensure_future(launch(), loop=loop)
        future.add_done_callback(cb)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            log.info('received signal to terminate client and event loop')
        finally:
            future.remove_done_callback(cb)
            log.info('cleaning up active tasks')
            Client._cleanup_loop(loop)

        if not future.cancelled():
            return future.result()

    @staticmethod
    def _cleanup_loop(loop):
        try:
            Client._cancel_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            log.info('closing event loop')
            loop.close()

    @staticmethod
    def _cancel_tasks(loop):
        tasks = {t for t in asyncio.all_tasks(loop=loop) if not t.done()}
        if not tasks:
            return

        log.info(f'cleaning up {len(tasks)} tasks')
        for t in tasks:
            t.cancel()

        loop.run_until_complete(
            asyncio.gather(*tasks, loop=loop, return_exceptions=True))
        log.info('all tasks cancelled')

        for t in tasks:
            if t.cancelled():
                continue
            if t.exception():
                loop.call_exception_handler(
                    {
                        'message': 'unhandled exception during Client.run() '
                                   'shutdown.',
                        'exception': t.exception(),
                        'task': t
                    })
