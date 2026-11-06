"""Runs every program in the examples folder and checks the result.

Usage (from the verbatim folder):   python tests/check_examples.py

A program that should run must print exactly the expected lines.
A program that should be rejected must stop with the expected kind of error,
on the expected line, with the expected text in the message, and print nothing first.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
EXAMPLES = os.path.join(ROOT, "examples")
sys.path.insert(0, ROOT)

from errors import VerbatimError  # noqa: E402
from verbatim import run_source   # noqa: E402

FIZZ = ["FizzBuzz" if i % 15 == 0 else "Fizz" if i % 3 == 0 else "Buzz" if i % 5 == 0 else str(i)
        for i in range(1, 16)]

# name -> ("run", [expected output lines])  or  ("error", kind, line, text in message)
EXPECTED = {
    "hello": ("run", ["Hello, World!"]),
    "factorial": ("run", ["120"]),
    "fizzbuzz": ("run", FIZZ),
    "arrays": ("run", ["Total: 27"]),
    "sort": ("run", ["1", "2", "5", "7", "9", "original first: 5"]),
    "signature": ("run", ["Total: 8"]),
    "scope": ("run", ["2", "1", "1"]),
    "pass_by_value": ("run", ["1"]),
    "sum_loop": ("run", ["6"]),
    "error_demo": ("error", "Type error", 3, "cannot add string and int"),
    "rejected": ("error", "Type error", 3, "cannot add string and int"),
    "condition_error": ("error", "Type error", 2, "must be a bool"),
    "missing_return": ("error", "Type error", 1, "might finish without returning"),
    "syntax_error": ("error", "Syntax error", 1, "cannot be chained"),
    "lex_error_string": ("error", "Lexical error", 1, "missing its closing quote"),
    "lex_error_char": ("error", "Lexical error", 1, "unexpected character '@'"),
    "lex_error_bang": ("error", "Lexical error", 1, "unexpected character '!'"),
    "runtime_error": ("error", "Runtime error", 2, "out of range"),
}


def run(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    out = []
    try:
        run_source(src, out.append)
        return out, None
    except VerbatimError as e:
        return out, e


def main():
    passed = 0
    for name, want in EXPECTED.items():
        path = os.path.join(EXAMPLES, name + ".vbt")
        if not os.path.exists(path):
            print(f"MISSING  {name}.vbt  (not found in the examples folder)")
            continue
        out, err = run(path)
        if want[0] == "run":
            ok = err is None and out == want[1]
            detail = f"expected {want[1]!r}, got output={out!r} error={err!s}"
        else:
            _, kind, line, text = want
            ok = (err is not None and err.kind == kind and err.line == line
                  and text in err.message and out == [])
            detail = (f"expected {kind} on line {line} containing {text!r}; "
                      f"got output={out!r} error={err!s}" if err is not None
                      else f"expected {kind}, but the program ran with output={out!r}")
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}     {name}.vbt")
        if not ok:
            print("         " + re.sub(r"\s+", " ", detail))
    print(f"\n{passed} of {len(EXPECTED)} example programs behaved as expected")
    sys.exit(0 if passed == len(EXPECTED) else 1)


if __name__ == "__main__":
    main()
