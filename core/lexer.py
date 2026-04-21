from typing import List, Tuple, Optional
from utils.token import Token, TokenType, KEYWORDS
from core.symbol_table import SymbolTable
from utils.constants import DIGITS, LETTERS, LETTERS_DIGITS, WHITESPACE, OPERATORS


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.symbol_table = SymbolTable()
        self.errors: List[str] = []

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break

            char = self.source[self.pos]

            if char.isalpha():
                self._identifier()
            elif char.isdigit():
                self._number()
            elif self._starts_operator():
                self._operator()
            else:
                self.errors.append(
                    f"Lexical error at line {self.line}, column {self.column}: Unexpected character '{char}'"
                )
                self.pos += 1
                self.column += 1

        self.tokens.append(Token(TokenType.EOF, "EOF", None, self.line, self.column))
        return self.tokens

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char in WHITESPACE:
                if char == "\n":
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.pos += 1
            elif char == "/" and self.pos + 1 < len(self.source):
                if self.source[self.pos + 1] == "/":
                    while self.pos < len(self.source) and self.source[self.pos] != "\n":
                        self.pos += 1
                elif self.source[self.pos + 1] == "*":
                    self.pos += 2
                    self.column += 2
                    while self.pos < len(self.source) - 1:
                        if self.source[self.pos] == "*" and self.source[self.pos + 1] == "/":
                            self.pos += 2
                            self.column += 2
                            break
                        if self.source[self.pos] == "\n":
                            self.line += 1
                            self.column = 1
                            self.pos += 1
                        else:
                            self.pos += 1
                            self.column += 1
                else:
                    break
            else:
                break

    def _starts_operator(self) -> bool:
        if self.pos >= len(self.source):
            return False

        return any(self.source.startswith(op, self.pos) for op in OPERATORS)

    def _identifier(self):
        start = self.pos
        start_col = self.column

        while self.pos < len(self.source) and self.source[self.pos] in LETTERS_DIGITS:
            self.pos += 1
            self.column += 1

        lexeme = self.source[start : self.pos]

        if lexeme in KEYWORDS:
            token_type = TokenType.KEYWORD
            token = Token(token_type, lexeme, lexeme, self.line, start_col)
        else:
            index = self.symbol_table.add(lexeme)
            token = Token(TokenType.IDENT, lexeme, index, self.line, start_col)

        self.tokens.append(token)

    def _number(self):
        start = self.pos
        start_col = self.column
        has_dot = False
        num_str = ""

        while self.pos < len(self.source):
            char = self.source[self.pos]
            if char.isdigit():
                num_str += char
                self.pos += 1
                self.column += 1
            elif char == "." and not has_dot:
                has_dot = True
                num_str += char
                self.pos += 1
                self.column += 1
            else:
                break

        if has_dot:
            token_type = TokenType.FLOAT
            value = float(num_str)
        else:
            token_type = TokenType.INT
            value = int(num_str)

        token = Token(token_type, num_str, value, self.line, start_col)
        self.tokens.append(token)

    def _operator(self):
        matched = None
        for op in sorted(OPERATORS.keys(), key=len, reverse=True):
            if self.source.startswith(op, self.pos):
                matched = op
                break

        if matched is None:
            char = self.source[self.pos]
            self.errors.append(
                f"Lexical error at line {self.line}, column {self.column}: Unexpected operator '{char}'"
            )
            self.pos += 1
            self.column += 1
            return

        token_type = OPERATORS[matched]
        token = Token(token_type, matched, matched, self.line, self.column)
        self.tokens.append(token)
        self.pos += len(matched)
        self.column += len(matched)


def lex(source: str) -> Tuple[List[Token], SymbolTable, List[str]]:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    return tokens, lexer.symbol_table, lexer.errors
