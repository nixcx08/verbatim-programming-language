"""Tree-walking interpreter: runs a type-checked Program by walking its AST."""
import copy
import re

from ast_nodes import *
from errors import VerbatimError


class ReturnSignal(Exception):
    """Used to jump out of a function body when 'return' runs."""
    def __init__(self, value):
        self.value = value


class FuncValue:
    def __init__(self, decl):
        self.decl = decl


class Env:
    """One scope: a dictionary of names, plus a link to the enclosing scope (static scope)."""
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def find(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env
            env = env.parent
        raise KeyError(name)

    def get(self, name):
        return self.find(name).vars[name]

    def set(self, name, value):
        self.find(name).vars[name] = value

    def declare(self, name, value):
        self.vars[name] = value


def copy_value(v):
    """Arrays are copied whenever they are stored or passed (pass-by-value)."""
    return copy.deepcopy(v) if isinstance(v, list) else v


class Interpreter:
    def __init__(self, out=print):
        self.out = out
        self.globals = Env()

    def run(self, program):
        try:
            for s in program.body:
                self.exec(s, self.globals)
        except RecursionError:
            raise VerbatimError("Runtime error", "too many nested function calls", None,
                                "check that your recursive function reaches a base case")

    def exec(self, node, env):
        return getattr(self, "x_" + type(node).__name__)(node, env)

    def eval(self, node, env):
        return getattr(self, "v_" + type(node).__name__)(node, env)

    def run_block(self, stmts, env):
        for s in stmts:
            self.exec(s, env)

    def fail(self, msg, line, hint=None):
        raise VerbatimError("Runtime error", msg, line, hint)

    # ---------- statements ----------
    def x_VarDecl(self, n, env):
        env.declare(n.name, copy_value(self.eval(n.value, env)))

    def x_Assign(self, n, env):
        value = copy_value(self.eval(n.value, env))
        if isinstance(n.target, Name):
            env.set(n.target.name, value)
        else:
            arr = self.eval(n.target.obj, env)
            i = self.eval(n.target.index, env)
            self.check_index(arr, i, n.line)
            arr[i] = value

    def x_If(self, n, env):
        branch = n.then if self.eval(n.cond, env) else n.otherwise
        if branch is not None:
            self.run_block(branch, Env(env))

    def x_While(self, n, env):
        while self.eval(n.cond, env):
            self.run_block(n.body, Env(env))

    def x_FuncDecl(self, n, env):
        env.declare(n.name, FuncValue(n))

    def x_Return(self, n, env):
        raise ReturnSignal(None if n.value is None else copy_value(self.eval(n.value, env)))

    def x_ExprStmt(self, n, env):
        self.v_Call(n.call, env)

    # ---------- expressions ----------
    def v_IntLit(self, n, env):
        return n.value

    def v_StrLit(self, n, env):
        return n.value

    def v_BoolLit(self, n, env):
        return n.value

    def v_Name(self, n, env):
        return env.get(n.name)

    def v_ArrayLit(self, n, env):
        return [self.eval(item, env) for item in n.items]

    def check_index(self, arr, i, line):
        if i < 0 or i >= len(arr):
            self.fail(f"index {i} is out of range for an array of length {len(arr)}", line,
                      "valid indexes run from 0 to length - 1")

    def v_Index(self, n, env):
        arr = self.eval(n.obj, env)
        i = self.eval(n.index, env)
        self.check_index(arr, i, n.line)
        return arr[i]

    def v_Unary(self, n, env):
        v = self.eval(n.operand, env)
        return -v if n.op == "-" else not v

    def v_Binary(self, n, env):
        op = n.op
        if op == "and":                                   # short-circuit
            return self.eval(n.left, env) and self.eval(n.right, env)
        if op == "or":
            return self.eval(n.left, env) or self.eval(n.right, env)
        l, r = self.eval(n.left, env), self.eval(n.right, env)
        if op == "+": return l + r
        if op == "-": return l - r
        if op == "*": return l * r
        if op in ("/", "%"):
            if r == 0:
                self.fail("division by zero", n.line, "check the divisor before dividing")
            return l // r if op == "/" else l % r         # integer division rounds down
        if op == "==": return l == r
        if op == "!=": return l != r
        if op == "<": return l < r
        if op == "<=": return l <= r
        if op == ">": return l > r
        return l >= r

    def v_Call(self, n, env):
        args = [self.eval(a, env) for a in n.args]       # left to right
        if n.name == "print":
            self.out(args[0])
            return None
        if n.name == "len":
            return len(args[0])
        if n.name == "str":
            return str(args[0])
        if n.name == "to_int":
            if not re.fullmatch(r"-?[0-9]+", args[0]):
                self.fail(f'cannot convert "{args[0]}" to an int', n.line,
                          "the text must contain only digits, optionally starting with '-'")
            return int(args[0])
        fn = self.globals.get(n.name)
        local = Env(self.globals)                         # new scope whose parent is the global scope
        for p, a in zip(fn.decl.params, args):
            local.declare(p.name, copy_value(a))          # pass-by-value
        try:
            self.run_block(fn.decl.body, local)
        except ReturnSignal as r:
            return r.value
        return None
