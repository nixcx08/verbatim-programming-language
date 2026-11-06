"""Recursive-descent parser. Each grammar rule in docs/grammar.md is one method here."""
import sys

from ast_nodes import *
from errors import VerbatimError
from lexer import tokenize

COMP_OPS = {"==", "!=", "<", "<=", ">", ">="}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- helpers ----------
    def peek(self, k=0):
        return self.tokens[min(self.pos + k, len(self.tokens) - 1)]

    def at(self, *types):
        return self.peek().type in types

    def advance(self):
        tok = self.peek()
        if tok.type != "EOF":
            self.pos += 1
        return tok

    @staticmethod
    def describe(tok):
        if tok.type == "NEWLINE":
            return "the end of the line"
        if tok.type == "EOF":
            return "the end of the file"
        return repr(tok.value)

    def error(self, message, tok=None, hint=None):
        tok = tok or self.peek()
        raise VerbatimError("Syntax error", message, tok.line, hint)

    def expect(self, ttype, what=None, hint=None):
        if not self.at(ttype):
            what = what or repr(ttype)
            self.error(f"expected {what} but found {self.describe(self.peek())}", hint=hint)
        return self.advance()

    # ---------- program and statements ----------
    def program(self):
        body = []
        while not self.at("EOF"):
            body.append(self.statement())
        return Program(body)

    def statement(self):
        t = self.peek().type
        if t == "let":
            return self.var_decl()
        if t == "if":
            return self.if_stmt()
        if t == "while":
            return self.while_stmt()
        if t == "func":
            return self.func_decl()
        if t == "return":
            return self.return_stmt()
        if t == "IDENT":
            return self.assignment_or_call()
        self.error(f"expected a statement but found {self.describe(self.peek())}")

    def var_decl(self):
        line = self.advance().line                       # 'let'
        name = self.expect("IDENT", "a variable name").value
        self.expect(":", "':' and a type", hint="declare the type, e.g.  let x: int = 5")
        typ = self.type()
        self.expect("=", "'='")
        value = self.expr()
        self.expect("NEWLINE", "the end of the line")
        return VarDecl(name, typ, value, line)

    def assignment_or_call(self):
        line = self.peek().line
        if self.peek(1).type == "(":                     # call statement
            call = self.call()
            self.expect("NEWLINE", "the end of the line")
            return ExprStmt(call, line)
        name = self.expect("IDENT")
        target = Name(name.value, line)
        if self.at("["):
            self.advance()
            idx = self.expr()
            self.expect("]", "']'")
            target = Index(target, idx, line)
        self.expect("=", "'=' (or a function call)")
        value = self.expr()
        self.expect("NEWLINE", "the end of the line")
        return Assign(target, value, line)

    def return_stmt(self):
        line = self.advance().line
        value = None if self.at("NEWLINE") else self.expr()
        self.expect("NEWLINE", "the end of the line")
        return Return(value, line)

    def if_chain(self):
        line = self.advance().line                       # 'if'
        cond = self.expr()
        then = self.block()
        otherwise = None
        if self.at("else"):
            self.advance()
            otherwise = [self.if_chain()] if self.at("if") else self.block()
        return If(cond, then, otherwise, line)

    def if_stmt(self):
        node = self.if_chain()
        self.expect("NEWLINE", "the end of the line")
        return node

    def while_stmt(self):
        line = self.advance().line
        cond = self.expr()
        body = self.block()
        self.expect("NEWLINE", "the end of the line")
        return While(cond, body, line)

    def func_decl(self):
        line = self.advance().line
        name = self.expect("IDENT", "a function name").value
        self.expect("(", "'('")
        params = []
        if not self.at(")"):
            params.append(self.param())
            while self.at(","):
                self.advance()
                params.append(self.param())
        self.expect(")", "')'")
        ret = None
        if self.at("->"):
            self.advance()
            ret = self.type()
        body = self.block()
        self.expect("NEWLINE", "the end of the line")
        return FuncDecl(name, params, ret, body, line)

    def param(self):
        name = self.expect("IDENT", "a parameter name").value
        self.expect(":", "':' and a type", hint="every parameter needs a type, e.g.  n: int")
        return Param(name, self.type())

    def block(self):
        self.expect("{", "'{'", hint="blocks use braces, and '{' goes on the same line")
        self.expect("NEWLINE", "a new line after '{'")
        stmts = []
        while not self.at("}"):
            if self.at("EOF"):
                self.error("reached the end of the file; a block is missing its '}'")
            stmts.append(self.statement())
        self.advance()                                    # '}'
        return stmts

    def type(self):
        if self.at("int", "bool", "string"):
            return self.advance().value
        if self.at("["):
            self.advance()
            inner = self.type()
            self.expect("]", "']'")
            return f"[{inner}]"
        self.error(f"expected a type (int, bool, string or [type]) but found {self.describe(self.peek())}")

    # ---------- expressions (lowest to highest precedence) ----------
    def expr(self):
        return self.or_expr()

    def or_expr(self):
        left = self.and_expr()
        while self.at("or"):
            tok = self.advance()
            left = Binary("or", left, self.and_expr(), tok.line)
        return left

    def and_expr(self):
        left = self.not_expr()
        while self.at("and"):
            tok = self.advance()
            left = Binary("and", left, self.not_expr(), tok.line)
        return left

    def not_expr(self):
        if self.at("not"):
            tok = self.advance()
            return Unary("not", self.not_expr(), tok.line)
        return self.comparison()

    def comparison(self):
        left = self.additive()
        if self.peek().type in COMP_OPS:
            tok = self.advance()
            left = Binary(tok.type, left, self.additive(), tok.line)
            if self.peek().type in COMP_OPS:
                self.error("comparisons cannot be chained",
                           hint="combine them with 'and', e.g.  a < b and b < c")
        return left

    def additive(self):
        left = self.term()
        while self.at("+", "-"):
            tok = self.advance()
            left = Binary(tok.type, left, self.term(), tok.line)
        return left

    def term(self):
        left = self.unary()
        while self.at("*", "/", "%"):
            tok = self.advance()
            left = Binary(tok.type, left, self.unary(), tok.line)
        return left

    def unary(self):
        if self.at("-"):
            tok = self.advance()
            return Unary("-", self.unary(), tok.line)
        return self.postfix()

    def postfix(self):
        node = self.primary()
        while self.at("["):
            tok = self.advance()
            idx = self.expr()
            self.expect("]", "']'")
            node = Index(node, idx, tok.line)
        return node

    def primary(self):
        tok = self.peek()
        if tok.type == "INT":
            self.advance()
            return IntLit(int(tok.value), tok.line)
        if tok.type == "STRING":
            self.advance()
            return StrLit(tok.value, tok.line)
        if tok.type in ("true", "false"):
            self.advance()
            return BoolLit(tok.type == "true", tok.line)
        if tok.type == "IDENT":
            if self.peek(1).type == "(":
                return self.call()
            self.advance()
            return Name(tok.value, tok.line)
        if tok.type == "[":
            self.advance()
            items = self.args("]")
            self.expect("]", "']'")
            return ArrayLit(items, tok.line)
        if tok.type == "(":
            self.advance()
            inner = self.expr()
            self.expect(")", "')'")
            return inner
        self.error(f"expected a value but found {self.describe(tok)}")

    def call(self):
        tok = self.expect("IDENT")
        self.expect("(", "'('")
        args = self.args(")")
        self.expect(")", "')'")
        return Call(tok.value, args, tok.line)

    def args(self, closer):
        items = []
        if not self.at(closer):
            items.append(self.expr())
            while self.at(","):
                self.advance()
                items.append(self.expr())
        return items


def parse(source):
    """Source text -> Program AST."""
    return Parser(tokenize(source)).program()


if __name__ == "__main__":                        # python parser.py file.vbt  -> show the tree
    from pprint import pprint
    try:
        pprint(parse(open(sys.argv[1]).read()), width=100)
    except VerbatimError as e:
        print(e)
