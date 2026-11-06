"""Runs the 24 targeted test cases listed in Chapter 10 (Table 10.2).

Usage (from the verbatim folder):   python tests/check_cases.py

Each case is a small Verbatim program.  A case passes when
  - it should run:  the output lines are exactly the expected lines, or
  - it should fail: it stops with an error whose message contains the expected text
                    (and, for T24, prints nothing before the error).
This file is not part of the 33 unittest tests; it only reproduces Table 10.2.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from errors import VerbatimError  # noqa: E402
from verbatim import run_source   # noqa: E402

# (id, description, program, expected output lines or None, expected error text or None)
CASES = [
    ("T01", "Operator precedence", 'print(str(2 + 3 * 4))\n', ["14"], None),
    ("T02", "Parentheses", 'print(str((2 + 3) * 4))\n', ["20"], None),
    ("T03", "Integer division rounds down", 'print(str(7 / 2))\nprint(str((0 - 7) / 2))\n', ["3", "-4"], None),
    ("T04", "Modulo", 'print(str(17 % 5))\n', ["2"], None),
    ("T05", "String concatenation", 'print("Ver" + "batim")\n', ["Verbatim"], None),
    ("T06", "Boolean logic", 'if 3 > 2 and not (1 == 2) {\n    print("yes")\n}\n', ["yes"], None),
    ("T07", "Array indexing", 'let a: [int] = [4, 8, 15]\nprint(str(a[2]))\n', ["15"], None),
    ("T08", "len of an array", 'let a: [int] = [4, 8, 15]\nprint(str(len(a)))\n', ["3"], None),
    ("T09", "Empty array literal", 'let a: [int] = []\nprint(str(len(a)))\n', ["0"], None),
    ("T10", "While loop",
     'let i: int = 1\nlet s: int = 0\nwhile i <= 4 {\n    s = s + i\n    i = i + 1\n}\nprint(str(s))\n', ["10"], None),
    ("T11", "Short-circuit and",
     'let a: [int] = [1]\nif len(a) > 5 and a[5] == 0 {\n    print("no")\n} else {\n    print("ok")\n}\n',
     ["ok"], None),
    ("T12", "Static scope",
     "let x: int = 1\nfunc show() {\n    print(str(x))\n}\nif true {\n    let x: int = 2\n    show()\n}\n",
     ["1"], None),
    ("T13", "Pass-by-value",
     "func change(a: [int]) {\n    a[0] = 99\n}\nlet n: [int] = [1, 2]\nchange(n)\nprint(str(n[0]))\n", ["1"], None),
    ("T14", "Recursion (Fibonacci)",
     "func fib(n: int) -> int {\n    if n < 2 {\n        return n\n    }\n"
     "    return fib(n - 1) + fib(n - 2)\n}\nprint(str(fib(15)))\n", ["610"], None),
    ("T15", "Type error: string + int", 'print("5" + 3)\n', None, "cannot add string and int"),
    ("T16", "Type error: non-bool condition", "let n: int = 3\nif n {\n}\n", None, "must be a bool"),
    ("T17", "Type error: undeclared name", "y = 1\n", None, "'y' is not declared"),
    ("T18", "Syntax error: chained comparison", "let b: bool = 1 < 2 < 3\n", None, "cannot be chained"),
    ("T19", "Lexical error: open string", 'let s: string = "oops\n', None, "missing its closing quote"),
    ("T20", "Runtime error: index range", "let a: [int] = [1]\nprint(str(a[3]))\n", None, "out of range"),
    ("T21", "Runtime error: division by zero", "print(str(1 / 0))\n", None, "division by zero"),
    ("T22", "Runtime error: bad to_int", 'print(str(to_int("abc")))\n', None, "cannot convert"),
    ("T23", "Runtime error: endless recursion",
     "func f(n: int) -> int {\n    return f(n + 1)\n}\nprint(str(f(1)))\n", None, "too many nested function calls"),
    ("T24", "No output before a type error", 'print("first")\nprint("5" + 3)\n', None, "cannot add"),
]


def run(src):
    out = []
    try:
        run_source(src, out.append)
        return out, None
    except VerbatimError as e:
        return out, str(e)


def main():
    passed = 0
    for cid, desc, src, want_out, want_err in CASES:
        out, err = run(src)
        if want_out is not None:
            ok = err is None and out == want_out
        else:
            ok = err is not None and want_err in err and out == []
        passed += ok
        print(f"{cid}  {'PASS' if ok else 'FAIL'}  {desc}")
        if not ok:
            print(f"      expected: {want_out if want_out is not None else want_err!r}")
            print(f"      actual:   output={out!r} error={err!r}")
    print(f"\n{passed} of {len(CASES)} cases passed")
    sys.exit(0 if passed == len(CASES) else 1)


if __name__ == "__main__":
    main()
