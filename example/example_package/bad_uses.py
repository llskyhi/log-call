# encoding=utf-8
import logging

from log_call import log_call

LOGGER = logging.getLogger(__name__)

@log_call
def decorated_hash_password(*, password: str) -> int:
    """BE CAREFUL!"""
    LOGGER.info(f"It looks fine .. BUT IT'S NOT!")
    return hash(password)

class NotLikeThis:
    @log_call
    @staticmethod
    def static_method():
        pass

    # classmethod instances are not callable
    # @log_call
    # @classmethod
    # def class_method(cls):
    #     pass

    @log_call
    @property
    def property_(self):
        pass

class DunderRecursive:
    @log_call
    def __repr__(self) -> str:
        return f"{type(self).__name__}()"
    @log_call
    def __str__(self) -> str:
        return f"{type(self).__name__}<>"
    @log_call
    def decorated_instance_method(self):
        LOGGER.info("Within DunderRecursive.decorated_instance_method")
