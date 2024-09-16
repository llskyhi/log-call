# encoding=utf-8
# Copyright (c) 2024 llskyhi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
__all__ = (
    "log_call",
)
import datetime
import functools
import inspect
import itertools
import logging
import threading
import time
import types
import typing

_P = typing.ParamSpec("_P")
_R = typing.TypeVar("_R")

class _CallableWrapper(typing.Generic[_P, _R]):
    """Class-based decorator implementation for `log_call`."""
    _LOG_STACK_INDENT = "- "
    _NO_BINDING = object()
    class _InvocationContext:
        """Context around a wrapped callable invocation."""
        _thread_local: threading.local = threading.local()
        _serial_number: int = 0
        _serial_number_lock = threading.Lock()
        def __init__(self, *, frame: types.FrameType | None):
            super().__init__()
            self._frame = frame
            self._serial_number = self._get_serial_number()
            self._stack_level: int
            self._start_time: float
            self._elapsed_time: datetime.timedelta
            self._entered: bool = False
            self._exited: bool = False
        def __enter__(self):
            assert not self._entered
            self._entered = True
            self._stack_level = getattr(type(self)._thread_local, "call_stack_level", 0) + 1
            setattr(type(self)._thread_local, "call_stack_level", self._stack_level)
            self._start_time = time.perf_counter()
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            setattr(type(self)._thread_local, "call_stack_level", self._stack_level - 1)
            self._elapsed_time = datetime.timedelta(seconds=time.perf_counter() - self._start_time)
            self._exited = True
            return False

        @property
        def frame(self) -> types.FrameType | None:
            return self._frame
        @property
        def identifier(self) -> str:
            """Identifier of this call stack context, guaranteed to be unique in program life cycle."""
            return str(self._serial_number)
        @property
        def stack_level(self) -> int:
            """The stack level of `log_call` logs, starts from 1."""
            assert self._entered
            return self._stack_level
        @property
        def elapsed_time(self) -> datetime.timedelta:
            """Time elapsed during the context management."""
            assert self._exited
            return self._elapsed_time

        @classmethod
        def _get_serial_number(cls) -> int:
            """Get a serial number over the program's life cycle."""
            with cls._serial_number_lock:
                cls._serial_number += 1
                serial_number = cls._serial_number
            return serial_number

    def __init__(
        self,
        callable_: typing.Callable[_P, _R],
        /,
        *,
        logger_name: str,
        level: int,
    ):
        # assert callable(callable_), f"Positional argument must be a callable object, not {callable_}."
        assert isinstance(logger_name, str), f"Keyword argument 'logger_name' must be a str, not {logger_name!r}."
        assert isinstance(level, int), f"Keyword argument 'level' must be an int, not {level!r}."

        super().__init__()
        functools.update_wrapper(self, callable_, updated=tuple())
        self._callable = callable_
        self._logger_name: str = logger_name
        self._log_level: int = level

    def __get__(self, instance, owner=None):
        # https://docs.python.org/3/howto/descriptor.html#functions-and-methods
        if instance is None:
            return self
        return types.MethodType(self, instance)

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Makes this class callable; invoke the wrapped callable when gets called."""
        context = self._InvocationContext(frame=inspect.currentframe())
        try:
            with context:
                self._log_enter(context, *args, **kwargs)
                returned = self._callable(*args, **kwargs)
        except Exception as exception:
            self._log_exit(context, raised=exception)
            raise
        else:
            self._log_exit(context, returned=returned)
            return returned

    @functools.cached_property
    def _logger(self) -> logging.Logger:
        return logging.getLogger(self._logger_name)

    def _log_enter(self, context: _InvocationContext, /, *args: _P.args, **kwargs: _P.kwargs) -> None:
        """Log about the callable invocation before invoking."""
        log_stack_indent = type(self)._LOG_STACK_INDENT * (context.stack_level - 1)
        context_info = f"{threading.current_thread().name} {context.identifier}"
        invocation_info = self._format_invocation_info(*args, **kwargs)
        self._logger.log(
            level=self._log_level,
            msg=f"{log_stack_indent}/{context_info}/ {invocation_info} started",
            # skips:
            #     logging.Logger.log
            #     (this method)
            #     self.__call__
            stacklevel=3,
        )
    @typing.overload
    def _log_exit(self, context: _InvocationContext, /, *, returned: _R) -> None:
        """Log the result returned from the callable invocation."""
    @typing.overload
    def _log_exit(self, context: _InvocationContext, /, *, raised: Exception) -> None:
        """Log the exception raised within the callable invocation."""
    def _log_exit(self, context: _InvocationContext, /, **kwargs) -> None:
        """Log the execution result of the callable invocation."""
        log_stack_indent = type(self)._LOG_STACK_INDENT * (context.stack_level - 1)
        context_info = f"{threading.current_thread().name} {context.identifier}"
        elapsed_time_info: str = f"{self._format_elapsed_time(context.elapsed_time)} elapsed"
        result_info: str
        if (raised := kwargs.pop("raised", None)) is not None:
            result_info = f"{raised!r} raised, stack: {self._format_one_line_call_stack(context.frame)}"
        else:
            returned: _R = typing.cast(_R, kwargs.pop("returned"))
            result_info = f"{returned!r} returned"
        assert not kwargs
        self._logger.log(
            level=self._log_level,
            msg=rf"{log_stack_indent}\{context_info}\ {elapsed_time_info}, {result_info}",
            # skips:
            #     logging.Logger.log
            #     (this method)
            #     self.__call__
            stacklevel=3,
        )
    def _format_invocation_info(self, *args: _P.args, **kwargs: _P.kwargs) -> str:
        """Callable invocation info to log, i.e. the callable name, arguments, etc."""
        binding: object = self._NO_BINDING
        args_: tuple[object, ...] = args
        kwargs_: dict[str, object] = kwargs
        if inspect.ismethod(self._callable):
            binding = self._callable.__self__
        if binding is not self._NO_BINDING:
            args_ = (binding, *args_)
        return f"{self._format_qualified_name(self._callable)}({self._format_invocation_argument(*args_, **kwargs_)})"
    @classmethod
    def _iterate_frames(cls, frame: types.FrameType | None, /) -> typing.Iterator[types.FrameType]:
        """
        Iterate frames in call stack of which code is *not* in this module,
        from top to bottom (i.e. last called first).
        """
        while frame:
            if not cls._is_code_in_this_module(frame):
                yield frame
            frame = frame.f_back
    @classmethod
    def _is_code_in_this_module(cls, frame: types.FrameType, /) -> bool:
        """Determine if the code in given frame is in this module."""
        module = inspect.getmodule(frame.f_code)
        return (module is not None) and (module.__name__ == __name__)
    @classmethod
    def _format_caller(cls, frame: types.FrameType | None, /) -> str:
        """
        Format a human-readable string for the caller of given frame object,
        with codes in this module skipped.
        """
        try:
            caller_frame = next(cls._iterate_frames(frame))
            return f"{cls._format_qualified_name(caller_frame.f_code)}:{caller_frame.f_lineno}"
        except StopIteration:
            return "(unknown caller)"
    @classmethod
    def _format_one_line_call_stack(cls, frame: types.FrameType | None, /) -> str:
        """
        Format a one-line message presents a simplified call stack.
        This has better readability than a formal, multi-line traceback string because
        - Sometimes exceptions will be caught out of decorated callable,
            you may not that care about it in such cases.
        - If there are nested `log_call` uses, each logging a multi-line stack may be annoying.
        """
        if result := " <- ".join(
            cls._format_caller(frame_)
            for frame_ in cls._iterate_frames(frame)
        ):
            return result
        return "(unknown stack)"
    @classmethod
    def _format_qualified_name(cls, object_: object) -> str:
        """Format the qualified name of given object."""
        name: str = "(unknown)"
        for attr in (
            "__qualname__",
            "co_qualname", # for code objects
            "__name__",
        ):
            if hasattr(object_, attr):
                name = getattr(object_, attr)
                break
        if module := inspect.getmodule(object_):
            return f"{module.__name__}.{name}"
        return name
    @classmethod
    def _format_invocation_argument(cls, *args, **kwargs) -> str:
        """Format a human-readable arguments representation."""
        return ", ".join(itertools.chain(
            (cls._format_object(arg) for arg in args),
            (f"{key}={cls._format_object(value)}" for key, value in kwargs.items()),
        ))
    @classmethod
    def _format_elapsed_time(cls, elapsed_time: datetime.timedelta) -> str:
        if elapsed_time.days > 0:
            return str(elapsed_time) # I don't really care this because it doesn't happen for me
        if (seconds := elapsed_time.seconds) < 60:
            return f"00:{seconds:02}.{elapsed_time.microseconds:06}"
        minutes, seconds = seconds // 60, seconds % 60
        if minutes <= 60:
            return f"{minutes:02}:{seconds:02}"
        hours, minutes = minutes // 60, minutes % 60
        return f"{hours}:{minutes:02}:{seconds:02}"
    @classmethod
    def _format_object(cls, object_: object) -> str:
        """Determine a string to present the given object."""
        # __repr__ and __str__ can raise exceptions due to implementation
        # e.g. when a class is implemented to have them available after specific operations.
        try:
            return repr(object_)
        except Exception:
            pass
        try:
            return str(object_)
        except Exception:
            pass
        return f"({cls._format_qualified_name(type(object_))} instance)"

@typing.overload
def log_call(
    callable_: typing.Callable[_P, _R],
    /,
    *,
    logger_name: str = __name__,
    level: int = logging.DEBUG,
) -> typing.Callable[_P, _R]:
    """
    ## Use as non-parameterized decorator
    ```
    @log_call
    def foo():
        ...
    ```

    ## Use as callable wrapper
    ```
    def bar():
        ...
    log_call(bar, level=logging.INFO)()
    ```
    """
@typing.overload
def log_call(
    *,
    logger_name: str = __name__,
    level: int = logging.DEBUG,
) -> typing.Callable[[typing.Callable[_P, _R]], typing.Callable[_P, _R]]:
    """
    ## Use as parameterized decorator
    ```
    @log_call(logger_name="my.error.name", level=logging.WARNING)
    def handle_error():
        ...
    ```
    """
def log_call(
    callable_: typing.Callable[_P, _R] | None = None,
    /,
    *,
    logger_name: str = __name__,
    level: int = logging.DEBUG,
) -> typing.Callable[_P, _R] | typing.Callable[[typing.Callable[_P, _R]], typing.Callable[_P, _R]]:
    """
    # Usage
    This module provides a decorator `log_call` that writes log using builtin `logging` module
    before and after running the decorated callable.

    ## Logged information
    ### before invocation
    - arguments (WARNING: you may not want to use it on functions taking confidential information!)
    - caller
    ### after invocation
    - result returned, if the callable completes successfully
    - exception raised and an one-line call stack, if the callable raised any
    - elapsed time

    Besides, the log message pair for a single callable invocation will be prefixed an unique identifier
    so that it's easy to identify the log range which the invocation produced.

    # Examples

    The decorator can be used in following 3 ways:

    ## Non-parameterized decorator
    The simplest form, just like how a decorator looks.
    ```Python
    @log_call
    def foo():
        ...
    ```

    Applies on instance method as well:
    ```Python
    class Foo:
        @log_call
        def foo(self):
            ...
    ```

    ## Parameterized decorator
    `log_call` can accept a set of keyword arguments for some advanced configuration.

    Example below defines a function that is potentially called when something bad happens,
    each call of it comes with log records with `WARNING` level.
    ```Python
    @log_call(logger_name="my.error.logger.name", level=logging.WARNING)
    def handle_error():
        ...
    ```

    ## Callable wrapper
    `log_call` can also be used to wrap a callable to call as decorators are just functions.
    ```Python
    def bar():
        ...

    log_call(bar, level=logging.WARNING)()
    ```
    """
    if callable_ is None:
        return functools.partial(log_call, logger_name=logger_name, level=level)
    return _CallableWrapper(callable_, logger_name=logger_name, level=level)
