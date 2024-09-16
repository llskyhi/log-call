# encoding=utf-8
import itertools
import logging
import typing
import unittest

from log_call import log_call

class TestDecorator(unittest.TestCase):
    def test_return(self):
        def returns_as_is(arg):
            return arg
        for object_ in (
            False,
            123,
            "456",
            78.9,
            tuple(),
            object(),
            log_call(returns_as_is),
        ):
            self.assertEqual(log_call(returns_as_is)(object_), object_, "Decorator must return result returned from wrapped callable as-is.")

    def test_exception(self):
        @log_call
        def raises_error(exception_type: typing.Type[Exception], *args) -> typing.NoReturn:
            raise exception_type(*args)
        for exception_type, args in (
            (RuntimeError, ("something wrong happened (bouyomi)")),
            (MemoryError, ("memory error - just saying ;)", )),
        ):
            with self.assertRaises(exception_type, msg="Exception raised from wrapped callable must be re-raise as-is."):
                raises_error(exception_type, *args)

    def test_functions(self):
        ASSERTION_MESSAGE = "Arguments must be passed into wrapped callable as-is."
        A = object()
        B = object()
        C = object()
        @log_call
        def function_(a: object, /, b: object, *, c: object) -> None:
            self.assertIs(a, A, ASSERTION_MESSAGE)
            self.assertIs(b, B, ASSERTION_MESSAGE)
            self.assertIs(c, C, ASSERTION_MESSAGE)
        function_(A, B, c=C)
        function_(A, b=B, c=C)
        with self.assertRaises(TypeError, msg="Callable signature must persist."):
            function_(A, B, C)
        with self.assertRaises(TypeError, msg="Callable signature must persist."):
            function_(a=A, b=B, c=C)

        lambda_function = log_call(lambda a, b, c: (
            self.assertIs(a, A, ASSERTION_MESSAGE),
            self.assertIs(b, B, ASSERTION_MESSAGE),
            self.assertIs(c, C, ASSERTION_MESSAGE),
        ))
        lambda_function(A, B, C)

    def test_methods(self):
        unittest_self = self
        A = object()
        B = object()
        C = object()
        ASSERTION_MESSAGE = "Arguments must be passed into wrapped callable as-is."
        class Foo:
            @staticmethod
            @log_call
            def static_do_nothing(a: object, /, b: object, *, c: object) -> None:
                unittest_self.assertIs(a, A, ASSERTION_MESSAGE)
                unittest_self.assertIs(b, B, ASSERTION_MESSAGE)
                unittest_self.assertIs(c, C, ASSERTION_MESSAGE)
            @classmethod
            @log_call
            def class_do_nothing(cls, a: object, /, b: object, *, c: object) -> None:
                unittest_self.assertTrue(issubclass(cls, Foo))
                unittest_self.assertIs(a, A, ASSERTION_MESSAGE)
                unittest_self.assertIs(b, B, ASSERTION_MESSAGE)
                unittest_self.assertIs(c, C, ASSERTION_MESSAGE)
            @log_call
            def do_nothing(self, a: object, /, b: object, *, c: object) -> None:
                unittest_self.assertIsInstance(self, Foo)
                unittest_self.assertIs(a, A, ASSERTION_MESSAGE)
                unittest_self.assertIs(b, B, ASSERTION_MESSAGE)
                unittest_self.assertIs(c, C, ASSERTION_MESSAGE)
            def non_decorated_do_nothing(self, a: object, /, b: object, *, c: object) -> None:
                unittest_self.assertIsInstance(self, Foo)
                unittest_self.assertIs(a, A, ASSERTION_MESSAGE)
                unittest_self.assertIs(b, B, ASSERTION_MESSAGE)
                unittest_self.assertIs(c, C, ASSERTION_MESSAGE)
        class Fooo(Foo):
            @classmethod
            @log_call
            def class_do_nothing(cls, a: object, /, b: object, *, c: object) -> None:
                super().class_do_nothing(a, b, c=c)
                unittest_self.assertTrue(issubclass(cls, Fooo))
                unittest_self.assertIs(a, A, ASSERTION_MESSAGE)
                unittest_self.assertIs(b, B, ASSERTION_MESSAGE)
                unittest_self.assertIs(c, C, ASSERTION_MESSAGE)
            @log_call
            def do_nothing(self, a: object, /, b: object, *, c: object) -> None:
                super().do_nothing(a, b, c=c)
                unittest_self.assertTrue(isinstance(self, Fooo))
                unittest_self.assertIs(a, A, ASSERTION_MESSAGE)
                unittest_self.assertIs(b, B, ASSERTION_MESSAGE)
                unittest_self.assertIs(c, C, ASSERTION_MESSAGE)
        class Foooo(Fooo):
            pass
        for class_ in (Foo, Fooo, Foooo):
            instance = class_()
            for method in (
                instance.static_do_nothing,
                class_.static_do_nothing,
                instance.class_do_nothing,
                class_.class_do_nothing,
                instance.do_nothing,
                log_call(instance.non_decorated_do_nothing), # test wrapping bound method
            ):
                method(A, B, c=C)
                method(A, b=B, c=C)
                with self.assertRaises(TypeError, msg="Callable signature must persist."):
                    method(A, B, C)
                with self.assertRaises(TypeError, msg="Callable signature must persist."):
                    method(a=A, b=B, c=C)
            with self.assertRaises(TypeError, msg="Callable signature must persist."):
                class_.do_nothing(A, b=B, c=C)

    def test_callable_object(self):
        unittest_self = self
        ASSERTION_MESSAGE = "Arguments must be passed into wrapped callable as-is."
        A = object()
        B = object()
        C = object()
        class Foo:
            @log_call
            def __call__(self, a: object, /, b: object, *, c: object) -> None:
                unittest_self.assertIs(a, A, ASSERTION_MESSAGE)
                unittest_self.assertIs(b, B, ASSERTION_MESSAGE)
                unittest_self.assertIs(c, C, ASSERTION_MESSAGE)
        foo = Foo()
        foo(A, B, c=C)
        foo(A, b=B, c=C)
        with self.assertRaises(TypeError, msg="Callable signature must persist."):
            foo(A, B, C)
        with self.assertRaises(TypeError, msg="Callable signature must persist."):
            foo(a=A, b=B, c=C)

class TestFeature(unittest.TestCase):
    class LogRecordHandler(logging.Handler):
        def __init__(self, level: int | str = 0):
            super().__init__(level)
            self.log_record_counter: int = 0
            self.last_record: logging.LogRecord | None = None
        def emit(self, record: logging.LogRecord):
            self.log_record_counter += 1
            self.last_record = record

    def setUp(self):
        self.logger = logging.getLogger("root") # use root logger, so that all log records propagates to it
        self.log_record_handler = self.LogRecordHandler(logging.DEBUG)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.log_record_handler)
        return super().setUp()

    def tearDown(self):
        self.logger.removeHandler(self.log_record_handler)
        del self.logger
        del self.log_record_handler
        return super().tearDown()

    def test_log_basic_behavior(self):
        expected_log_record_count: int = self.log_record_handler.log_record_counter
        @log_call
        def do_nothing():
            nonlocal expected_log_record_count
            expected_log_record_count += 1
            self.assertEqual(self.log_record_handler.log_record_counter, expected_log_record_count, "log_call must log exactly once before the callable invocation.")
        do_nothing()
        expected_log_record_count += 1
        self.assertEqual(self.log_record_handler.log_record_counter, expected_log_record_count, "log_call must log exactly once before the callable invocation.")

        @log_call
        def recursive(times: int):
            if times - 1 > 0:
                recursive(times - 1)
        RECURSIVE_TIMES = 5
        recursive(RECURSIVE_TIMES)
        expected_log_record_count += RECURSIVE_TIMES * 2
        self.assertEqual(self.log_record_handler.log_record_counter, expected_log_record_count, "log_call must work well on recursion callables.")

    def test_log_record_properties(self):
        THIS_METHOD_NAME = "test_log_record_properties"
        ASSERTION_MESSAGE = "Created log records must present correct caller information."
        @log_call
        def do_nothing():
            log_enter_record = typing.cast(logging.LogRecord, self.log_record_handler.last_record)
            self.assertEqual(log_enter_record.funcName, THIS_METHOD_NAME, ASSERTION_MESSAGE)
            self.assertEqual(log_enter_record.module, __name__, ASSERTION_MESSAGE)
        do_nothing()
        log_exit_record = typing.cast(logging.LogRecord, self.log_record_handler.last_record)
        self.assertEqual(log_exit_record.funcName, THIS_METHOD_NAME, ASSERTION_MESSAGE)
        self.assertEqual(log_exit_record.module, __name__, ASSERTION_MESSAGE)

    def test_parameters(self):
        for logger_name, log_level in itertools.product(
            ("root", "package.module"), # an exception is that "" results in logger name "root"
            (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL),
        ):
            @log_call(logger_name=logger_name, level=log_level)
            def do_nothing():
                log_enter_record = typing.cast(logging.LogRecord, self.log_record_handler.last_record)
                self.assertEqual(log_enter_record.name, logger_name, "Keyword argument 'logger_name' must work.")
                self.assertEqual(log_enter_record.levelno, log_level, "Keyword argument 'level' must work.")
            do_nothing()
            log_exit_record = typing.cast(logging.LogRecord, self.log_record_handler.last_record)
            self.assertEqual(log_exit_record.name, logger_name, "Keyword argument 'logger_name' must work.")
            self.assertEqual(log_exit_record.levelno, log_level, "Keyword argument 'level' must work.")
