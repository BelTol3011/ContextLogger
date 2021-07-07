import inspect
from typing import Callable, Any, Union, Awaitable
from contextvars import ContextVar


def std_log_function(message: str, prefix: str, indentation: int):
    print((f"[{prefix}] " if prefix else "") + (" " * indentation) + message)


def log_decorator(message_or_func: Union[Any, Union[Callable[[tuple, dict], Any]]]):
    """
    Returns a decorator that wraps a logger around a function.

    :type message_or_func: Can be ether a message (Any) or a function to which the arguments are passed and which
        returns amessage.
    """

    def decorator(decorated_func):
        if inspect.iscoroutinefunction(decorated_func):
            async def wrapper(*args, **kwargs):
                if isinstance(message_or_func, Callable):
                    func_args = inspect.getfullargspec(decorated_func)[0]
                    assigned_args = {key: value for key, value in zip(func_args, args)} | kwargs

                    message_ = message_or_func(assigned_args)
                else:
                    message_ = message_or_func
                with log(message_):
                    return await decorated_func(*args, **kwargs)
        else:
            def wrapper(*args, **kwargs):
                if isinstance(message_or_func, Callable):
                    func_args = inspect.getfullargspec(decorated_func)[0]
                    assigned_args = {key: value for key, value in zip(func_args, args)} | kwargs

                    message_ = message_or_func(assigned_args)
                else:
                    message_ = message_or_func
                with log(message_):
                    return decorated_func(*args, **kwargs)

        return wrapper

    return decorator


def log(message):
    return logger_contextvar.get().log(message)


class Logger:
    def __init__(self, prefix, log_function: Callable[[Any, Any, int], None] = std_log_function, *,
                 indentation: int = 0):
        self.log_function = log_function
        self.prefix = prefix
        self._indentation = indentation

    def log(self, message):
        self.log_function(message, self.prefix, self._indentation)

        return self

    def __enter__(self):
        if logger_contextvar.get() == self:
            self._indentation += 1
        else:
            logger_contextvar.set(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._indentation -= 1


logger_contextvar: ContextVar[Logger] = ContextVar("__context_logger_var__", default=Logger("GLOBAL"))
