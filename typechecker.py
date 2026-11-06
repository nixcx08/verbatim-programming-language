"""Static type checker. Runs BEFORE the program executes, so type mistakes
(like "5" + 3) are reported without running a single line. This is where
Verbatim's "the compiler never guesses" rule lives."""
from ast_nodes import *
from errors import VerbatimError


class FuncSig:
    def __init__(self, params, ret):
        self.params = params      # list of type strings
        self.ret = ret            # type string, or None if it returns nothing


BUILTINS = {
    "print": FuncSig(["string"], None),
    "len": FuncSig(["[any]"], "int"),          # special-cased: accepts any array
    "str": FuncSig(["int"], "string"),
    "to_int": FuncSig(["string"], "int"),
}


def merge(a, b):
    """Combine two types if they are compatible. '[?]' is the type of an empty [] literal."""
    if a == b:
        return a
    if a == "[?]" and b.startswith("["):
        return b
    if b == "[?]" and a.startswith("["):
        return a
    return None


def assignable(expected, actual):
    return merge(expected, actual) == expected


def art(t):
    """'a string', 'an int' (for error messages)."""
    return ("an " if t[0] in "aeiou" else "a ") + t


def show(node):
    """Source-like text for a node, used in hints."""
    if isinstance(node, Name):
        return node.name
    if isinstance(node, IntLit):
        return str(node.value)
    if isinstance(node, StrLit):
        return f'"{node.value}"'
    return "..."


def always_returns(stmts):
    for s in stmts:
        if isinstance(s, Return):
            return True
        if (isinstance(s, If) and s.otherwise is not None
                and always_returns(s.then) and always_returns(s.otherwise)):
            return True
    return False


class TypeChecker:
    def __init__(self):
        self.scopes = [dict(BUILTINS)]     # scopes[0] is the global scope (holds built-ins too)
        self.in_func = False
        self.ret = None

    # ---------- helpers ----------
    def error(self, msg, line, hint=None):
        raise VerbatimError("Type error", msg, line, hint)

    def declare(self, name, entry, line):
        if name in self.scopes[-1]:
            if name in BUILTINS and len(self.scopes) == 1:
                self.error(f"'{name}' is a built-in function and cannot be redefined", line)
            self.error(f"'{name}' is already declared in this scope", line,
                       f"to change its value, write:  {name} = ...")
        self.scopes[-1][name] = entry

    def lookup(self, name, line):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        self.error(f"'{name}' is not declared", line,
                   f"declare it first, e.g.  let {name}: int = 0")

    def block(self, stmts):
        self.scopes.append({})
        for s in stmts:
            self.stmt(s)
        self.scopes.pop()

    def stmt(self, node):
        getattr(self, "s_" + type(node).__name__)(node)

    def expr(self, node):
        return getattr(self, "e_" + type(node).__name__)(node)

    # ---------- statements ----------
    def check(self, program):
        for s in program.body:
            self.stmt(s)

    def s_VarDecl(self, n):
        t = self.expr(n.value)
        if not assignable(n.type, t):
            hint = None
            if {t, n.type} == {"int", "string"}:
                hint = "convert explicitly with str(...) or to_int(...)"
            self.error(f"cannot store {art(t)} in '{n.name}', which is declared as {n.type}", n.line, hint)
        self.declare(n.name, n.type, n.line)

    def s_Assign(self, n):
        if isinstance(n.target, Name):
            entry = self.lookup(n.target.name, n.line)
            if isinstance(entry, FuncSig):
                self.error(f"'{n.target.name}' is a function, not a variable", n.line)
            t = self.expr(n.value)
            if not assignable(entry, t):
                hint = None
                if {t, entry} == {"int", "string"}:
                    hint = "convert explicitly with str(...) or to_int(...)"
                self.error(f"cannot assign {art(t)} to '{n.target.name}', which is {art(entry)}", n.line, hint)
        else:                                            # arr[i] = value
            arr = self.expr(n.target.obj)
            if not arr.startswith("[") or arr == "[?]":
                self.error(f"only arrays can be indexed, but this is {art(arr)}", n.line)
            if self.expr(n.target.index) != "int":
                self.error("an array index must be an int", n.line)
            elem = arr[1:-1]
            t = self.expr(n.value)
            if not assignable(elem, t):
                self.error(f"cannot put {art(t)} into an array of {elem}", n.line)

    def condition(self, node, what):
        t = self.expr(node)
        if t != "bool":
            self.error(f"the {what} condition must be a bool, but this is {art(t)}", node.line,
                       "write an explicit comparison, e.g.  x > 0")

    def s_If(self, n):
        self.condition(n.cond, "if")
        self.block(n.then)
        if n.otherwise is not None:
            self.block(n.otherwise)

    def s_While(self, n):
        self.condition(n.cond, "while")
        self.block(n.body)

    def s_ExprStmt(self, n):
        self.check_call(n.call)

    def s_Return(self, n):
        if not self.in_func:
            self.error("'return' can only be used inside a function", n.line)
        if self.ret is None:
            if n.value is not None:
                self.error("this function has no return type, so it cannot return a value", n.line,
                           "add '-> type' to the function header")
        else:
            if n.value is None:
                self.error(f"this function must return {art(self.ret)}", n.line)
            t = self.expr(n.value)
            if not assignable(self.ret, t):
                self.error(f"this function returns {self.ret}, but this value is {art(t)}", n.line)

    def s_FuncDecl(self, n):
        if len(self.scopes) != 1:
            self.error("functions can only be declared at the top level of a program", n.line)
        self.declare(n.name, FuncSig([p.type for p in n.params], n.ret), n.line)   # before body: allows recursion
        self.scopes.append({})
        for p in n.params:
            self.declare(p.name, p.type, n.line)
        saved = (self.in_func, self.ret)
        self.in_func, self.ret = True, n.ret
        for s in n.body:
            self.stmt(s)
        self.in_func, self.ret = saved
        self.scopes.pop()
        if n.ret is not None and not always_returns(n.body):
            self.error(f"function '{n.name}' might finish without returning {art(n.ret)}", n.line,
                       "make sure every path ends with a return")

    # ---------- expressions ----------
    def e_IntLit(self, n):
        return "int"

    def e_StrLit(self, n):
        return "string"

    def e_BoolLit(self, n):
        return "bool"

    def e_Name(self, n):
        entry = self.lookup(n.name, n.line)
        if isinstance(entry, FuncSig):
            self.error(f"'{n.name}' is a function; call it like {n.name}(...)", n.line)
        return entry

    def e_ArrayLit(self, n):
        if not n.items:
            return "[?]"
        t = self.expr(n.items[0])
        for item in n.items[1:]:
            x = self.expr(item)
            m = merge(t, x)
            if m is None:
                self.error(f"all array items must have the same type, but found {t} and {x}", n.line)
            t = m
        return f"[{t}]"

    def e_Index(self, n):
        ot = self.expr(n.obj)
        if not ot.startswith("["):
            self.error(f"only arrays can be indexed, but this is {art(ot)}", n.line)
        if ot == "[?]":
            self.error("cannot index an empty array literal", n.line)
        if self.expr(n.index) != "int":
            self.error("an array index must be an int", n.line)
        return ot[1:-1]

    def e_Unary(self, n):
        t = self.expr(n.operand)
        if n.op == "-":
            if t != "int":
                self.error(f"'-' needs an int, but this is {art(t)}", n.line)
            return "int"
        if t != "bool":
            self.error(f"'not' needs a bool, but this is {art(t)}", n.line,
                       "use a comparison, e.g.  not (x > 0)")
        return "bool"

    def e_Binary(self, n):
        l, r, op = self.expr(n.left), self.expr(n.right), n.op
        mixed = {l, r} == {"int", "string"}
        if op == "+":
            if l == r and l in ("int", "string"):
                return l
            if mixed:
                int_node, str_node = (n.left, n.right) if l == "int" else (n.right, n.left)
                if isinstance(str_node, StrLit):
                    hint = f"convert the number to text with str({show(int_node)})"
                else:
                    hint = (f"convert the number to text with str({show(int_node)}), "
                            f"or the text to a number with to_int({show(str_node)})")
                self.error(f"cannot add {l} and {r}", n.line, hint)
            self.error(f"'+' works on two ints or two strings, not {l} and {r}", n.line)
        if op in ("-", "*", "/", "%"):
            if l == r == "int":
                return "int"
            self.error(f"'{op}' needs two ints, but got {l} and {r}", n.line,
                       "convert text to a number with to_int(...)" if mixed else None)
        if op in ("<", "<=", ">", ">="):
            if l == r == "int":
                return "bool"
            self.error(f"'{op}' compares two ints, but got {l} and {r}", n.line,
                       "convert text to a number with to_int(...)" if mixed else None)
        if op in ("==", "!="):
            if merge(l, r) is None:
                self.error(f"cannot compare {l} with {r}", n.line,
                           "convert one side so both have the same type" if mixed else None)
            return "bool"
        if l == r == "bool":                              # and / or
            return "bool"
        self.error(f"'{op}' needs two bools, but got {l} and {r}", n.line,
                   "use comparisons, e.g.  x > 0 and y > 0")

    def e_Call(self, n):
        t = self.check_call(n)
        if t is None:
            self.error(f"'{n.name}' does not give back a value, so it cannot be used here", n.line)
        return t

    def check_call(self, n):
        if not any(n.name in scope for scope in self.scopes):
            self.error(f"function '{n.name}' is not declared", n.line,
                       "functions must be declared above the line that calls them")
        sig = self.lookup(n.name, n.line)
        if not isinstance(sig, FuncSig):
            self.error(f"'{n.name}' is not a function", n.line)
        if len(n.args) != len(sig.params):
            self.error(f"'{n.name}' expects {len(sig.params)} argument(s) but got {len(n.args)}", n.line)
        for i, (arg, want) in enumerate(zip(n.args, sig.params), start=1):
            t = self.expr(arg)
            if want == "[any]":
                if not t.startswith("["):
                    self.error(f"'len' needs an array, but got {art(t)}", n.line)
            elif not assignable(want, t):
                hint = None
                if {t, want} == {"int", "string"}:
                    hint = (f"convert with str({show(arg)})" if want == "string"
                            else f"convert with to_int({show(arg)})")
                self.error(f"argument {i} of '{n.name}' must be {art(want)}, but this is {art(t)}", n.line, hint)
        return sig.ret


def check(program):
    TypeChecker().check(program)
