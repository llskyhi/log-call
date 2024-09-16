# encoding=utf-8
import logging
import logging.config
import pathlib

from log_call import log_call
from example_package.bad_uses import *
from example_package.functions import *
from example_package.methods import *

LOGGER = logging.getLogger()

@log_call
def run_function_examples() -> None:
    LOGGER.info(f"{decorated_function() = !r}")
    # LOGGER.info(f"{call_decorated_function() = !r}")
    # LOGGER.info(f"{decorated_lambda() = !r}")
    # LOGGER.info(f"{decorated_recursive_fibonacci(5) = !r}")
    try:
        decorated_recursive_raises_runtime_error(5)
    except RuntimeError as error:
        LOGGER.info(f"Caught error: {error!r}.", exc_info=True)

@log_call
def run_method_examples() -> None:
    LOGGER.info(f"{Fooo.decorated_class_method() = !r}")
    LOGGER.info(f"{Fooo().decorated_class_method() = !r}")
    LOGGER.info(f"{Fooo.decorated_static_method() = !r}")
    LOGGER.info(f"{Fooo().decorated_static_method() = !r}")
    LOGGER.info(f"{Fooo().decorated_instance_method() = !r}")
    LOGGER.info(f"{log_call(Fooo.non_decorated_class_method)() = !r}")
    LOGGER.info(f"{log_call(Fooo().non_decorated_class_method)() = !r}")
    LOGGER.info(f"{log_call(Fooo.non_decorated_static_method)() = !r}")
    LOGGER.info(f"{log_call(Fooo().non_decorated_static_method)() = !r}")
    LOGGER.info(f"{log_call(Fooo().non_decorated_instance_method)() = !r}")
    LOGGER.info(f"{Fooo().call_decorated_instance_method() = !r}")
    Foooo(123, baz=456)

@log_call
def run_bad_uses() -> None:
    decorated_hash_password(password="p@ssword")

    # NotLikeThis.static_method() may looks fine, but ..
    try:
        LOGGER.info(f"{NotLikeThis().static_method() = !r}")
    except TypeError as error:
        # TypeError: NotLikeThis.static_method() takes 0 positional arguments but 1 was given
        LOGGER.exception(error)

    LOGGER.info(f"{NotLikeThis().property_ = !r}") # the property getter will not even be called

    # examples below will fall into recursion for a while
    # LOGGER.info(f"{DunderRecursive().decorated_instance_method() = !r}") # boom!
    # LOGGER.info(f"{str(DunderRecursive()) = !r}") # boom!
    # LOGGER.info(f"{repr(DunderRecursive()) = !r}") # boom!

if __name__ == "__main__":
    logging.config.fileConfig(
        pathlib.Path(__file__).with_name("log-config.conf"),
        disable_existing_loggers=False,
    )

    run_function_examples()
    run_method_examples()
    # run_bad_uses()
