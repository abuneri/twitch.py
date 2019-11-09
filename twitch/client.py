import asyncio
import logging
import signal
import aiohttp
import websockets

from .capability import CapabilityConfig
from .events import Event
from .event_handler import EventHandler
from .http import HTTPClient, HTTPException
from .websocket import WebSocketClient, TwitchBackoff
from .exception import WebSocketConnectionClosed, WebSocketLoginFailure
from .user import User

log = logging.getLogger(__name__)


class Client:
    """Represents a client connection that connects to Twitch.
        This class is used to interact with the Twitch IRC (via WebSocket)
        and Helix API.
        A number of options can be passed to the :class:`Client`.

        Parameters
        -----------

        capability: Optional[:class:`CapabilityConfig`]
            Defaults to ``CapabilityConfig()`` where all
            capabilities will be requested.
        loop: Optional[:class:`asyncio.AbstractEventLoop`]
            The :class:`asyncio.AbstractEventLoop` to use for asynchronous
            operations. Defaults to ``None``, in which case the
            default event loop is used via :func:`asyncio.get_event_loop()`.
        connector: :class:`aiohttp.BaseConnector`
            The connector to use for connection pooling.

        Attributes
        -----------
        ws
            The websocket gateway the client is currently connected to.
            Could be ``None``.
        loop: :class:`asyncio.AbstractEventLoop`
            The event loop that the client uses for HTTP requests and
            websocket operations.
        """
    def __init__(self, *, capability=CapabilityConfig(), loop=None, **kwargs):
        self.ws = None
        self.username = None
        self.capability = capability
        self.loop = loop if loop else asyncio.get_event_loop()
        self.event_handler = EventHandler(self.loop)

        connector = kwargs.pop('connector', None)
        self.http = HTTPClient(connector=connector, loop=self.loop)
        self._closed = False

    # ================ #
    # event management #
    # ================ #

    def event(self, name):
        """A decorator that registers an event to listen to.
                You can find more info about the events_ here.
                The events must be a ``coroutine``, if not,
                :exc:`TypeError` is raised.

                Example
                ---------

                .. code-block:: python3

                    @client.event(twitch.Event.CONNECTED)
                    async def on_connected(user):
                        print(f'{user.login} connected!')
                Raises
                --------
                TypeError
                    The coroutine passed is not actually a coroutine.

                ValueError
                    The coroutine's name can't start with an
                    underscore (``_``). Those are reserved for the library.
                """
        def decorator(client):
            def wrapper(coro):
                if not asyncio.iscoroutinefunction(coro):
                    raise TypeError(
                        f'{coro.__name__} '
                        f'must be a coroutine function to be registered')

                real_name = name if name else coro.__name__
                alias = f' (with the alias ' \
                        f'{coro.__name__})' if name else ''

                if real_name.startswith('_'):
                    raise ValueError(
                        f'event names cannot start with an underscore, '
                        f'those are reserverd for the library: {real_name}')

                client.event_handler.register(real_name, coro)
                log.debug(
                    f'{real_name}{alias} '
                    f'has successfully been registered as an event')
                return coro
            return wrapper
        return decorator(self)

    def wait_for(self, event, *, check=None, timeout=None):
        """
        Waits for a WebSocket event to be dispatched.
        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained way.
        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`.
        By default, it does not timeout.

        .. note::

            This does propagate the :exc:`asyncio.TimeoutError` for you
            in case of timeout and is provided for ease of use. In case
            the event returns multiple arguments, a :class:`tuple` containing
            those arguments is returned instead. This function returns the
            **first event that meets the requirements**.
        """
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
        """:class:`~twitch.User`: Returns a user object from the user_id
        or login passed

        .. warning::

            There isn't actually an endpoint provided by Twitch to receive
            one user, so this method is just a wrapper around ``get_users()``
            and returns the first user that matches the user_id OR login the
            caller passes in. You should only pass in a user_id AND login
            if they are referencing the same user. Otherwise, it's fine to
            just pass in either a single user_id or login.


        Parameters
        -----------

        user_id: Optional[:class:`int`]
            A user's ID

        login: Optional[:class:`str`]
            A user's login name (NOT display name)
        """
        user_ids = [user_id] if user_id else None
        logins = [login] if login else None
        users = await self.get_users(user_ids=user_ids, logins=logins)
        user_id = int(user_id) if user_id else user_id
        for user in users:
            if user_id == user.id or login == user.login:
                return user

    async def get_users(self, *, user_ids=None, logins=None):
        """List[:class:`~twitch.User`]: Returns a list of all the users defined
        by the user_ids and logins passed

        Parameters
        -----------

        user_ids: Optional[List[:class:`int`]]
            A list of user id's

        logins: Optional[List[:class:`str`]]
            A list of user's login names (NOT display names)

        """
        users = []
        resps = await self.http.get_users(user_ids=user_ids, logins=logins)
        for resp in resps:
            users += [User(data, session=self) for data in resp['data'] if
                      resp and resp['data']]
        return users

    # =================== #
    # websocket utilities #
    # =================== #

    async def join_channel(self, channel_name):
        """
        Sends an IRC message to the Websocket server to join the channel
        specified.

        .. note::

            Once the client is connected, you must explicitly join channels
            yourself, otherwise you won't receive any useful Events as they
            are all based on things happening while listening to channels.

        Parameters
        -----------

        channel_name: :class:`str`
            The name of the channel you wish to join
        """
        await self.ws.send_join(channel_name)

    async def send_message(self, channel_name, message):
        """
        Sends an IRC message to the Websocket server to send a chat message
        to the channel specified.

        Parameters
        -----------

        channel_name: :class:`str`
            The name of the channel you where wish to send the message

        message: :class:`str`
            The content of the message
        """
        # TODO: maybe add an opt-in parameter to wait for the sent message
        # and return it instead of getting nothing back. Might be useful
        # for some users since they'd get the full metadata of their message
        await self.ws.send_message(channel_name, message)

    # ===================== #
    # connection management #
    # ===================== #

    def is_connected(self):
        """Indicates if the websocket connection is closed."""
        return self.event_handler.connected.is_set()

    async def wait_until_connected(self):
        """
        Waits until the client's internal setup is complete and for the
        Websocket server to confirm our connection.
        """
        await self.event_handler.connected.wait()

    async def _connect(self):
        ws = WebSocketClient.create_client(self)
        user = await self.get_user(login=self.username)
        self.ws = await asyncio.wait_for(ws, timeout=120.0, loop=self.loop)
        self.event_handler.emit(Event.CONNECTED, user)
        while True:
            await self.ws.poll_event()

    async def connect(self, *, reconnect=True):
        """
        Creates a websocket connection and lets the websocket listen
        to messages from Twitch. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.
        Parameters
        -----------
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Twitch's part.
        Raises
        -------
        :exc:`.WebSocketConnectionClosed`
            The websocket connection has been terminated.
        """

        backoff = TwitchBackoff()
        while not self._closed:
            try:
                await self._connect()
            except (OSError,
                    HTTPException,
                    WebSocketConnectionClosed,
                    WebSocketLoginFailure,
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
        """
        Closes the connection to Twitch.
        """
        if self._closed:
            return
        await self.http.close_session()
        self._closed = True

        if self.ws and self.ws.open:
            await self.ws.close()

        self.event_handler.clear_connected()

    async def clear(self):
        """
        Clears the internal state of the client.
        After this, the client can be considered "re-opened", i.e.
        :meth:`is_closed` and :meth:`is_connected` both return ``False``.
        """
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
        """
        A shorthand coroutine for :meth:`login` + :meth:`connect`.
        """
        await self.login(username, access_token)
        await self.connect(reconnect=reconnect)

    def run(self, username, access_token, *, reconnect=True):
        """
        A blocking call that abstracts away the event loop
        initialisation from you.
        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        Roughly Equivalent to: ::

            try:
                loop.run_until_complete(start(*args, **kwargs))
            except KeyboardInterrupt:
                loop.run_until_complete(logout())
                # cancel all tasks lingering
            finally:
                loop.close()

        .. warning::

            This function must be the last function to call due to the fact
            that it is blocking. That means that registration of events
            or anything being called after this function call will not
            execute until it returns.
        """
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
