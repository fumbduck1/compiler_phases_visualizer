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
    PLUS_ASSIGN = "+="
    MINUS_ASSIGN = "-="
    MUL_ASSIGN = "*="
    DIV_ASSIGN = "/="
    MOD_ASSIGN = "%="
    PLUS = "+"
    MINUS = "-"
    MUL = "*"
    DIV = "/"
    MOD = "%"
    INC = "++"
    DEC = "--"
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    EQ = "=="
    NE = "!="
    AND = "&&"
    OR = "||"
    NOT = "!"
    BIT_AND = "&"
    BIT_OR = "|"
    BIT_XOR = "^"
    BIT_NOT = "~"
    SHL = "<<"
    SHR = ">>"
    ARROW = "->"
    SCOPE = "::"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    SEMICOLON = ";"
    COMMA = ","
    DOT = "."
    COLON = ":"
    QUESTION = "?"
    KEYWORD = "keyword"
    EOF = "EOF"
    UNKNOWN = "unknown"


KEYWORDS = {
    "break",
    "case",
    "char",
    "class",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "float",
    "for",
    "if",
    "int",
    "long",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "struct",
    "switch",
    "typedef",
    "union",
    "unsigned",
    "void",
    "volatile",
    "while",
    "bool",
    "true",
    "false",
    "namespace",
    "using",
    "template",
    "typename",
    "public",
    "private",
    "protected",
    "virtual",
    "override",
    "friend",
    "new",
    "delete",
    "this",
    "operator",
}
