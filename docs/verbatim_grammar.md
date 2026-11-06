# Appendix A: Verbatim Grammar (EBNF)

Verbatim is a small, statically typed teaching language. Its distinctive idea is that *the compiler never guesses*: there are no implicit type conversions and no "truthy" values.

This appendix gives the complete lexical rules and the grammar for expressions and statements. The notation is ISO-style EBNF:

| Notation | Meaning |
|---|---|
| `a , b` | `a` followed by `b` |
| `a \| b` | `a` or `b` |
| `{ a }` | zero or more repetitions of `a` |
| `[ a ]` | `a` is optional |
| `( a )` | grouping |
| `"x"` | the literal text `x` |
| `(* ... *)` | comment |

---

## A.1 Lexical structure

```ebnf
IDENT      = letter , { letter | digit | "_" } ;      (* must not be a reserved word *)
INT        = digit , { digit } ;
STRING     = '"' , { any character except '"' and newline } , '"' ;
NEWLINE    = end of a non-blank line ;                (* blank lines and comments produce none *)
COMMENT    = "#" , { any character except newline } ; (* discarded by the lexer *)

letter     = "a".."z" | "A".."Z" ;
digit      = "0".."9" ;
```

**Reserved words:**
`func let if else while return true false and or not int bool string`

**Other rules:**

- Verbatim is **case-sensitive**: `Total` and `total` are different identifiers.
- Whitespace other than newlines is ignored between tokens.
- Operators and punctuation: `+ - * / % == != < <= > >= = -> : , ( ) [ ] { }`
- Built-in functions are ordinary identifiers, not reserved words: `print`, `len`, `str` (int to string), `to_int` (string to int).

---

## A.2 Statements

```ebnf
program     = { statement } ;

statement   = var_decl
            | assignment
            | if_stmt
            | while_stmt
            | func_decl
            | return_stmt
            | call_stmt ;

var_decl    = "let" , IDENT , ":" , type , "=" , expr , NEWLINE ;
assignment  = target , "=" , expr , NEWLINE ;
target      = IDENT , [ "[" , expr , "]" ] ;
call_stmt   = call , NEWLINE ;
return_stmt = "return" , [ expr ] , NEWLINE ;

if_stmt     = if_chain , NEWLINE ;
if_chain    = "if" , expr , block , [ "else" , ( if_chain | block ) ] ;
while_stmt  = "while" , expr , block , NEWLINE ;

func_decl   = "func" , IDENT , "(" , [ params ] , ")" ,
              [ "->" , type ] , block , NEWLINE ;
params      = param , { "," , param } ;
param       = IDENT , ":" , type ;

block       = "{" , NEWLINE , { statement } , "}" ;

type        = "int" | "bool" | "string" | "[" , type , "]" ;
```

---

## A.3 Expressions

Listed from lowest to highest precedence. Each rule only refers to rules below it, which is what fixes the precedence.

```ebnf
expr        = or_expr ;
or_expr     = and_expr , { "or" , and_expr } ;
and_expr    = not_expr , { "and" , not_expr } ;
not_expr    = "not" , not_expr | comparison ;
comparison  = additive , [ comp_op , additive ] ;
comp_op     = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
additive    = term , { ( "+" | "-" ) , term } ;
term        = unary , { ( "*" | "/" | "%" ) , unary } ;
unary       = "-" , unary | postfix ;
postfix     = primary , { "[" , expr , "]" } ;
primary     = INT | STRING | "true" | "false"
            | call
            | IDENT
            | array_lit
            | "(" , expr , ")" ;

call        = IDENT , "(" , [ args ] , ")" ;
args        = expr , { "," , expr } ;
array_lit   = "[" , [ args ] , "]" ;
```

### Operator summary

| Level (low to high) | Operators | Associativity |
|---|---|---|
| 1 | `or` | left |
| 2 | `and` | left |
| 3 | `not` | prefix |
| 4 | `==` `!=` `<` `<=` `>` `>=` | non-associative |
| 5 | `+` `-` | left |
| 6 | `*` `/` `%` | left |
| 7 | unary `-` | prefix |
| 8 | indexing `[ ]` | left |

---

## A.4 Why the grammar is unambiguous

- **Precedence is built into the rule layers.** `2 + 3 * 4` can only parse as `2 + (3 * 4)`, because `*` lives in `term`, which sits below `additive`.
- **Associativity comes from the `{ ... }` loops.** `a - b - c` parses as `(a - b) - c`.
- **Comparisons are non-associative.** `comparison` allows at most one operator, so `a < b < c` is a syntax error rather than something that silently means something else.
- **No dangling else.** Braces are mandatory, so every `else` belongs to the nearest `if`.
- **`else if` versus `else`** is decided by one token: after `else`, the keyword `if` starts a chain and `{` starts a block.
- **Statements that start with `IDENT`** are told apart by the next token: `(` means a call, while `=` or `[` means an assignment.
- **`else` must be on the same line as the closing `}`**, because a NEWLINE ends the statement.

---

## A.5 Worked parse example

Source: `let total: int = a + b * 2`

```
var_decl
├── "let"
├── IDENT   total
├── ":"
├── type    int
├── "="
└── expr
    └── or_expr → and_expr → not_expr → comparison
        └── additive
            ├── term → unary → postfix → primary → IDENT a
            ├── "+"
            └── term
                ├── unary → postfix → primary → IDENT b
                ├── "*"
                └── unary → postfix → primary → INT 2
```

The multiplication `b * 2` is grouped inside one `term`, so it binds tighter than the `+`.

---

## A.6 Example programs accepted by this grammar

```verbatim
# Factorial
func factorial(n: int) -> int {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

print(str(factorial(5)))
```

```verbatim
# FizzBuzz
let i: int = 1
while i <= 15 {
    if i % 15 == 0 {
        print("FizzBuzz")
    } else if i % 3 == 0 {
        print("Fizz")
    } else if i % 5 == 0 {
        print("Buzz")
    } else {
        print(str(i))
    }
    i = i + 1
}
```

Note: because `print` accepts only strings, numbers must be converted explicitly with `str(...)`. This is the "never guesses" rule applied to output.
