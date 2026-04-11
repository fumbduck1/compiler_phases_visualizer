from typing import List, Optional, Dict, Any
from core.parser import ParseNode
from core.symbol_table import SymbolTable


class TypeInfo:
    INT = "int"
    FLOAT = "float"
    UNKNOWN = "unknown"

    @staticmethod
    def coerce(from_type: str, to_type: str) -> Optional[str]:
        if from_type == to_type:
            return None
        if from_type == TypeInfo.INT and to_type == TypeInfo.FLOAT:
            return "intfloat"
        return None

    @staticmethod
    def display_coercion(coercion: Optional[str]) -> str:
        if coercion == "intfloat":
            return "inttofloat()"
        return coercion or ""


class SemanticAnalyzer:
    def __init__(self, ast: ParseNode, symbol_table: SymbolTable):
        self.ast = ast
        self.symbol_table = symbol_table
        self.errors: List[str] = []
        self.coercions: List[Dict[str, Any]] = []
        self.temp_counter = 0

    def analyze(self) -> ParseNode:
        if self.ast is None:
            return None
        self._visit(self.ast)
        return self.ast

    def _visit(self, node: ParseNode):
        if node.node_type == "assign":
            self._analyze_assignment(node)
        elif node.node_type == "op":
            self._analyze_operation(node)
        elif node.node_type == "id":
            self._analyze_identifier(node)
        elif node.node_type == "num":
            self._analyze_numeric_literal(node)

    def _record_coercion(self, node: ParseNode, from_type: str, to_type: str):
        coercion_op = TypeInfo.coerce(from_type, to_type)
        if not coercion_op:
            return

        node.coercion = coercion_op
        self.coercions.append(
            {
                "node": node,
                "coercion": TypeInfo.display_coercion(coercion_op),
                "op": coercion_op,
                "from": from_type,
                "to": to_type,
            }
        )

    def _analyze_numeric_literal(self, node: ParseNode):
        # Every direct integer literal is promoted through inttofloat() semantics.
        if isinstance(node.value, int):
            node.type_info = TypeInfo.FLOAT
            self._record_coercion(node, TypeInfo.INT, TypeInfo.FLOAT)
        elif isinstance(node.value, float):
            node.type_info = TypeInfo.FLOAT
        else:
            node.type_info = TypeInfo.UNKNOWN

    def _analyze_assignment(self, node: ParseNode):
        if len(node.children) >= 2:
            left_child = node.children[0]
            right_child = node.children[1]

            # Visit RHS first to resolve its type
            self._visit(right_child)

            # Infer LHS identifier type from RHS expression type
            if left_child.node_type == "id" and right_child.type_info:
                left_child.type_info = right_child.type_info
                # Update symbol table with inferred type
                sym = self.symbol_table.get_by_index(left_child.value)
                if sym:
                    sym["dtype"] = right_child.type_info
            else:
                # Visit LHS as fallback
                self._visit(left_child)

            # Check for coercions between LHS and RHS
            if left_child.type_info and right_child.type_info:
                self._record_coercion(
                    right_child, right_child.type_info, left_child.type_info
                )

    def _analyze_operation(self, node: ParseNode):
        for child in node.children:
            self._visit(child)

        if len(node.children) == 2:
            left_type = node.children[0].type_info or TypeInfo.UNKNOWN
            right_type = node.children[1].type_info or TypeInfo.UNKNOWN

            # If any operand is FLOAT, promote result to FLOAT and coerce other operands
            if left_type == TypeInfo.FLOAT or right_type == TypeInfo.FLOAT:
                node.type_info = TypeInfo.FLOAT

                # Coerce INT or UNKNOWN to FLOAT in float context
                for child in node.children:
                    if child.type_info == TypeInfo.INT:
                        self._record_coercion(child, TypeInfo.INT, TypeInfo.FLOAT)
                        child.type_info = TypeInfo.FLOAT
            else:
                node.type_info = TypeInfo.INT
        elif len(node.children) == 1:
            node.type_info = node.children[0].type_info

    def _analyze_identifier(self, node: ParseNode):
        sym = self.symbol_table.get_by_index(node.value)
        if sym:
            node.type_info = sym.get("dtype") or TypeInfo.FLOAT
        else:
            # Unknown identifiers default to FLOAT to enable coercion detection
            node.type_info = TypeInfo.FLOAT

    def get_coercions(self) -> List[Dict[str, Any]]:
        return self.coercions


def analyze_semantics(
    ast: ParseNode, symbol_table: SymbolTable
) -> tuple[ParseNode, List[str], List[Dict[str, Any]]]:
    analyzer = SemanticAnalyzer(ast, symbol_table)
    ast = analyzer.analyze()
    return ast, analyzer.errors, analyzer.get_coercions()
