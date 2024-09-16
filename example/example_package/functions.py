# encoding=utf-8
import logging

from log_call import log_call

LOGGER = logging.getLogger(__name__)

@log_call
def decorated_function():
    LOGGER.info("Within decorated_function")

def call_decorated_function():
    LOGGER.info("Within call_decorated_function")
    decorated_function()

@log_call
def decorated_recursive_fibonacci(n: int) -> int:
    LOGGER.info(f"Within decorated_fibonacci, {n = !r}")
    if n >= 2:
        return decorated_recursive_fibonacci(n - 1) + decorated_recursive_fibonacci(n - 2)
    elif n == 1:
        return 1
    return 0

@log_call
def decorated_recursive_raises_runtime_error(times: int):
    if times - 1 > 0:
        decorated_recursive_raises_runtime_error(times - 1)
    raise RuntimeError

decorated_lambda = log_call(lambda: None)
