"""AST node definitions: the tree the parser builds and the interpreter walks."""
from dataclasses import dataclass
from typing import List, Optional, Union

# Types are plain strings: "int", "bool", "string", "[int]", "[[string]]", ...

# ---- Expressions ----
@dataclass
class IntLit:
    value: int
    line: int = 0

@dataclass
class StrLit:
    value: str
    line: int = 0

@dataclass
class BoolLit:
    value: bool
    line: int = 0

@dataclass
class Name:
    name: str
    line: int = 0

@dataclass
class ArrayLit:
    items: list
    line: int = 0

@dataclass
class Call:
    name: str
    args: list
    line: int = 0

@dataclass
class Index:
    obj: object
    index: object
    line: int = 0

@dataclass
class Unary:
    op: str            # "-" or "not"
    operand: object
    line: int = 0

@dataclass
class Binary:
    op: str            # + - * / % == != < <= > >= and or
    left: object
    right: object
    line: int = 0

# ---- Statements ----
@dataclass
class VarDecl:
    name: str
    type: str
    value: object
    line: int = 0

@dataclass
class Assign:
    target: Union[Name, Index]
    value: object
    line: int = 0

@dataclass
class If:
    cond: object
    then: list
    otherwise: Optional[list] = None   # list of statements; an "else if" is a one-item list holding an If
    line: int = 0

@dataclass
class While:
    cond: object
    body: list
    line: int = 0

@dataclass
class Param:
    name: str
    type: str

@dataclass
class FuncDecl:
    name: str
    params: List[Param]
    ret: Optional[str]
    body: list
    line: int = 0

@dataclass
class Return:
    value: Optional[object]
    line: int = 0

@dataclass
class ExprStmt:
    call: Call
    line: int = 0

@dataclass
class Program:
    body: list
