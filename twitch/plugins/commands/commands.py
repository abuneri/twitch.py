import logging
import asyncio
import enum
from inspect import Parameter

from . import context

_has_fuzzywuzzy = True
try:
    from fuzzywuzzy import fuzz
except ImportError:
    _has_fuzzywuzzy = False

log = logging.getLogger(__name__)


class FuzzyRatio(enum.Enum):
    NONE = 0
    SIMPLE = 1
    PARTIAL = 2
    TOKEN_SORT_RATIO = 3
    TOKEN_SET_RATIO = 4


class FuzzyMatch:
    HAS_FUZZYWUZZY = _has_fuzzywuzzy

    # Note: force_ascii and full_process options only
    # apply with the TOKEN_SORT_RATIO and TOKEN_SET_RATIO types
    def __init__(self, ratio=FuzzyRatio.NONE, threshold=95, force_ascii=True,
                 full_process=True):
        self._ratio = ratio
        self._threshold = threshold
        self._force_ascii = force_ascii
        self._full_process = full_process

    @property
    def threshold(self):
        return self._threshold

    def match(self, user_command, registered_command):
        if self._ratio == FuzzyRatio.SIMPLE:
            return self._match_simple(user_command, registered_command)
        elif self._ratio == FuzzyRatio.PARTIAL:
            return self._match_partial(user_command, registered_command)
        elif self._ratio == FuzzyRatio.TOKEN_SORT_RATIO:
            return self._match_token_sort(user_command, registered_command)
        elif self._ratio == FuzzyRatio.TOKEN_SET_RATIO:
            return self._match_token_set(user_command, registered_command)
        else:
            # the ratio was NONE
            return -1

    def _match_simple(self, user_command, registered_command):
        return fuzz.ratio(user_command, registered_command)

    def _match_partial(self, user_command, registered_command):
        return fuzz.partial_ratio(user_command, registered_command)

    def _match_token_sort(self, user_command, registered_command):
        return fuzz.token_sort_ratio(user_command, registered_command,
                                     self._force_ascii, self._full_process)

    def _match_token_set(self, user_command, registered_command):
        return fuzz.token_set_ratio(user_command, registered_command,
                                    self._force_ascii, self._full_process)


class CommandParser:
    def __init__(self, command, pass_ctx, cmd_params, sig_params, message):
        self.cmd_params = cmd_params
        self.sig_params = sig_params
        self.ctx = context.Context(message) if pass_ctx else None
        self.name = command.__name__
        self.command = command

        if self.sig_params and pass_ctx:
            # we don't want to parse the context object as it always invoked
            # as the first parameter and doesnt depend on the command params
            self.sig_params.pop(0)

    async def _invoke(self, coro, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            try:
                log.info(
                    f'{self.name} raised an exception: {str(e)}')
            except asyncio.CancelledError:
                pass

    async def _invoke_kwargs(self, coro, ctx, **kwargs):
        if ctx:
            await self._invoke(coro, ctx=ctx, **kwargs)
        else:
            await self._invoke(coro, **kwargs)

    async def invoke(self):
        if not self.sig_params:
            if self.ctx:
                await self._invoke(self.command, ctx=self.ctx)
            else:
                await self._invoke(self.command)
            return

        same_param_type = _same_sig_param_types(self.sig_params)
        if same_param_type:
            if not self.cmd_params:
                log.info(f'the command `{self.name}` requires '
                         f'message parameters')
                return

            param_type = self.sig_params[0].kind
            sig_params_len = len(self.sig_params)
            cmd_params_len = len(self.cmd_params)

            if sig_params_len < cmd_params_len:
                await self._invoke_more_cmd_params(param_type)
            elif sig_params_len > cmd_params_len:
                await self._invoke_less_cmd_params(param_type)
            else:
                await self._invoke_equal_params(param_type)
        else:
            log.info('the parameter kind for all the commands parameters must'
                     'be the same')

    async def _invoke_more_cmd_params(self, param_type):
        if param_type == Parameter.VAR_POSITIONAL \
                or param_type == Parameter.POSITIONAL_OR_KEYWORD:
            """
            Python only allows 1 VAR_POSITIONAL argument to be in a method,
            so we don't have to worry about the cases where self.sig_params
            is > 1 and we can just invoke
            """
            typed_args = _get_invoke_args(self.cmd_params, self.sig_params,
                                          self.ctx)
            await self._invoke(self.command, *typed_args)

        elif param_type == Parameter.KEYWORD_ONLY:
            typed_kwargs = _get_invoke_kwargs(self.cmd_params, self.sig_params)
            await self._invoke_kwargs(self.command, self.ctx, **typed_kwargs)

        else:
            _log_unsupported_param_kind()

    async def _invoke_less_cmd_params(self, param_type):
        if param_type == Parameter.VAR_POSITIONAL:
            typed_args = _get_invoke_args(self.cmd_params, self.sig_params,
                                          self.ctx)
            await self._invoke(self.command, *typed_args)
        elif param_type == Parameter.POSITIONAL_OR_KEYWORD:
            log.info('can\'t invoke a command with less message parameters '
                     'than the signature requires')
        elif param_type == Parameter.KEYWORD_ONLY:
            log.info('can\'t build **kwargs with less message parameters than '
                     'command signature params')
        else:
            _log_unsupported_param_kind()

    async def _invoke_equal_params(self, param_type):
        if param_type == Parameter.VAR_POSITIONAL \
                or param_type == Parameter.POSITIONAL_OR_KEYWORD:
            typed_args = _get_invoke_args(self.cmd_params, self.sig_params,
                                          self.ctx)
            await self._invoke(self.command, *typed_args)

        elif param_type == Parameter.KEYWORD_ONLY:
            typed_kwargs = _get_invoke_kwargs(self.cmd_params, self.sig_params)
            await self._invoke_kwargs(self.command, self.ctx, **typed_kwargs)
        else:
            _log_unsupported_param_kind()


def _convert_to_annotation(sig_param, cmd_param):
    """
    Attempt to convert the parameter to the type of the signature parameter.
    The three builtin types supported are: str, int, and float

    :param sig_param:
    :param cmd_param:
    :return:
    """
    annotation = sig_param.annotation
    if str == annotation:
        return cmd_param
    elif int == annotation:
        return int(cmd_param)
    elif float == annotation:
        return float(cmd_param)
    else:
        # TODO: ? allow registry of custom types and
        #  auto build based on *args/**kwargs ?
        return cmd_param


def _get_invoke_args(cmd_params, sig_params, ctx):
    args = [arg for _, arg in zip(sig_params, cmd_params)]
    typed_args = [_convert_to_annotation(param, arg) for param, arg in
                  zip(sig_params, args)]
    if ctx:
        typed_args.insert(0, ctx)
    return typed_args


def _get_invoke_kwargs(cmd_params, sig_params):
    kwargs = {}
    for k, v in zip(sig_params, cmd_params):
        kwargs[k.name] = _convert_to_annotation(k, v)
    return kwargs


def _log_unsupported_param_kind():
    log.info('the parameter kind for the commands parameters isn\'t supported')


def _same_sig_param_types(sig_params):
    param_types = [param.kind for param in sig_params]
    return len(set(param_types)) == 1
