from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class Token:
    type: str
    lexeme: str
    value: Optional[Any] = None
    line: int = 1
    column: int = 1

    def __repr__(self):
        if self.value is not None:
            return f"({self.type},{self.value})"
        return f"({self.type})"

    def to_dict(self):
        return {
            "type": self.type,
            "lexeme": self.lexeme,
            "value": self.value,
            "line": self.line,
            "column": self.column,
        }


class TokenType:
    IDENT = "id"
    NUMBER = "num"
    FLOAT = "float"
    INT = "int"
    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    MUL = "*"
    DIV = "/"
    LPAREN = "("
    RPAREN = ")"
    SEMICOLON = ";"
    COMMA = ","
    KEYWORD = "keyword"
    EOF = "EOF"
    UNKNOWN = "unknown"


KEYWORDS = {"int", "float", "if", "else", "while", "return"}
