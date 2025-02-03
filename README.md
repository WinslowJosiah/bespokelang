# bespokelang

Run programs written in the Bespoke esolang.

## Installation

`bespokelang` is installable from PyPI:

```bash
pip install --upgrade bespokelang
```

## What is Bespoke?

Bespoke is an [esoteric programming language](https://esolangs.org/wiki/Esoteric_programming_language)
I created in January 2025, based loosely on my earlier language [Poetic](https://esolangs.org/wiki/Poetic_(esolang)).
The goal was to use the same encoding process as Poetic, but change the
underlying structure of the language into something tolerable to write programs
with.

I'm very happy with what I came up with; it's been a delight to write the
included example programs, and they were _much_ easier to write than most of the
Poetic programs I've ever written.

## Features of Bespoke

- Imperative paradigm
- Arbitrary precision integers
- A stack, for temporary number storage
- A "heap", for permanent number storage
- IF statements, looping, and _functions_!
- Comments (which _weren't_ in Poetic, technically)
- Flexible syntax based on word lengths (e.g. `PUSH SEVENTH` = `tiny pythons`)

## Documentation

Documentation can be found [on the GitHub wiki](https://github.com/WinslowJosiah/bespokelang/wiki/Documentation)
for this project. A tutorial on how to use each feature of the language is also
[on the wiki](https://github.com/WinslowJosiah/bespokelang/wiki/Tutorial).

## Changelog

### v1.2.3 (2025-02-03)

- Fixed behavior of `DO ROTINVERSE` with an argument outside the range from 1 to
the stack size

### v1.2.2 (2025-02-03)

- Fixed behavior of `DO TURNOVERN` with an argument of 0

### v1.2.1 (2025-02-02)

- Fixed behavior of `CONTROL B` and `CONTROL RETURN` when not nested
- The output buffer is now flushed every 0.5 seconds

### v1.2.0 (2025-01-31)

- Added `--debug` option to CLI, for displaying stack/heap contents after
program execution
- Added `BespokeInterpreter.from_file()` method
- Fixed bug where `Specifier was expected, but none found` would not show the
command which expected a specifier
- Fixed behavior of `STACKTOP POW` with a second argument of 0
- `BespokeInterpreter` no longer writes error message to STDERR when used as a
context manager
- Many properties of `BespokeInterpreter` objects are now private, or have
getters/setters
- CLI now handles file-opening errors

### v1.1.0 (2025-01-17)

- Changed `CONTROL RESETLOOP` to `CONTROL OTHERWISE`

### v1.0.2 (2025-01-15)

- Fixed error on empty program
- Fixed behavior of `CONTINUED` numbers

### v1.0.1 (2025-01-15)

- Fixed behavior of `DO ROT` and `DO ROTINVERSE` with negative numbers

### v1.0.0 (2025-01-13)

Initial release.
