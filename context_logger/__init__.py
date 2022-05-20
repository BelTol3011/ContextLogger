import abc
import asyncio
import inspect
import warnings
from contextvars import ContextVar, Context
from typing import Any, Callable, Union, Optional, Awaitable


def async_safe(decorated_corofunc):
    async def reset_context(*args, **kwargs):
        loggerstack_contextvar.set([loggerstack_contextvar.get()[-1]])
        nlist_contextvar.set(get_current_nlist()[:])

        return await decorated_corofunc(*args, **kwargs)


    return reset_context


def log_decorator(message_or_func: Union[Any, Callable[[dict], Any]], **kwargs_decorator):
    """
    Returns a decorator that wraps a logger around a function.

    :param message_or_func: Can be ether a message (Any) or a function to which the argument values of the decorated
        function are passed and which returns a message.
    """

    def decorator(decorated_func):
        if inspect.iscoroutinefunction(decorated_func):
            async def wrapper(*args, **kwargs):
                if isinstance(message_or_func, Callable):
                    assigned_args = inspect.getcallargs(decorated_func, *args, *kwargs)

                    message_ = message_or_func(assigned_args)
                else:
                    message_ = message_or_func

                log(message_, **kwargs_decorator)

                return await decorated_func(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):
                if isinstance(message_or_func, Callable):
                    assigned_args = inspect.getcallargs(decorated_func, *args, *kwargs)

                    message_ = message_or_func(assigned_args)
                else:
                    message_ = message_or_func
                with log(message_, **kwargs_decorator):
                    return decorated_func(*args, **kwargs)

        return wrapper

    return decorator


def log(message, key: Callable[[Any], str] = lambda x: x, dont_advance: bool = False, prefix: str = None):
    return get_current_logger().log(message, key=key, dont_advance=dont_advance, prefix=prefix)


class BaseIndent(abc.ABC):
    @abc.abstractmethod
    def __call__(self, nlist: list[int]) -> str:
        ...


class NoneIndent(BaseIndent):
    def __call__(self, nlist: list[int]) -> str:
        return ""


class SpaceIndent(BaseIndent):
    def __init__(self, char: str = " "):
        self.char = char

    def __call__(self, nlist: list[int]) -> str:
        return self.char * (len(nlist) - 1)


class NumberedIndent(BaseIndent):
    def __call__(self, nlist: list[int]) -> str:
        return "".join([f"{number}. " for number in nlist])


class ListIndent(BaseIndent):
    def __call__(self, nlist: list[int]):
        if len(nlist) == 1:
            return " * "
        elif len(nlist) == 2:
            return " => "
        else:
            return " " * (len(nlist) - 1) + "-> "


STD_NONE_INDENT = NoneIndent()
STD_SPACE_INDENT = SpaceIndent()
STD_NUMBERED_INDENT = NumberedIndent()
STD_LIST_INDENT = ListIndent()


def strip_colons(string: str) -> str:
    if string.startswith(":"):
        string = string[1:]

    if string.endswith(":"):
        string = string[:-1]

    return string


def std_log_function(message_str: str, message_raw: Any, prefix: str, nlist: list[int],
                     indent: BaseIndent = STD_SPACE_INDENT):
    print((f"[{prefix:<12}] " if prefix else "") + indent(nlist) + message_str)


def std_prefixless_log_function(message_str: str, message_raw: Any, prefix: str, nlist: list[int],
                                indent: BaseIndent = STD_SPACE_INDENT):
    print(indent(nlist) + message_str)


class LogWarning(Warning): ...


class LogIndentorContextManager:
    def __enter__(self):
        indent()

    def __exit__(self, exc_type, exc_val, exc_tb):
        deindent()


_log_indentor_context_manage = LogIndentorContextManager()


class Logger:
    def __init__(self, prefix,
                 log_function: Callable[[str, Any, Any, list[int], Optional[BaseIndent]], None] = std_log_function,
                 indent: BaseIndent = STD_LIST_INDENT):
        self.log_function = log_function
        self.prefix = prefix
        self.indent_type = indent

    def log(self, message, key: Callable[[Any], str] = lambda x: x, dont_advance: bool = False, prefix: str = None):

        str_message = key(message)

        if str_message.startswith(":"):
            deindent()

        colon_stripped = strip_colons(str_message)
        if colon_stripped and colon_stripped != " ":
            if not dont_advance:
                advance()
            self.log_function(colon_stripped, message, self.prefix if prefix is None else prefix, get_current_nlist(),
                              self.indent_type)

        if str_message.endswith(":"):
            indent()

        return _log_indentor_context_manage

    def __enter__(self):
        push_logger(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self != get_current_logger():
            warnings.warn(LogWarning(f"Invalid log state! Exiting a logger ({self!r}) that is no longer the "
                                     f"top-of-stack logger ({get_current_logger()!r})."))

        pop_logger()


loggerstack_contextvar: ContextVar[list[Logger]] = ContextVar("__context_logger_loggerstack__",
                                                              default=[Logger("GLOBAL")])
nlist_contextvar: ContextVar[list[int]] = ContextVar("__context_logger_nlist__", default=[0])

get_current_logger: Callable[[], Logger] = lambda: loggerstack_contextvar.get()[-1]
get_current_nlist: Callable[[], list[int]] = lambda: nlist_contextvar.get()


class LogException(Exception): ...


def both(*funcs):
    def both_functions(*args, **kwargs):
        return [func(*args, **kwargs) for func in funcs]

    return both_functions


def indent():
    get_current_nlist().append(0)


def deindent():
    get_current_nlist().pop()

    if not get_current_nlist():
        raise LogException(
            f"Can't deindent! Invalid state of nlist={get_current_nlist()}! Reached bottom of hierarchy!")


def advance():
    get_current_nlist()[-1] += 1


def push_logger(logger: Logger):
    logger.__prev_nlist = get_current_nlist()[:]

    loggerstack_contextvar.get().append(logger)


def pop_logger():
    logger = loggerstack_contextvar.get().pop()

    if not hasattr(logger, "__prev_nlist"):
        warnings.warn(LogWarning(f"Logger {logger!r} was not pushed onto the logger stack using push_logger function."))
    else:
        # noinspection PyUnresolvedReferences
        nlist_contextvar.set(logger.__prev_nlist)

    return logger
