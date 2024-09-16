# Purpose of this repository
Provide a Python *decorator* function `log_call` for Python 3.10+ that logs before and after the decorated callable
using builtin [`logging`](https://docs.python.org/3/library/logging.html) to help developing.

# Examples

Directory [`example/`](./example/) contains some detailed examples which can be run with `python example/example.py`.

The decorator can be used in 3 ways list below.

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
`log_call` may take a set of keyword arguments for some advanced behavior.

Example below defines a function that is potentially called when something bad happens,
each call of it comes with log records with `WARNING` level.
```Python
@log_call(level=logging.WARNING)
def handle_error():
    ...
```

Check the `log_call` signature to see the full set of arguments.

## Callable wrapper
As decorators are just functions, `log_call` can also be used to wrap a callable to call.
```Python
def bar():
    ...

log_call(bar, level=logging.WARNING)()
```

# Logged information

## before invocation
- the decorated callable's name, and the arguments to call it (see also [Warnings](#warning))
- caller

## after invocation
- result returned, if the callable completes successfully
- exception (`Exception`, not `BaseException`) raised, if the callable raised any, and an one-liner call stack
- elapsed time

Besides, the log message pair for a single callable invocation will be prefixed an unique identifier
so that it's easy to identify the log range which the invocation produced.

# Unit test
A simple unit test can be run using `python -m unittest test`.

# Notes

## Warning
Since `log_call` is meant to help development, **it logs ALL arguments** as possible,
which means it may not applicable on functions that takes confidential information like passwords.

Of course it can still be used with caution.

## Limitation

### `__repr__` and `__str__`
Since `log_call` tries to use objects' `repr` (mainly used) and `str` to log arguments,
instances passing into decorated callable having `__repr__` and `__str__` implemented
can result in endless recursive.

### Use with other decorators
`log_call` is not implemented to accept other decorator types like `staticmethod`, `property`, etc.,
instead it should always decorate functions themself.
i.e. *not* this:
```Python
class Foo:
    @log_call # <- bad
    @staticmethod
    def static_foo():
        ...
    @log_call # <- bad
    @classmethod
    def static_foo(cls):
        ...
    @log_call # <- bad
    @property
    def property_foo(self):
        ...
    @log_call # <- bad
    @property_foo.setter
    def property_foo(self, new_value):
        ...
```

but this:
```Python
class Foo:
    @staticmethod
    @log_call # <- good
    def static_foo():
        ...
    @classmethod
    @log_call # <- good
    def static_foo(cls):
        ...
    @property
    @log_call # <- good
    def property_foo(self):
        ...
    @property_foo.setter
    @log_call # <- good
    def property_foo(self, new_value):
        ...
```

### Not supported callable types
- (non-async/async) generator functions
- coroutine functions
