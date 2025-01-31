__all__ = ["cli"]

from argparse import ArgumentParser
import sys

from bespokelang.exceptions import *
from bespokelang.interpreter import *


def cli():
    # Create parser for command line arguments
    parser = ArgumentParser(
        prog="bespoke",
        description="Run programs written in the Bespoke esolang.",
    )
    parser.add_argument(
        "program", help="Bespoke program",
        metavar="PROGRAM",
        type=str,
    )
    parser.add_argument(
        "-d", "--debug",
        help="print the stack and heap contents after the program ends",
        action="store_true",
    )

    # If there aren't any arguments to parse
    if len(sys.argv) < 2:
        # Print help message and exit with error
        parser.print_help()
        sys.exit(1)

    # Overwrite the error handler to also print a help message
    # HACK: This is what's known in the biz as a "monkey-patch". Don't
    # worry if it doesn't make sense to you; it makes sense to argparse,
    # and that's all that matters.
    def custom_error_handler(_self: ArgumentParser):
        def wrapper(message: str):
            sys.stderr.write(f"{_self.prog}: error: {message}\n")
            _self.print_help()
            sys.exit(2)
        return wrapper
    parser.error = custom_error_handler(parser)

    # Actually parse and handle the arguments
    args = parser.parse_args()
    try:
        with open(args.program, "r") as file:
            bespoke = BespokeInterpreter.from_file(file)
            bespoke.interpret()
    except BespokeException as e:
        sys.stderr.write(str(e))
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write("File does not exist.")
        sys.exit(1)
    except OSError as e:
        sys.stderr.write(
            f"Could not open file.\n\t{type(e).__name__}: {e}"
        )
        sys.exit(1)

    if not args.debug:
        return

    # HACK Just in case the stack or heap has any super large values,
    # the limit for integer string conversion is temporarily disabled.
    int_max_str_digits = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(0)

    print(f"\nStack: {bespoke.stack}")
    if not bespoke.heap:
        print("Heap: {}")
    elif len(bespoke.heap) <= 32:
        print("Heap: {")
        for key, value in sorted(bespoke.heap.items()):
            print(f"    {key}: {value},")
        print("}")
    else:
        print(f"Heap: {dict(sorted(bespoke.heap.items()))}")

    sys.set_int_max_str_digits(int_max_str_digits)
