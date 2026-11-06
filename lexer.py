"""Lexer: turns Verbatim source text into a list of tokens (grammar section A.1)."""
import sys
from dataclasses import dataclass

from errors import VerbatimError

KEYWORDS = {
    "func", "let", "if", "else", "while", "return", "true", "false",
    "and", "or", "not", "int", "bool", "string",
}
TWO_CHAR = {"==", "!=", "<=", ">=", "->"}
ONE_CHAR = set("+-*/%=<>:,()[]{}")


@dataclass
class Token:
    type: str    # "IDENT", "INT", "STRING", "NEWLINE", "EOF", or the keyword/symbol itself
    value: str
    line: int


def _is_letter(c):
    return c.isascii() and c.isalpha()


def _is_digit(c):
    return c.isascii() and c.isdigit()


def tokenize(source):
    tokens = []
    lines = source.splitlines()
    for lineno, text in enumerate(lines, start=1):
        before = len(tokens)
        i, n = 0, len(text)
        while i < n:
            c = text[i]
            if c in " \t\r":                      # whitespace (not newlines) is ignored
                i += 1
            elif c == "#":                        # comment: discard rest of line
                break
            elif _is_letter(c):                   # identifier or keyword
                j = i
                while j < n and (_is_letter(text[j]) or _is_digit(text[j]) or text[j] == "_"):
                    j += 1
                word = text[i:j]
                tokens.append(Token(word if word in KEYWORDS else "IDENT", word, lineno))
                i = j
            elif _is_digit(c):                    # integer literal
                j = i
                while j < n and _is_digit(text[j]):
                    j += 1
                if j < n and (_is_letter(text[j]) or text[j] == "_"):
                    raise VerbatimError("Lexical error", f"invalid number '{text[i:j + 1]}...'",
                                        lineno, "identifiers cannot start with a digit")
                tokens.append(Token("INT", text[i:j], lineno))
                i = j
            elif c == '"':                        # string literal (no escapes, one line)
                j = text.find('"', i + 1)
                if j == -1:
                    raise VerbatimError("Lexical error", "string is missing its closing quote",
                                        lineno, 'add a " at the end of the string')
                tokens.append(Token("STRING", text[i + 1:j], lineno))
                i = j + 1
            elif text[i:i + 2] in TWO_CHAR:       # check two-character symbols first
                tokens.append(Token(text[i:i + 2], text[i:i + 2], lineno))
                i += 2
            elif c in ONE_CHAR:
                tokens.append(Token(c, c, lineno))
                i += 1
            else:
                hint = "use 'not' instead of '!'" if c == "!" else None
                raise VerbatimError("Lexical error", f"unexpected character {c!r}", lineno, hint)
        if len(tokens) > before:                  # blank/comment-only lines make no NEWLINE
            tokens.append(Token("NEWLINE", "\\n", lineno))
    tokens.append(Token("EOF", "", len(lines) + 1))
    return tokens


if __name__ == "__main__":                        # python lexer.py file.vbt  -> show tokens
    try:
        for t in tokenize(open(sys.argv[1]).read()):
            print(f"{t.line:>3}  {t.type:<8} {t.value!r}")
    except VerbatimError as e:
        print(e)
