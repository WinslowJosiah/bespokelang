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

### v1.0.1 (2025-01-15)

- Fixed behavior of `DO ROT` and `DO ROTINVERSE` with negative numbers

### v1.0.0 (2025-01-13)

Initial release.
