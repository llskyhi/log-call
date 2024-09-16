# encoding=utf-8
import logging

from log_call import log_call

LOGGER = logging.getLogger(__name__)

class Foo:
    @log_call
    def __init__(self):
        LOGGER.info("Within Foo.__init__")

    @classmethod
    def non_decorated_class_method(cls) -> None:
        LOGGER.info("Within Foo.non_decorated_class_method")

    @classmethod
    @log_call
    def decorated_class_method(cls) -> None:
        LOGGER.info("Within Foo.decorated_class_method")

    @staticmethod
    def non_decorated_static_method() -> None:
        LOGGER.info("Within Foo.non_decorated_static_method")

    @staticmethod
    @log_call
    def decorated_static_method() -> None:
        LOGGER.info("Within Foo.decorated_static_method")

    @log_call
    def decorated_instance_method(self) -> None:
        LOGGER.info("Within Foo.decorated_instance_method")

    def non_decorated_instance_method(self) -> None:
        LOGGER.info("Within Foo.non_decorated_instance_method")

    @property
    @log_call
    def decorated_property(self) -> None:
        LOGGER.info("Within Foo.decorated_property getter")

    @decorated_property.setter
    @log_call
    def decorated_property(self, new_value) -> None:
        LOGGER.info(f"Within Foo.decorated_property setter, {new_value = !r}")

    @decorated_property.deleter
    @log_call
    def decorated_property(self) -> None:
        LOGGER.info("Within Foo.decorated_property deleter")

    def call_decorated_instance_method(self) -> None:
        self.decorated_instance_method()

class Fooo(Foo):
    """Empty subclass to see the arguments passed into binding methods."""

class Foooo(Foo):
    @log_call
    def __init__(self, bar: int, /, *, baz: int):
        super().__init__()
        LOGGER.info(f"{bar = }, {baz = }")
        self.bar = bar
        self.baz = baz
