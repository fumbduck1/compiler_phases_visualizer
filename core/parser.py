from typing import List, Optional
from utils.token import Token, TokenType
from core.symbol_table import SymbolTable


class ParseNode:
    def __init__(
        self, node_type: str, value=None, children: Optional[List["ParseNode"]] = None
    ):
        self.node_type = node_type
        self.value = value
        self.children = children or []
        self.type_info: Optional[str] = None
        self.coercion: Optional[str] = None

    def add_child(self, child: "ParseNode"):
        self.children.append(child)

    def __repr__(self):
        return f"Node({self.node_type}, {self.value})"

    def to_dict(self):
        return {
            "node_type": self.node_type,
            "value": self.value,
            "type_info": self.type_info,
            "children": [child.to_dict() for child in self.children],
        }

    def to_ascii(self, prefix="", is_last=True):
        result = prefix
        if is_last:
            result += "└── "
            new_prefix = prefix + "    "
        else:
            result += "├── "
            new_prefix = prefix + "│   "

        result += f"{self.node_type}"
        if self.value is not None:
            result += f": {self.value}"
        if self.type_info:
            result += f" [type: {self.type_info}]"
        result += "\n"

        for i, child in enumerate(self.children):
            result += child.to_ascii(new_prefix, i == len(self.children) - 1)

        return result


class Parser:
    def __init__(self, tokens: List[Token], symbol_table: SymbolTable):
        self.tokens = tokens
        self.symbol_table = symbol_table
        self.pos = 0
        self.errors: List[str] = []

    def parse(self) -> Optional[ParseNode]:
        if not self.tokens:
            self.errors.append("No tokens to parse")
            return None

        return self._statement()

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "EOF")

    def _peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, "EOF")

    def _advance(self):
        self.pos += 1

    def _match(self, token_type: str) -> bool:
        return self._current().type == token_type

    def _expect(self, token_type: str) -> bool:
        if self._match(token_type):
            self._advance()
            return True
        self.errors.append(f"Expected {token_type} but got {self._current()}")
        return False

    def _statement(self) -> ParseNode:
        if self._match(TokenType.IDENT) and self._peek().type == TokenType.ASSIGN:
            return self._assignment()
        return self._expression()

    def _assignment(self) -> ParseNode:
        left = ParseNode("id", self._current().value)
        self._advance()

        if self._match(TokenType.ASSIGN):
            assign_op = self._current()
            self._advance()
            right = self._expression()

            node = ParseNode("assign", assign_op.lexeme)
            node.add_child(left)
            node.add_child(right)
            return node

        return left

    def _expression(self) -> ParseNode:
        return self._additive()

    def _additive(self) -> ParseNode:
        left = self._multiplicative()

        while self._match(TokenType.PLUS) or self._match(TokenType.MINUS):
            op = self._current()
            self._advance()
            right = self._multiplicative()

            node = ParseNode("op", op.lexeme)
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

    def _multiplicative(self) -> ParseNode:
        left = self._unary()

        while self._match(TokenType.MUL) or self._match(TokenType.DIV):
            op = self._current()
            self._advance()
            right = self._unary()

            node = ParseNode("op", op.lexeme)
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

    def _unary(self) -> ParseNode:
        if self._match(TokenType.MINUS):
            op = self._current()
            self._advance()
            operand = self._unary()

            node = ParseNode("op", op.lexeme)
            node.add_child(operand)
            return node

        return self._primary()

    def _primary(self) -> ParseNode:
        current = self._current()

        if current.type == TokenType.IDENT:
            node = ParseNode("id", current.value)
            self._advance()
            return node

        if current.type == TokenType.INT or current.type == TokenType.FLOAT:
            node = ParseNode("num", current.value)
            node.type_info = "int" if current.type == TokenType.INT else "float"
            self._advance()
            return node

        if self._match(TokenType.LPAREN):
            self._advance()
            expr = self._expression()
            if self._match(TokenType.RPAREN):
                self._advance()
            return expr

        self.errors.append(f"Unexpected token: {current}")
        return ParseNode("error", str(current))


def parse(
    tokens: List[Token], symbol_table: SymbolTable
) -> tuple[Optional[ParseNode], List[str]]:
    parser = Parser(tokens, symbol_table)
    ast = parser.parse()
    return ast, parser.errors
