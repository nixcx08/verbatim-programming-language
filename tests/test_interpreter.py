import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from errors import VerbatimError
from verbatim import run_source

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def run(src):
    out = []
    run_source(src, out.append)
    return out


def run_file(name):
    with open(os.path.join(EXAMPLES, name), encoding="utf-8") as f:
        return run(f.read())


class ProgramTests(unittest.TestCase):
    def test_hello(self):
        self.assertEqual(run_file("hello.vbt"), ["Hello, World!"])

    def test_factorial(self):
        self.assertEqual(run_file("factorial.vbt"), ["120"])

    def test_fizzbuzz(self):
        out = run_file("fizzbuzz.vbt")
        self.assertEqual(len(out), 15)
        self.assertEqual(out[:5], ["1", "2", "Fizz", "4", "Buzz"])
        self.assertEqual(out[-1], "FizzBuzz")

    def test_arrays(self):
        self.assertEqual(run_file("arrays.vbt"), ["Total: 27"])

    def test_signature(self):
        self.assertEqual(run_file("signature.vbt"), ["Total: 8"])

    def test_static_scope(self):
        src = ('let x: int = 1\nfunc show() {\n    print(str(x))\n}\n'
               'if true {\n    let x: int = 2\n}\nshow()\n')
        self.assertEqual(run(src), ["1"])

    def test_block_scope_ends(self):
        with self.assertRaises(VerbatimError):
            run('if true {\n    let y: int = 2\n}\nprint(str(y))\n')

    def test_pass_by_value(self):
        src = ('func change(a: [int]) {\n    a[0] = 99\n}\n'
               'let nums: [int] = [1, 2]\nchange(nums)\nprint(str(nums[0]))\n')
        self.assertEqual(run(src), ["1"])

    def test_array_assignment_and_len(self):
        src = 'let a: [int] = [1, 2, 3]\na[1] = 20\nprint(str(a[1] + len(a)))\n'
        self.assertEqual(run(src), ["23"])

    def test_precedence_and_division(self):
        self.assertEqual(run('print(str(2 + 3 * 4))\nprint(str(7 / 2))\nprint(str(7 % 3))\n'),
                         ["14", "3", "1"])

    def test_short_circuit(self):
        src = 'let a: [int] = [1]\nif len(a) > 5 and a[5] == 0 {\n    print("no")\n} else {\n    print("ok")\n}\n'
        self.assertEqual(run(src), ["ok"])

    def test_empty_array_literal(self):
        self.assertEqual(run('let a: [int] = []\nprint(str(len(a)))\n'), ["0"])

    def test_recursion(self):
        src = 'func fib(n: int) -> int {\n    if n < 2 {\n        return n\n    }\n    return fib(n - 1) + fib(n - 2)\n}\nprint(str(fib(15)))\n'
        self.assertEqual(run(src), ["610"])


class TypeErrorTests(unittest.TestCase):
    def assert_error(self, src, kind):
        with self.assertRaises(VerbatimError) as cm:
            run(src)
        self.assertEqual(cm.exception.kind, kind, src)

    def test_type_errors(self):
        bad = [
            'print("5" + 3)\n',
            'let x: int = "a"\n',
            'if 1 {\n}\n',
            'let x: int = 1\nx = "a"\n',
            'print(5)\n',
            'y = 1\n',
            'func f() -> int {\n}\n',
            'return 1\n',
            'let a: [int] = [1, "a"]\n',
            'print(str(len(5)))\n',
            'let x: int = 1\nlet x: int = 2\n',
            'let b: bool = 1 == "1"\n',
            'let x: int = print("a")\n',
            'func f(a: int) {\n}\nf("x")\n',
            'let n: int = 3\nif n {\n}\n',
        ]
        for src in bad:
            self.assert_error(src, "Type error")

    def test_nothing_runs_before_type_error(self):
        out = []
        with self.assertRaises(VerbatimError):
            run_source('print("first")\nprint("5" + 3)\n', out.append)
        self.assertEqual(out, [])             # static checking: no output at all

    def test_error_demo_file(self):
        with self.assertRaises(VerbatimError) as cm:
            run_file("error_demo.vbt")
        self.assertEqual(cm.exception.kind, "Type error")
        self.assertIn("cannot add string and int", cm.exception.message)

    def test_runtime_errors(self):
        for src in ['print(str(1 / 0))\n',
                    'let a: [int] = [1]\nprint(str(a[3]))\n',
                    'print(str(to_int("abc")))\n',
                    'func f(n: int) -> int {\n    return f(n + 1)\n}\nprint(str(f(1)))\n']:
            self.assert_error(src, "Runtime error")


if __name__ == "__main__":
    unittest.main()
