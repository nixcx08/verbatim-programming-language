# Verbatim Programming Language

### A Final Project for Language Translation and Execution
**Master of Science in Computer Science (MSCS)**

Verbatim is a small, statically typed teaching programming language developed as a final project for the course **Language Translation and Execution** in the Master of Science in Computer Science (MSCS) program.

The project demonstrates the design and implementation of a programming language, covering lexical analysis, syntax analysis, abstract syntax tree construction, static type checking, and program interpretation.

Verbatim is designed around the principle that *the compiler never guesses*. It emphasizes explicit type declarations, strict type checking, and predictable program behavior by disallowing implicit type conversions and truthy values.

## Language Features

- **Static Type System** – Explicit type declarations and compile-time type checking.
- **Primitive Data Types** – Integer, Boolean, and string.
- **Arrays** – Array declarations, literals, and indexing.
- **Expressions** – Arithmetic, comparison, and logical operators with defined precedence and associativity.
- **Control Flow** – Conditional statements (`if`, `else`, and `else if`) and `while` loops.
- **Functions** – Function declarations, parameters, return values, and function calls.
- **Recursion** – Support for recursive function execution.
- **Explicit Type Conversion** – Built-in conversion functions such as `str()` and `to_int()`.
- **Error Handling** – Syntax, type, and runtime error reporting.

## Language Processing Architecture

Verbatim follows a structured language processing pipeline:

```text
Source Code
    |
    v
Lexical Analysis
    |
    v
Syntax Analysis
    |
    v
Abstract Syntax Tree (AST)
    |
    v
Static Type Checking
    |
    v
Interpretation
    |
    v
Program Output
```

Each component performs a distinct responsibility in translating and executing Verbatim source programs.

## Technologies Used

- **Python** – Implementation language
- **Tkinter** – Graphical user interface
- **Recursive Descent Parsing** – Syntax analysis
- **Abstract Syntax Tree (AST)** – Intermediate representation of program structure

## Project Structure

```text
verbatim/
├── docs/
│   └── verbatim_grammar.md
├── examples/
│   ├── factorial.vbt
│   ├── fizzbuzz.vbt
│   ├── hello.vbt
│   └── ...
├── tests/
│   ├── check_cases.py
│   ├── test_front_end.py
│   └── test_interpreter.py
├── ast_nodes.py
├── errors.py
├── gui.py
├── interpreter.py
├── lexer.py
├── parser.py
├── typechecker.py
└── verbatim.py
```

## Sample Program

The following example demonstrates variable declarations, arithmetic expressions, explicit type conversion, and output.

```verbatim
let a: int = 10
let b: int = 5
let total: int = a + b

print(str(total))
```

Output:

```text
15
```

## Running Verbatim

1. Install Python 3.
2. Clone or download this repository.
3. Open the project directory.
4. Run the main application:

```bash
python verbatim.py
```

The graphical interface allows users to write and execute Verbatim programs.

## Testing

The project includes test files covering front-end processing, interpreter behavior, and language test cases.

Run the tests using:

```bash
python -m unittest discover -s tests
```

## Documentation

The `docs/` directory contains the formal grammar and supporting language documentation.

The `examples/` directory contains sample programs demonstrating the syntax and capabilities of Verbatim.

## Academic Context

**Course:** Language Translation and Execution  
**Program:** Master of Science in Computer Science (MSCS)  
**Project:** Verbatim Programming Language

## Author

Ma. Nicole L. Batallones

---

*Developed as an academic final project demonstrating programming language design, implementation, translation, and execution.*
