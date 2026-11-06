"""Shared error type. Every stage (lexer, parser, checker, interpreter) raises this."""


class VerbatimError(Exception):
    def __init__(self, kind, message, line=None, hint=None):
        super().__init__(message)
        self.kind = kind        # e.g. "Syntax error", "Type error"
        self.message = message
        self.line = line
        self.hint = hint

    def __str__(self):
        where = f" on line {self.line}" if self.line else ""
        text = f"{self.kind}{where}: {self.message}"
        if self.hint:
            text += f"\n  Hint: {self.hint}"
        return text
