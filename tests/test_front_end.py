import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ast_nodes import *
from errors import VerbatimError
from lexer import tokenize
from parser import parse

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def types(src):
    return [t.type for t in tokenize(src)]


class LexerTests(unittest.TestCase):
    def test_declaration(self):
        self.assertEqual(types("let x: int = 5"),
                         ["let", "IDENT", ":", "int", "=", "INT", "NEWLINE", "EOF"])

    def test_two_char_symbols(self):
        self.assertEqual(types("a <= b == c -> d")[:7],
                         ["IDENT", "<=", "IDENT", "==", "IDENT", "->", "IDENT"])

    def test_comments_and_blank_lines_make_no_newline(self):
        self.assertEqual(types("# hi\n\nlet x: int = 1  # note\n"),
                         ["let", "IDENT", ":", "int", "=", "INT", "NEWLINE", "EOF"])

    def test_case_sensitive_keywords(self):
        self.assertEqual(types("While")[0], "IDENT")

    def test_string(self):
        tok = tokenize('"hello world"')[0]
        self.assertEqual((tok.type, tok.value), ("STRING", "hello world"))

    def test_errors(self):
        for bad in ['"oops', "a ! b", "3abc", "x @ y"]:
            with self.assertRaises(VerbatimError, msg=bad):
                tokenize(bad)


class ParserTests(unittest.TestCase):
    def expr(self, text):
        return parse(f"let x: int = {text}").body[0].value

    def test_precedence(self):
        e = self.expr("2 + 3 * 4")
        self.assertEqual(e.op, "+")
        self.assertEqual(e.right.op, "*")

    def test_left_associative(self):
        e = self.expr("10 - 3 - 2")
        self.assertEqual(e.op, "-")
        self.assertEqual(e.left.op, "-")      # (10 - 3) - 2

    def test_parentheses(self):
        e = self.expr("(2 + 3) * 4")
        self.assertEqual(e.op, "*")
        self.assertEqual(e.left.op, "+")

    def test_logic_precedence(self):
        e = self.expr("true or false and false")
        self.assertEqual(e.op, "or")
        self.assertEqual(e.right.op, "and")

    def test_chained_comparison_rejected(self):
        with self.assertRaises(VerbatimError):
            parse("let b: bool = 1 < 2 < 3")

    def test_else_if_chain(self):
        node = parse("if a {\n} else if b {\n} else {\n}\n").body[0]
        self.assertIsInstance(node.otherwise[0], If)
        self.assertEqual(node.otherwise[0].otherwise, [])

    def test_assignment_vs_call(self):
        prog = parse("x = 1\nx[0] = 2\nprint(x)\n")
        self.assertIsInstance(prog.body[0], Assign)
        self.assertIsInstance(prog.body[1].target, Index)
        self.assertIsInstance(prog.body[2], ExprStmt)

    def test_function(self):
        f = parse("func add(a: int, b: int) -> int {\n    return a + b\n}\n").body[0]
        self.assertEqual([p.name for p in f.params], ["a", "b"])
        self.assertEqual(f.ret, "int")

    def test_syntax_errors(self):
        for bad in ["let x = 5", "if x {", "while true\n{\n}\n", "x +", "let a: [int = 1"]:
            with self.assertRaises(VerbatimError, msg=bad):
                parse(bad)

    def test_example_programs_parse(self):
        for name in ("factorial.vbt", "fizzbuzz.vbt", "arrays.vbt", "error_demo.vbt"):
            with open(os.path.join(EXAMPLES, name)) as f:
                self.assertIsInstance(parse(f.read()), Program, name)


if __name__ == "__main__":
    unittest.main()
