import logging
import asyncio
from .events import Event

log = logging.getLogger(__name__)


class _EventTask(asyncio.Task):
    def __init__(self, original_coro, event_name, coro, *, loop):
        super().__init__(coro, loop=loop)
        self.__event_name = event_name
        self.__original_coro = original_coro

    def __repr__(self):
        info = [
            ('state', self._state.lower()),
            ('event', self.__event_name),
            ('coro', repr(self.__original_coro)),
        ]
        if self._exception is not None:
            info.append(('exception', repr(self._exception)))
        task = ' '.join(f'{t}={t}' for t in info)
        return f'<EventTask {task}>'


class EventHandler:
    def __init__(self, loop):
        self.loop = loop
        self._listeners = {}
        self._handlers = {Event.CONNECTED: self._handle_connected}
        self._connected = asyncio.Event(loop=self.loop)

    def __getitem__(self, event):
        try:
            listener = self._listeners[event]
        except KeyError:
            listener = []
            self._listeners[event] = listener
        return listener

    def register(self, event, coro):
        event = f'on_{event}' if not event.startswith('on_') else event
        setattr(self, event, coro)

    def emit(self, event, *args, **kwargs):
        handler = self._handlers.get(event)
        if handler:
            log.info(f'invoking custom handler for {event}')
            handler()

        log.info(f'emitting event {event}')
        method = f'on_{event}'

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    def _schedule_event(self, coro, event_name, *args, **kwargs):
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # schedule the task
        return _EventTask(original_coro=coro, event_name=event_name,
                          coro=wrapped, loop=self.loop)

    async def _run_event(self, coro, event_name, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self._on_error(event_name)
            except asyncio.CancelledError:
                pass

    async def _on_error(self, method):
        log.error(f'ignoring exception in {method}')

    @property
    def connected(self):
        return self._connected

    def clear_connected(self):
        self._connected.clear()

    def _handle_connected(self):
        self._connected.set()
