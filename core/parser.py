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

        program = ParseNode("program")

        while not self._match(TokenType.EOF):
            start_pos = self.pos
            statement = self._statement()
            if statement is not None:
                program.add_child(statement)

            self._consume_statement_terminator()

            if self.pos == start_pos:
                self.errors.append(f"Parser stalled at token {self._current()}")
                break

        return program if program.children else None

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

    def _consume_statement_terminator(self):
        if self._match(TokenType.SEMICOLON):
            self._advance()

    def _is_type_keyword(self, token: Token) -> bool:
        return token.type == TokenType.KEYWORD and token.lexeme in {
            "bool",
            "char",
            "double",
            "float",
            "int",
            "long",
            "short",
            "signed",
            "unsigned",
            "void",
        }

    def _statement(self) -> ParseNode:
        current = self._current()

        if current.type == TokenType.LBRACE:
            return self._block()

        if current.type == TokenType.KEYWORD:
            if current.lexeme == "for":
                return self._for_statement()
            if current.lexeme == "while":
                return self._while_statement()
            if current.lexeme == "if":
                return self._if_statement()
            if current.lexeme == "return":
                return self._return_statement()
            if current.lexeme in {"break", "continue"}:
                node = ParseNode(current.lexeme)
                self._advance()
                return node
            if self._is_type_keyword(current):
                return self._declaration_statement()

        if self._match(TokenType.IDENT) and self._peek().type == TokenType.ASSIGN:
            return self._assignment()
        if self._match(TokenType.IDENT) and self._peek().type in {
            TokenType.PLUS_ASSIGN,
            TokenType.MINUS_ASSIGN,
            TokenType.MUL_ASSIGN,
            TokenType.DIV_ASSIGN,
            TokenType.MOD_ASSIGN,
        }:
            return self._compound_assignment()

        if self._match(TokenType.SEMICOLON):
            self._advance()
            return ParseNode("empty")

        return self._expression()

    def _block(self) -> ParseNode:
        node = ParseNode("block")
        if not self._expect(TokenType.LBRACE):
            return node

        while not self._match(TokenType.RBRACE) and not self._match(TokenType.EOF):
            statement = self._statement()
            if statement is not None:
                node.add_child(statement)
            self._consume_statement_terminator()

        self._expect(TokenType.RBRACE)
        return node

    def _declaration_statement(self) -> ParseNode:
        type_token = self._current()
        self._advance()

        node = ParseNode("declaration", type_token.lexeme)

        if self._match(TokenType.IDENT):
            ident = ParseNode("id", self._current().value)
            self._advance()
            node.add_child(ident)

            if self._match(TokenType.ASSIGN):
                self._advance()
                node.add_child(self._expression())
        else:
            self.errors.append(f"Expected identifier after type {type_token.lexeme}")

        return node

    def _compound_assignment(self) -> ParseNode:
        left = ParseNode("id", self._current().value)
        self._advance()

        assign_op = self._current()
        self._advance()
        right = self._expression()

        node = ParseNode("assign", assign_op.lexeme)
        node.add_child(left)
        node.add_child(right)
        return node

    def _return_statement(self) -> ParseNode:
        self._advance()
        node = ParseNode("return")
        if not self._match(TokenType.SEMICOLON) and not self._match(TokenType.RBRACE):
            node.add_child(self._expression())
        return node

    def _if_statement(self) -> ParseNode:
        self._advance()
        node = ParseNode("if")
        if self._expect(TokenType.LPAREN):
            node.add_child(self._expression())
            self._expect(TokenType.RPAREN)
        node.add_child(self._statement())
        if self._match(TokenType.KEYWORD) and self._current().lexeme == "else":
            self._advance()
            node.add_child(self._statement())
        return node

    def _while_statement(self) -> ParseNode:
        self._advance()
        node = ParseNode("while")
        if self._expect(TokenType.LPAREN):
            node.add_child(self._expression())
            self._expect(TokenType.RPAREN)
        node.add_child(self._statement())
        return node

    def _for_statement(self) -> ParseNode:
        self._advance()
        node = ParseNode("for")

        if not self._expect(TokenType.LPAREN):
            return node

        node.add_child(self._for_initializer())
        self._expect(TokenType.SEMICOLON)

        if not self._match(TokenType.SEMICOLON):
            node.add_child(self._expression())
        else:
            node.add_child(ParseNode("empty"))
        self._expect(TokenType.SEMICOLON)

        if not self._match(TokenType.RPAREN):
            node.add_child(self._expression())
        else:
            node.add_child(ParseNode("empty"))
        self._expect(TokenType.RPAREN)

        if self._match(TokenType.EOF) or self._match(TokenType.RBRACE):
            node.add_child(ParseNode("empty"))
        else:
            node.add_child(self._statement())

        return node

    def _for_initializer(self) -> ParseNode:
        if self._match(TokenType.SEMICOLON):
            return ParseNode("empty")

        if self._current().type == TokenType.KEYWORD and self._is_type_keyword(self._current()):
            type_token = self._current()
            self._advance()
            node = ParseNode("declaration", type_token.lexeme)

            if self._match(TokenType.IDENT):
                ident = ParseNode("id", self._current().value)
                self._advance()
                node.add_child(ident)

                if self._match(TokenType.ASSIGN):
                    self._advance()
                    node.add_child(self._expression())
            else:
                self.errors.append(f"Expected identifier after type {type_token.lexeme}")

            return node

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
        return self._assignment_expression()

    def _assignment_expression(self) -> ParseNode:
        left = self._logical_or()

        if self._match(TokenType.ASSIGN):
            assign_op = self._current()
            self._advance()
            right = self._assignment_expression()

            node = ParseNode("assign", assign_op.lexeme)
            node.add_child(left)
            node.add_child(right)
            return node

        if self._match(TokenType.PLUS_ASSIGN) or self._match(TokenType.MINUS_ASSIGN) or self._match(TokenType.MUL_ASSIGN) or self._match(TokenType.DIV_ASSIGN) or self._match(TokenType.MOD_ASSIGN):
            assign_op = self._current()
            self._advance()
            right = self._assignment_expression()

            node = ParseNode("assign", assign_op.lexeme)
            node.add_child(left)
            node.add_child(right)
            return node

        return left

    def _logical_or(self) -> ParseNode:
        left = self._logical_and()

        while self._match(TokenType.OR):
            op = self._current()
            self._advance()
            right = self._logical_and()

            node = ParseNode("op", op.lexeme)
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

    def _logical_and(self) -> ParseNode:
        left = self._equality()

        while self._match(TokenType.AND):
            op = self._current()
            self._advance()
            right = self._equality()

            node = ParseNode("op", op.lexeme)
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

    def _equality(self) -> ParseNode:
        left = self._relational()

        while self._match(TokenType.EQ) or self._match(TokenType.NE):
            op = self._current()
            self._advance()
            right = self._relational()

            node = ParseNode("op", op.lexeme)
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

    def _relational(self) -> ParseNode:
        left = self._additive()

        while self._match(TokenType.LT) or self._match(TokenType.GT) or self._match(TokenType.LE) or self._match(TokenType.GE):
            op = self._current()
            self._advance()
            right = self._additive()

            node = ParseNode("op", op.lexeme)
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

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

        while self._match(TokenType.MUL) or self._match(TokenType.DIV) or self._match(TokenType.MOD):
            op = self._current()
            self._advance()
            right = self._unary()

            node = ParseNode("op", op.lexeme)
            node.add_child(left)
            node.add_child(right)
            left = node

        return left

    def _unary(self) -> ParseNode:
        if self._match(TokenType.MINUS) or self._match(TokenType.PLUS) or self._match(TokenType.NOT) or self._match(TokenType.INC) or self._match(TokenType.DEC):
            op = self._current()
            self._advance()
            operand = self._unary()

            node = ParseNode("op", op.lexeme)
            node.add_child(operand)
            return node

        return self._postfix()

    def _postfix(self) -> ParseNode:
        node = self._primary()

        while self._match(TokenType.INC) or self._match(TokenType.DEC):
            op = self._current()
            self._advance()
            postfix = ParseNode("op", op.lexeme)
            postfix.add_child(node)
            node = postfix

        return node

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

        if current.type == TokenType.KEYWORD and current.lexeme in {"true", "false"}:
            node = ParseNode("num", 1 if current.lexeme == "true" else 0)
            node.type_info = "int"
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
