import abc
import inspect
from contextvars import ContextVar
from typing import Any, Callable, Union, Optional


def log_decorator(message_or_func: Union[Any, Union[Callable[[dict], Any]]], **kwargs_decorator):
    """
    Returns a decorator that wraps a logger around a function.

    :type message_or_func: Can be ether a message (Any) or a function to which the arguments are passed and which
        returns a message.
    """

    def decorator(decorated_func):
        if inspect.iscoroutinefunction(decorated_func):
            async def wrapper(*args, **kwargs):
                if isinstance(message_or_func, Callable):
                    assigned_args = inspect.getcallargs(decorated_func, *args, **kwargs)

                    message_ = message_or_func(assigned_args)
                else:
                    message_ = message_or_func
                with log(message_, **kwargs_decorator):
                    return await decorated_func(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):
                if isinstance(message_or_func, Callable):
                    assigned_args = inspect.getcallargs(decorated_func, *args, **kwargs)

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
        raise NotImplementedError()


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


STD_NONE_INDENT = NoneIndent()
STD_SPACE_INDENT = SpaceIndent()
STD_NUMBERED_INDENT = NumberedIndent()


def strip_colons(string: str) -> str:
    if string.startswith(":"):
        string = string[1:]

    if string.endswith(":"):
        string = string[:-1]

    return string


def std_log_function(message_str: str, message_raw: Any, prefix: str, nlist: list[int], indent: BaseIndent = STD_SPACE_INDENT):
    print((f"[{prefix}] " if prefix else "") + indent(nlist) + message_str)


class Logger:
    def __init__(self, prefix,
                 log_function: Callable[[str, Any, Any, list[int], Optional[BaseIndent]], None] = std_log_function,
                 indent: BaseIndent = STD_NUMBERED_INDENT):
        self.log_function = log_function
        self.prefix = prefix
        self.indent_type = indent
        self.prev_loggers: list[tuple[Logger, list[int]]] = []

    @property
    def nlist(self):
        return nlist_contextvar.get()

    def indent(self):
        self.nlist.append(0)

    def deindent(self):
        nlist_contextvar.set(self.nlist[:-1])

    def log(self, message, key: Callable[[Any], str] = lambda x: x, dont_advance: bool = False, prefix: str = None):

        str_message = key(message)

        if str_message.startswith(":"):
            self.deindent()

        colon_stripped = strip_colons(str_message)
        if colon_stripped and colon_stripped != " ":
            if not dont_advance:
                self.nlist[-1] += 1
            self.log_function(colon_stripped, message, self.prefix if prefix is None else prefix, self.nlist, self.indent_type)

        if str_message.endswith(":"):
            self.indent()

        return self

    def __enter__(self):
        self.prev_loggers.append((logger_contextvar.get(), nlist_contextvar.get()[:]))

        logger_contextvar.set(self)
        self.indent()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deindent()

        *self.prev_loggers, (logger, nlist) = self.prev_loggers

        logger_contextvar.set(logger)
        nlist_contextvar.set(nlist)


global_logger = Logger("GLOBAL")
logger_contextvar: ContextVar[Logger] = ContextVar("__context_logger_logger__", default=global_logger)

nlist_contextvar: ContextVar[list[int]] = ContextVar("__context_logger_nlist__", default=[0])

get_current_logger: Callable[[], Logger] = logger_contextvar.get
