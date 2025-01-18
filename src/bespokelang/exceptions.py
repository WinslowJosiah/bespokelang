__all__ = [
    "BespokeException",

    "TokenizerException", "ExpectedSpecifier", "ImproperSizedNumber",
    "UnterminatedCommentBody", "UnterminatedCommentSignature",

    "ParserException", "UnexpectedContinuedNumber",
    "UnexpectedEndOfBlock", "UnexpectedOtherwise",

    "RuntimeException", "InvalidNumberInput", "InvalidStackArgument",
    "StackUnderflow", "UndefinedFunction", "UnexpectedBreak",
    "UnexpectedReturn",
]

from abc import abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class SupportsStr(Protocol):
    """An ABC with one abstract method __str__."""

    __slots__ = ()

    @abstractmethod
    def __str__(self) -> str:
        pass


class BespokeException(Exception):
    """Generic Bespoke interpreter exception."""
    ___marker = object()
    def __init__(self, value: SupportsStr = ___marker):
        self.value = value

    def __str__(self) -> str:
        msg = self.__class__.__doc__ or ""
        if self.value is not self.___marker:
            msg = msg.rstrip(".")
            value = str(self.value)
            if "'" not in value:
                value = repr(self.value)
            msg += f": {value}"
        return msg


class TokenizerException(BespokeException):
    """Generic exception while tokenizing."""

class ExpectedSpecifier(TokenizerException):
    """Specifier was expected, but none found."""

class ImproperSizedNumber(TokenizerException):
    """Improper "sized number"."""

class UnterminatedCommentBody(TokenizerException):
    """Unterminated comment body."""

class UnterminatedCommentSignature(TokenizerException):
    """Unterminated comment signature."""


class ParserException(BespokeException):
    """Generic exception while parsing."""

class UnexpectedContinuedNumber(ParserException):
    """Unexpected CONTINUED number."""

class UnexpectedEndOfBlock(ParserException):
    """Unexpected end of block."""

class UnexpectedOtherwise(ParserException):
    """Unexpected OTHERWISE command."""


class RuntimeException(BespokeException):
    """Generic exception while running."""

class InvalidNumberInput(RuntimeException):
    """Invalid number input."""

class InvalidStackArgument(RuntimeException):
    """Invalid stack argument."""

class StackUnderflow(RuntimeException):
    """Stack underflow."""

class UndefinedFunction(RuntimeException):
    """Undefined function."""

class UnexpectedBreak(RuntimeException):
    """Unexpected B command."""

class UnexpectedReturn(RuntimeException):
    """Unexpected RETURN command."""
