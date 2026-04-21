from typing import Any, Dict, List, Optional

from utils.token import TokenType


class VisualHelpers:
    @staticmethod
    def _symbol_name(symbol_table, index: Optional[int]) -> str:
        if symbol_table is None or index is None:
            return ""

        symbol = symbol_table.get_by_index(index)
        if not symbol:
            return str(index)
        return symbol.get("name") or str(index)

    @staticmethod
    def _node_label(node, include_types: bool = False, semantic: bool = False, symbol_table=None) -> str:
        if node is None:
            return "?"

        label = node.node_type

        if node.node_type == "id":
            label = f"<id,{node.value}>"
        elif node.node_type == "num":
            label = f"num: {node.value}"
        elif node.node_type == "op":
            label = str(node.value)
        elif node.value is not None:
            label = f"{node.node_type}: {node.value}"

        if node.node_type in {"program", "block", "for", "while", "if", "return", "declaration", "empty"} and node.value is not None:
            label = f"{node.node_type}: {node.value}"
        elif node.node_type in {"program", "block", "for", "while", "if", "return", "declaration", "empty"}:
            label = node.node_type

        if include_types and node.type_info:
            label = f"{label} [{node.type_info}]"

        if (
            semantic
            and node.node_type == "num"
            and isinstance(node.value, int)
            and getattr(node, "coercion", None) == "intfloat"
        ):
            label = f"{label}\ninttofloat()"

        return label

    @staticmethod
    def _node_to_tree(node, include_types: bool = False, semantic: bool = False, symbol_table=None) -> Dict[str, Any]:
        if node is None:
            return {"label": "?", "children": []}

        return {
            "label": VisualHelpers._node_label(node, include_types, semantic, symbol_table),
            "children": [
                VisualHelpers._node_to_tree(child, include_types, semantic, symbol_table)
                for child in getattr(node, "children", [])
            ],
        }

    @staticmethod
    def _to_syntax_tree_model(ast, symbol_table=None):
        return VisualHelpers._node_to_tree(ast, include_types=False, semantic=False, symbol_table=symbol_table)

    @staticmethod
    def _to_tree_model(ast, include_types: bool = False, semantic: bool = False, symbol_table=None):
        return VisualHelpers._node_to_tree(ast, include_types=include_types, semantic=semantic, symbol_table=symbol_table)

    @staticmethod
    def lexical_identifiers_rows(tokens) -> List[List[Any]]:
        rows = []
        seen = set()
        for token in tokens:
            if token.type == TokenType.IDENT and token.lexeme not in seen:
                seen.add(token.lexeme)
                rows.append([token.lexeme, token.value])
        return rows

    @staticmethod
    def lexical_operators_rows(tokens) -> List[List[Any]]:
        rows = []
        seen = set()
        for token in tokens:
            if token.type in {
                TokenType.ASSIGN,
                TokenType.PLUS_ASSIGN,
                TokenType.MINUS_ASSIGN,
                TokenType.MUL_ASSIGN,
                TokenType.DIV_ASSIGN,
                TokenType.MOD_ASSIGN,
                TokenType.PLUS,
                TokenType.MINUS,
                TokenType.MUL,
                TokenType.DIV,
                TokenType.MOD,
                TokenType.INC,
                TokenType.DEC,
                TokenType.LT,
                TokenType.GT,
                TokenType.LE,
                TokenType.GE,
                TokenType.EQ,
                TokenType.NE,
                TokenType.AND,
                TokenType.OR,
                TokenType.NOT,
                TokenType.BIT_AND,
                TokenType.BIT_OR,
                TokenType.BIT_XOR,
                TokenType.BIT_NOT,
                TokenType.SHL,
                TokenType.SHR,
                TokenType.ARROW,
                TokenType.SCOPE,
                TokenType.LPAREN,
                TokenType.RPAREN,
                TokenType.LBRACE,
                TokenType.RBRACE,
                TokenType.LBRACKET,
                TokenType.RBRACKET,
                TokenType.SEMICOLON,
                TokenType.COMMA,
                TokenType.DOT,
                TokenType.COLON,
                TokenType.QUESTION,
            } and token.lexeme not in seen:
                seen.add(token.lexeme)
                rows.append([token.lexeme, token.type])
        return rows

    @staticmethod
    def lexical_literals_rows(tokens) -> List[List[Any]]:
        rows = []
        seen = set()
        for token in tokens:
            if token.type in {TokenType.INT, TokenType.FLOAT} and token.lexeme not in seen:
                seen.add(token.lexeme)
                rows.append([token.lexeme, token.type])
        return rows

    @staticmethod
    def lexical_token_rows(tokens) -> List[List[Any]]:
        parts = []

        for token in tokens:
            if token.type == TokenType.EOF:
                continue

            if token.type == TokenType.IDENT:
                parts.append(f"<id,{token.value}>")
            elif token.type in {TokenType.INT, TokenType.FLOAT}:
                token_name = "int" if token.type == TokenType.INT else "float"
                parts.append(f"<{token_name},{token.lexeme}>")
            elif token.type == TokenType.KEYWORD:
                parts.append(f"<kw,{token.lexeme}>")
            else:
                parts.append(f"<{token.lexeme}>")

        if not parts:
            return []

        expression = "".join(parts)
        return [[expression]]
