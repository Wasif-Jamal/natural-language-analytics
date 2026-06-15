import pytest

from services.exceptions import (
    DBExecutionError,
    EmptyResultError,
    InsightError,
    NLQueryError,
    SQLValidationError,
)

_ALL_EXCEPTIONS = [
    NLQueryError,
    SQLValidationError,
    DBExecutionError,
    EmptyResultError,
    InsightError,
]


@pytest.mark.parametrize("exc_class", _ALL_EXCEPTIONS)
def test_is_subclass_of_exception(exc_class):
    assert issubclass(exc_class, Exception)


@pytest.mark.parametrize("exc_class", _ALL_EXCEPTIONS)
def test_is_raiseable(exc_class):
    with pytest.raises(exc_class):
        raise exc_class("test message")


@pytest.mark.parametrize("exc_class", _ALL_EXCEPTIONS)
def test_message_preserved(exc_class):
    msg = "detailed error info"
    exc = exc_class(msg)
    assert str(exc) == msg
