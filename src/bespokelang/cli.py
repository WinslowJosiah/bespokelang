__all__ = ["cli"]

from argparse import ArgumentParser
import sys

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

    # If where aren't any arguments to parse
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
    with (
        open(args.program, "r") as file,
        BespokeInterpreter(file.read()) as bespoke,
    ):
        bespoke.interpret()
