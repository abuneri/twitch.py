import sys
import traceback
import shlex
import logging
import asyncio
from inspect import signature
from functools import partial

import twitch
from .commands import CommandParser, FuzzyMatch

log = logging.getLogger(__name__)


class Bot(twitch.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command_prefix = kwargs.get('command_prefix', '!')
        self.channels = kwargs.get('channels', None)
        self._commands = {}
        self._registered_types = {}

        # auto register some MESSAGE events for command parser
        process_commands = partial(self.process_commands, _ctor=True)
        self.event_handler.register(twitch.Event.MESSAGE, process_commands)

        # auto register CONNECTED events for auto-joining channels
        self.event_handler.register(twitch.Event.CONNECTED, self.join_channels)

    def command(self, **kwargs):
        def decorator(bot):
            def wrapper(coro):
                name = kwargs.get('name')
                pass_ctx = kwargs.get('pass_ctx', True)
                fuzzy_match = kwargs.get('fuzzy_match', FuzzyMatch())

                command_name = name if name else coro.__name__
                if command_name in bot._commands.keys():
                    raise NameError(f'{command_name} is already a registered'
                                    f'command')
                elif not asyncio.iscoroutinefunction(coro):
                    raise TypeError(
                        f'{coro.__name__} '
                        f'must be a coroutine function to be a command')
                else:
                    bot._commands[command_name] = (coro, pass_ctx, fuzzy_match)

            return wrapper
        return decorator(self)

    def register_type(self, type):
        def decorator(bot):
            def wrapper(func):
                if asyncio.iscoroutinefunction(func):
                    raise TypeError(
                        'type conversion registered should not be a coroutine')
                if not type:
                    raise TypeError(
                        'type trying to be registered is not valid')

                if type in bot._registered_types.keys():
                    raise ValueError(f'the type {type} is already registered')

                conversion_params = list(signature(func).parameters.values())
                num_params = len(conversion_params)
                if num_params > 1 or num_params < 1:
                    raise TypeError('your conversion function should only '
                                    'have one parameter. the parameter '
                                    'should be the string you are '
                                    'converting to the custom type')
                param = conversion_params[0]
                if param.annotation != str:
                    raise TypeError(
                        f'the conversion parameter {param.name} must be a str')

                # type successfully registered
                bot._registered_types[type] = func
            return wrapper
        return decorator(self)

    async def join_channels(self, user):
        if not self.channels:
            return
        for channel in self.channels:
            log.info(f'attemping to join {channel}s channel...')
            await self.join_channel(channel)

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
        command, pass_ctx, _ = self._commands.get(name, (None, False,
                                                         FuzzyMatch()))
        if command:
            await self._invoke_command(command, pass_ctx, params, message)
            return
        elif FuzzyMatch.HAS_FUZZYWUZZY:
            best_match = self._fuzzy_match_command(name)
            if best_match:
                try:
                    command, pass_ctx, _ = self._commands[best_match]
                    await self._invoke_command(command, pass_ctx, params,
                                               message)
                    return
                except KeyError:
                    pass

        log.info(f'{name} is not a registered command')

    async def _invoke_command(self, command, pass_ctx, params, message):
        sig = signature(command)
        sig_params = list(sig.parameters.values())
        command_parser = CommandParser(command, self._registered_types,
                                       pass_ctx, params,
                                       sig_params, message)
        await command_parser.invoke()

    def _fuzzy_match_command(self, name):
        matched_commands = {}
        for command in self._commands.items():
            command_name, (_,  _, fuzzy_matcher) = command
            ratio = fuzzy_matcher.match(name, command_name)
            if ratio >= fuzzy_matcher.threshold:
                matched_commands[command_name] = ratio

        best_match = max(matched_commands, key=lambda key: matched_commands[
            key]) if matched_commands else None
        return best_match
