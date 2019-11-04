import sys
import traceback
import shlex
import logging
import asyncio
from inspect import signature
from functools import partial

import twitch
from .commands import CommandParser

log = logging.getLogger(__name__)


class Bot(twitch.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command_prefix = kwargs.get('command_prefix', '!')
        self._commands = {}
        process_commands = partial(self.process_commands, _ctor=True)
        self.event_handler.register(twitch.Event.MESSAGE, process_commands)

    def command(self, **kwargs):
        def decorator(bot):
            def wrapper(coro):
                """
                TODO: allow command name to be fuzzy matched with a reasonable
                 threshold. User can specifc by passing in a bot.FuzzyMatch()
                 object, which defines the threshold to match on.

                 fuzzy_match = kwargs.get('fuzzy_match', FuzzyMatch.None())
                """
                name = kwargs.get('name')
                pass_ctx = kwargs.get('pass_ctx', True)
                command_name = name if name else coro.__name__

                if command_name in bot._commands.keys():
                    raise NameError(f'{command_name} is already a registered'
                                    f'command')
                elif not asyncio.iscoroutinefunction(coro):
                    raise TypeError(
                        f'{coro.__name__} '
                        f'must be a coroutine function to be a command')
                else:
                    bot._commands[command_name] = (coro, pass_ctx)

            return wrapper
        return decorator(self)

    async def process_commands(self, message, _ctor=False):
        if not _ctor:
            return
        try:
            content = message.content
            if content.startswith(self.command_prefix):
                parts = shlex.split(content)

                command_name = parts[0].lstrip(
                    self.command_prefix) if parts else None

                command_params = parts[1:] if len(parts) > 1 else None

                await self.invoke_command(command_name, command_params,
                                          message)
        except BaseException as e:
            log.info(str(e))
            _, _, tb = sys.exc_info()
            traceback.print_tb(tb, file=sys.stdout)

    async def invoke_command(self, name, params, message):
        command, pass_ctx = self._commands.get(name)
        if command:
            sig = signature(command)
            sig_params = list(sig.parameters.values())
            command_parser = CommandParser(command, pass_ctx, params,
                                           sig_params, message)
            await command_parser.invoke()
        else:
            log.info(f'{name} is not a registered command')
            pass
