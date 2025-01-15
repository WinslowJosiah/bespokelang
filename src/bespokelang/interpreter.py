__all__ = [
    "Block", "Token",

    "BespokeInterpreter",
]

from collections import defaultdict, deque
from collections.abc import Callable, Iterable, Iterator, Sequence
import sys
from types import TracebackType
from typing import NamedTuple, SupportsIndex, TextIO, TypeAlias
import unicodedata

from bespokelang.exceptions import *


class Token(NamedTuple):
    category: str
    command: str
    args: tuple[str, ...] = ()
Block: TypeAlias = "Sequence[Token | Block]"


class PeekableStream:
    """Wrapper around a stream to make it peekable."""

    def __init__(self, stream: TextIO):
        self.stream = stream
        self.buffer: deque[str] = deque()

    def read(self, size: int | None = -1) -> str:
        """
        Read and return at most `size` characters from the stream as a
        single `str`. If `size` is negative or `None`, the stream is
        read until EOF.

        Parameters
        ----------
        size : int or None, default -1
            Number of characters to read from the stream. If `size` is
            negative or `None`, the stream is read until EOF.

        Returns
        -------
        str
            Characters read from the stream.
        """
        if size is None or size < 0:
            chars = self.stream.read(size or -1)
            self.buffer.extend(chars)
            result = "".join(self.buffer)
            self.buffer.clear()
        else:
            if len(self.buffer) < size:
                chars = self.stream.read(size - len(self.buffer))
                self.buffer.extend(chars)
            result = "".join(
                self.buffer.popleft()
                for _ in range(size)
                if self.buffer
            )
        return result

    def peek(self, size: int):
        """
        Return at most `size` characters from the stream as a single
        `str` without consuming them.

        Parameters
        ----------
        size : int
            Number of characters to peek at from the stream.

        Returns
        -------
        str
            Characters peeked at from the stream.
        """
        if len(self.buffer) < size:
            chars = self.stream.read(size - len(self.buffer))
            self.buffer.extend(chars)
        return "".join(c for c, _ in zip(self.buffer, range(size)))


def int_nth_root(x: int, n: int):
    """
    Return the integer `n`th root of `x`.

    Parameters
    ----------
    x : int
        Integer to get the `n`th root of.
    n : int
        Number to root by.

    Returns
    -------
    int
        Integer `n`th root of `x`.
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if not x:
        return 0
    if x <= 0:
        raise ValueError("x must be nonnegative")

    q, r = x + 1, x
    while q > r:
        q, r = r, ((n-1) * r + x // pow(r, n - 1)) // n
    return q


def split_by_function(
        st: str,
        sep: Callable[[str], bool],
        maxsplit: SupportsIndex = -1,
) -> Iterator[str]:
    """
    Return an iterator over substrings in the string, using `sep` as the
    function by which the separator characters are defined.

    Splitting starts at the front of the string and works to the end.

    If `sep` is `str.isspace`, this function splits equivalently to the
    builtin function `str.split`.

    Parameters
    ----------
    st : str
        The string to split.
    sep : callable
        A function that takes a single character as an argument. The
        `sep` function returns `True` if the character should be used as
        a separator, and `False` otherwise.
    maxsplit : int, default -1
        Maximum number of splits. A negative number means no limit.

    Yields
    -------
    str
        The next substring in the string.
    """
    maxcount = maxsplit.__index__()
    # If maxsplit is negative
    if maxcount < 0:
        # Set to maximum count of substrings
        maxcount = (len(st) - 1) // 2 + 1

    i = 0
    for _ in range(maxcount):
        # Skip separator characters
        while i < len(st):
            if not sep(st[i]):
                break
            i += 1
        # Stop splitting if end of string was reached
        else:
            return

        # This substring should start here
        j = i
        i += 1
        # Scan forward to the next separator
        while i < len(st) and not sep(st[i]):
            i += 1
        # Collect the substring
        yield st[j:i]

    # If end of string was reached, return
    if i >= len(st):
        return
    # Otherwise, maxcount must have been reached

    # Skip remaining separators
    while i < len(st) and sep(st[i]):
        i += 1
    # Collect until end of string
    if i < len(st):
        yield st[i:]


def convert_to_digits(text: str) -> str:
    """
    Convert `text` to a string containing the digits of its word
    lengths.

    "Words" are considered to be sequences of letters and/or
    apostrophes; any other characters are treated as word delimiters.
    Each word of `n` letters represents:

    - The digit `n` if `n` < 10
    - The digit 0 if `n` = 10
    - Multiple consecutive digits if `n` > 10 (for example, a 12-letter
    word represents the digits 1, 2)

    Parameters
    ----------
    text : str
        Text to convert to digit string.

    Returns
    -------
    str
        String of digits.

    Examples
    --------
    >>> convert_to_digits("I marred a groaning silhouette")
    "16180"
    >>> convert_to_digits("Fun-filled? It isn't all fun & games!")
    "3624335"
    >>> convert_to_digits("Feelings of faith, and eyes of rationalism")
    "82534211"
    """
    # Normalize to NFKC form (compatibility composition)
    normalized_text = unicodedata.normalize("NFKC", text)
    words = split_by_function(
        normalized_text,
        lambda c: not (c.isalpha() or c in "'\u2019"),
    )
    # Count letters in words
    word_lengths = (
        sum(c.isalpha() for c in word)
        for word in words
    )
    return "".join(
        # Replace 10-letter words with 0
        str(0 if word_length == 10 else word_length)
        for word_length in word_lengths
        if word_length
    )


class BespokeInterpreter:
    def __init__(self, program: str):
        self.program = program

    def __enter__(self):
        # HACK We temporarily disable the limit for integer string
        # conversion, so large numbers can be outputted in full.
        self._int_max_str_digits = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(0)

        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_traceback: TracebackType | None,
    ):
        # Restore integer string conversion limit
        sys.set_int_max_str_digits(self._int_max_str_digits)

        if isinstance(exc_value, BespokeException):
            sys.stderr.write(str(exc_value))
            return True

        return False

    def tokenize(self, digits: str) -> list[Token]:
        """Convert a series of digits into a list of Bespoke tokens."""
        tokens: list[Token] = []
        i = 0

        def parse_sized_number() -> str:
            # Get size of number
            nonlocal i
            if i + 1 > len(digits):
                raise ImproperSizedNumber(digits[i:])
            size = int(digits[i]) or 10
            i += 1

            # Get number
            if i + size > len(digits):
                raise ImproperSizedNumber(digits[i - 1:])
            sized_number = digits[i:i + size]
            i += size
            return sized_number

        while i < len(digits):
            digit = digits[i]
            i += 1
            match digit:
                # H / DO / PUSH / INPUT / OUTPUT / CONTROL / STACKTOP
                case "1" | "2" | "4" | "5" | "6" | "7" | "8":
                    if i + 1 > len(digits):
                        raise ExpectedSpecifier(digits[i:])
                    next_digit = digits[i]
                    i += 1

                    # If the command is CONTROL CALL or CONTROL FUNCTION
                    if (digit, next_digit) in (("7", "4"), ("7", "8")):
                        # The function's "name" is a "sized number"
                        token = Token(
                            digit, next_digit, (parse_sized_number(),)
                        )
                    else:
                        token = Token(digit, next_digit)
                # PUT / CONTINUED
                case "3" | "9":
                    token = Token(digit, "", (parse_sized_number(),))
                # COMMENTARY
                case "0":
                    # Comment signature is between next two 0 digits
                    try:
                        j = digits.index("0", i)
                    except ValueError:
                        raise UnterminatedCommentSignature(digits[i - 1:])
                    comment_signature = digits[i - 1:j + 1]
                    i = j + 1

                    # End of comment is next occurrence of comment
                    # signature
                    try:
                        j = digits.index(comment_signature, i)
                    except ValueError:
                        raise UnterminatedCommentBody(digits[i:])
                    comment = digits[i:j]
                    i = j + len(comment_signature)

                    token = Token(digit, comment_signature, (comment,))
                case _:
                    assert False, digit
            tokens.append(token)
        return tokens

    def create_ast(
            self,
            tokens: Iterable[Token],
            block: "Block | None" = None,
            inside_block: bool = False,
    ) -> Block:
        """Create an Bespoke AST from a list of Bespoke tokens."""
        if block is None:
            block = []
        block = list(block)
        token_iter = iter(tokens)

        for token in token_iter:
            match token:
                # CONTROL IF / CONTROL WHILE / CONTROL DOWHILE /
                # CONTROL FUNCTION
                case Token("7", "2" | "5" | "7" | "8", _):
                    block.append(self.create_ast(
                        token_iter,
                        [token],
                        inside_block=True,
                    ))
                # CONTROL END
                case Token("7", "3", _):
                    if not inside_block:
                        raise UnexpectedEndOfBlock
                    block.append(token)
                    break
                # CONTINUED
                case Token("9", _, continuation):
                    if not block or not isinstance(block[-1], Token):
                        raise UnexpectedContinuedNumber

                    last_token = category, command, args = block[-1]
                    # CONTINUED is only valid after a PUT, CONTROL CALL,
                    # or CONTROL FUNCTION command
                    match last_token:
                        case Token("3", _, _) | Token("7", "4" | "8", _):
                            raise UnexpectedContinuedNumber
                        case _:
                            pass

                    block[-1] = Token(category, command, args + continuation)
                # COMMENTARY
                case Token("0", _, _):
                    pass
                case _:
                    block.append(token)
        else:
            # Add a CONTROL END at the end if inside a block
            if inside_block:
                block.append(Token("7", "3"))
        return block

    def interpret(self):
        """Interpret this Bespoke program."""
        digits = convert_to_digits(self.program)
        tokens = self.tokenize(digits)
        ast = self.create_ast(tokens)
        if not ast:
            return

        self.heap: defaultdict[int, int] = defaultdict(int)
        self.functions: dict[str, Block] = {}
        self.stack: list[int] = []

        self.input_stream = PeekableStream(sys.stdin)

        self.block_stack: list[tuple[Block, int]] = [(ast, 0)]
        self.returning = self.breaking = self.resetting = False

        while self.block_stack:
            self.block, self.block_pointer = self.block_stack.pop()
            first_token = self.block[0]

            if self.returning:
                match first_token:
                    # function
                    case Token("", _, _):
                        self.returning = False
                        continue
                    case _:
                        continue

            if self.breaking:
                match first_token:
                    # function
                    case Token("", _, _):
                        raise UnexpectedLoopManipulation
                    # CONTROL WHILE / CONTROL DOWHILE
                    case Token("7", "5" | "7", _):
                        self.breaking = False
                        continue
                    case _:
                        continue

            if self.resetting:
                match first_token:
                    # function
                    case Token("", _, _):
                        raise UnexpectedLoopManipulation
                    # CONTROL WHILE / CONTROL DOWHILE
                    case Token("7", "5" | "7", _):
                        self.resetting = False
                        self.block_pointer = len(self.block) - 1
                    case _:
                        continue

            # For each token in the block
            while self.block_pointer < len(self.block):
                token = self.block[self.block_pointer]
                self.block_pointer += 1

                # If the "token" is really a block
                if not isinstance(token, Token):
                    # We should return here when done
                    self.block_stack.append((self.block, self.block_pointer))
                    # The block will start on its first token
                    self.block_stack.append((token, 0))
                    break

                # Handle this token, and stop iterating if necessary
                if self._handle_token(token):
                    break

        # If we are still returning/breaking/resetting once we've gone
        # past the main block, we actually weren't supposed to do so in
        # the first place
        if self.returning:
            raise UnexpectedReturn
        if self.breaking or self.resetting:
            raise UnexpectedLoopManipulation

    def _handle_token(self, token: Token) -> bool:
        match token:
            # H V
            case Token("1", "1" | "3" | "5" | "7" | "9", _):
                if not self.stack:
                    raise StackUnderflow
                key = self.stack.pop()
                self.stack.append(self.heap[key])

            # H SV
            case Token("1", "2" | "4" | "6" | "8" | "0", _):
                if len(self.stack) < 2:
                    raise StackUnderflow
                key = self.stack.pop()
                value = self.stack.pop()
                self.heap[key] = value

            # DO P
            case Token("2", "1", _):
                if not self.stack:
                    raise StackUnderflow
                self.stack.pop()

            # DO PN
            case Token("2", "2", _):
                if not self.stack:
                    raise StackUnderflow
                n = self.stack.pop()
                if not n or abs(n) > len(self.stack):
                    raise InvalidStackArgument(n)
                # A positive n pops the nth item from the top
                if n > 0:
                    self.stack.pop(-n)
                # A negative n pops the nth item from the bottom
                else:
                    self.stack.pop(-n - 1)

            # DO ROT
            case Token("2", "3", _):
                if not self.stack:
                    raise StackUnderflow
                n = self.stack.pop()
                if not n or abs(n) > len(self.stack):
                    raise InvalidStackArgument(n)
                # A positive n brings items from top to bottom
                if n > 0:
                    self.stack[-n:] = [self.stack[-1]] + self.stack[-n:-1]
                # A negative n brings items from bottom to top
                else:
                    self.stack[n:] = self.stack[n + 1:] + [self.stack[n]]

            # DO COPY
            case Token("2", "4", _):
                if not self.stack:
                    raise StackUnderflow
                self.stack.append(self.stack[-1])

            # DO COPYN
            case Token("2", "5", _):
                if not self.stack:
                    raise StackUnderflow
                n = self.stack.pop()
                if not n or abs(n) > len(self.stack):
                    raise InvalidStackArgument(n)
                # A positive n copies the nth item from the top
                if n > 0:
                    self.stack.append(self.stack[-n])
                # A negative n copies the nth item from the bottom
                else:
                    self.stack.append(self.stack[-n - 1])

            # DO SWITCH
            case Token("2", "6", _):
                if len(self.stack) < 2:
                    raise StackUnderflow
                self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

            # DO SWITCHN
            case Token("2", "7", _):
                if not self.stack:
                    raise StackUnderflow
                n = self.stack.pop()
                if not n or abs(n) > len(self.stack):
                    raise InvalidStackArgument(n)
                # A positive n swaps with the nth item from the top
                if n > 0:
                    self.stack[-1], self.stack[-n] = (
                        self.stack[-n], self.stack[-1]
                    )
                # A negative n swaps with the nth item from the bottom
                else:
                    self.stack[-1], self.stack[-n - 1] = (
                        self.stack[-n - 1], self.stack[-1]
                    )

            # DO TURNOVER
            case Token("2", "8", _):
                self.stack.reverse()

            # DO TURNOVERN
            case Token("2", "9", _):
                if not self.stack:
                    raise StackUnderflow
                n = self.stack.pop()
                if abs(n) > len(self.stack):
                    raise InvalidStackArgument(n)
                # A positive n reverses the top n items
                if n > 0:
                    self.stack[-n:] = self.stack[:-n - 1:-1]
                # A negative n reverses the bottom n items
                else:
                    self.stack[:-n] = self.stack[-n - 1::-1]

            # DO ROTINVERSE
            case Token("2", "0", _):
                if not self.stack:
                    raise StackUnderflow
                n = self.stack.pop()
                # A positive n brings items from bottom to top
                if n > 0:
                    self.stack[-n:] = self.stack[-n + 1:] + [self.stack[-n]]
                # A negative n brings items from top to bottom
                elif n < 0:
                    self.stack[n:] = [self.stack[-1]] + self.stack[n:-1]

            # PUT
            case Token("3", _, args):
                self.stack.append(int("".join(args)))

            # PUSH
            case Token("4", arg, _):
                self.stack.append(int(arg))

            # INPUT N
            case Token("5", "1" | "3" | "5" | "7" | "9", _):
                sys.stdout.flush()
                inp: list[str] = []
                # Skip spaces at start
                while self.input_stream.peek(1).isspace():
                    self.input_stream.read(1)
                # Consume a minus sign, if it's there
                if self.input_stream.peek(1) == "-":
                    inp.extend(self.input_stream.read(1))
                # Consume digits
                while self.input_stream.peek(1) in list("0123456789"):
                    inp.extend(self.input_stream.read(1))

                # Push the resulting int
                try:
                    self.stack.append(int("".join(inp)))
                except ValueError:
                    raise InvalidNumberInput

            # INPUT CH
            case Token("5", "2" | "4" | "6" | "8" | "0", _):
                sys.stdout.flush()
                if (char := self.input_stream.read(1)):
                    self.stack.append(ord(char))
                else:
                    # EOF pushes -1
                    self.stack.append(-1)

            # OUTPUT N
            case Token("6", "1" | "3" | "5" | "7" | "9", _):
                if not self.stack:
                    raise StackUnderflow
                sys.stdout.write(str(self.stack.pop()))

            # OUTPUT CH
            case Token("6", "2" | "4" | "6" | "8" | "0", _):
                if not self.stack:
                    raise StackUnderflow
                sys.stdout.write(chr(self.stack.pop() % 0x110000))

            # CONTROL B
            case Token("7", "1", _):
                self.breaking = True
                return True

            # CONTROL IF
            case Token("7", "2", _):
                if not self.stack:
                    raise StackUnderflow
                if not self.stack.pop():
                    return True

            # CONTROL END
            case Token("7", "3", _):
                match self.block[0]:
                    # CONTROL WHILE
                    case Token("7", "5", _):
                        self.block_stack.append((self.block, 0))
                        # NOTE The condition of a CONTROL WHILE loop is
                        # tested at the start.
                    # CONTROL DOWHILE
                    case Token("7", "7", _):
                        if not self.stack:
                            raise StackUnderflow
                        if self.stack.pop():
                            self.block_stack.append((self.block, 0))
                    case _:
                        pass

            # CONTROL CALL
            case Token("7", "4", args):
                name = "".join(args)
                function_ = self.functions.get(name, None)
                if function_ is None:
                    raise UndefinedFunction
                # We should return here when done
                self.block_stack.append((self.block, self.block_pointer))
                # The function will start on its first token
                self.block_stack.append((function_, 0))
                return True

            # CONTROL WHILE
            case Token("7", "5", _):
                if not self.stack:
                    raise StackUnderflow
                # NOTE This is similar to CONTROL IF; the difference is
                # in how the corresponding CONTROL END is handled.
                if not self.stack.pop():
                    return True

            # CONTROL RETURN
            case Token("7", "6", _):
                self.returning = True
                return True

            # CONTROL DOWHILE
            case Token("7", "7", _):
                # NOTE The condition of a CONTROL DOWHILE loop is tested
                # at the end.
                pass

            # CONTROL FUNCTION
            case Token("7", "8", args):
                name = "".join(args)
                # HACK The first token of the function is changed to a
                # blank token. This way, it's identifiable as a called
                # function on the block stack, and I don't have to
                # implement a complex special case.
                self.functions[name] = [Token("", "")] + list(self.block[1:])
                return True

            # CONTROL RESETLOOP
            case Token("7", "9", _):
                self.resetting = True
                # NOTE In case the current block is the CONTROL WHILE or
                # CONTROL DOWHILE loop to reset, the current block must
                # be pushed back onto the block stack.
                self.block_stack.append((self.block, self.block_pointer))
                return True

            # CONTROL ENDPROGRAM
            case Token("7", "0", _):
                self.block_stack.clear()
                return True

            # STACKTOP F
            case Token("8", "1", _):
                if not self.stack:
                    raise StackUnderflow
                self.stack.append(int(not self.stack.pop()))

            # STACKTOP LT
            case Token("8", "2", _):
                if len(self.stack) < 2:
                    raise StackUnderflow
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a < b))

            # STACKTOP POW
            case Token("8", "3", _):
                if len(self.stack) < 2:
                    raise StackUnderflow
                b = self.stack.pop()
                a = self.stack.pop()
                if a < 0 and b < 0:
                    raise InvalidStackArgument((a, b))

                # A positive b takes the bth power of a
                if b > 0:
                    self.stack.append(a ** b)
                # A negative b takes the bth root of a
                else:
                    self.stack.append(int_nth_root(a, -b))

            # STACKTOP PLUS
            case Token("8", "4", _):
                if len(self.stack) < 2:
                    raise StackUnderflow
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)

            # STACKTOP MINUS
            case Token("8", "5", _):
                if len(self.stack) < 2:
                    raise StackUnderflow
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)

            # STACKTOP MODULO
            case Token("8", "6", _):
                if not self.stack:
                    raise StackUnderflow
                b = self.stack.pop()
                if not b:
                    raise InvalidStackArgument(b)

                if not self.stack:
                    raise StackUnderflow
                a = self.stack.pop()

                self.stack.append(a % b)

            # STACKTOP PLUSONE
            case Token("8", "7", _):
                if not self.stack:
                    raise StackUnderflow
                self.stack[-1] += 1

            # STACKTOP MINUSONE
            case Token("8", "8", _):
                if not self.stack:
                    raise StackUnderflow
                self.stack[-1] -= 1

            # STACKTOP PRODUCTOF
            case Token("8", "9", _):
                if len(self.stack) < 2:
                    raise StackUnderflow
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)

            # STACKTOP QUOTIENTOF
            case Token("8", "0", _):
                if not self.stack:
                    raise StackUnderflow
                b = self.stack.pop()
                if not b:
                    raise InvalidStackArgument(b)

                if not self.stack:
                    raise StackUnderflow
                a = self.stack.pop()

                self.stack.append(a // b)

            # function
            case Token("", _, _):
                pass

            # NOTE I haven't accounted for CONTINUED or COMMENTARY,
            # because they shouldn't be present at this stage.
            case _:
                assert False, token

        return False
