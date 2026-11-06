"""Verbatim: run a program.   Usage:  python verbatim.py examples/factorial.vbt"""
import sys

from errors import VerbatimError
from interpreter import Interpreter
from parser import parse
from typechecker import check

sys.setrecursionlimit(6000)


def run_source(source, out=print):
    program = parse(source)          # text -> tokens -> tree   (syntax errors)
    check(program)                   # static type check        (type errors)
    Interpreter(out).run(program)    # execute                  (runtime errors)


def main():
    if len(sys.argv) != 2:
        print("Usage: python verbatim.py <file.vbt>")
        sys.exit(2)
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"Cannot open file: {e}")
        sys.exit(2)
    try:
        run_source(source)
    except VerbatimError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
