from typing import List, Optional
from core.parser import ParseNode


class TACInstruction:
    def __init__(self, op: str, arg1=None, arg2=None, result=None, type_info=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.type_info = type_info  # Type of result (int, float, etc.)

    def __repr__(self):
        type_suffix = f":{self.type_info}" if self.type_info else ""
        if self.result:
            if self.op == "=" and self.arg1 is not None:
                return f"{self.result} = {self.arg1}{type_suffix}"
            if self.arg2:
                return f"{self.result} = {self.arg1} {self.op} {self.arg2}{type_suffix}"
            elif self.arg1:
                return f"{self.result} = {self.op}({self.arg1}){type_suffix}"
            return f"{self.result} = {self.op}{type_suffix}"
        return f"{self.op} {self.arg1} {self.arg2}{type_suffix}"

    def to_dict(self):
        return {
            "op": self.op,
            "arg1": self.arg1,
            "arg2": self.arg2,
            "result": self.result,
            "type_info": self.type_info,
        }


class IntermediateCodeGenerator:
    def __init__(self, ast: ParseNode):
        self.ast = ast
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
        self.temp_types = {}  # Track types of temps: {temp_name: type}

    def _emit_copy(self, operand: str, type_info=None) -> str:
        result = self._new_temp()
        instr = TACInstruction("=", arg1=operand, result=result, type_info=type_info)
        self.instructions.append(instr)
        self.temp_types[result] = type_info
        return result

    def _materialize_operand(self, node: ParseNode) -> Optional[str]:
        if node is None:
            return None

        if hasattr(node, "coercion") and node.coercion:
            return self._handle_coercion(node)

        if node.node_type == "id":
            return self._emit_copy(f"id{node.value}", node.type_info)
        if node.node_type == "num":
            return self._emit_copy(str(node.value), node.type_info)

        return self._visit(node, None)

    def _materialize_operand_without_coercion(self, node: ParseNode) -> Optional[str]:
        if node is None:
            return None

        if node.node_type == "id":
            return self._emit_copy(f"id{node.value}", node.type_info)
        if node.node_type == "num":
            return self._emit_copy(str(node.value), node.type_info)

        return self._visit_without_coercion(node)

    def generate(self) -> List[TACInstruction]:
        if self.ast is None:
            return []
        self._visit(self.ast, None)
        return self.instructions

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def _visit(self, node: ParseNode, result: Optional[str]) -> Optional[str]:
        if node is None:
            return None

        # If this node has a coercion, emit it first and return the converted value
        if hasattr(node, 'coercion') and node.coercion:
            return self._handle_coercion(node)

        if node.node_type == "assign":
            return self._gen_assign(node)
        elif node.node_type == "op":
            return self._gen_op(node)
        elif node.node_type == "id":
            operand = f"id{node.value}"
            return operand
        elif node.node_type == "num":
            return str(node.value)

        return None

    def _handle_coercion(self, node: ParseNode) -> str:
        """Emit coercion instruction for a node with coercion attribute."""
        # Recursively visit the node without coercion to get the raw operand
        if node.node_type in ("num", "id"):
            operand = self._materialize_operand_without_coercion(node)
        else:
            # For complex expressions, visit normally then coerce result
            operand = self._visit_without_coercion(node)
        
        result = self._new_temp()
        result_type = node.type_info if hasattr(node, 'type_info') else None
        coerce_instr = TACInstruction(node.coercion, arg1=operand, result=result, type_info=result_type)
        self.instructions.append(coerce_instr)
        self.temp_types[result] = result_type
        return result

    def _visit_without_coercion(self, node: ParseNode) -> Optional[str]:
        """Visit a node ignoring its coercion attribute."""
        if node is None:
            return None

        if node.node_type == "assign":
            if len(node.children) >= 2:
                target = self._visit_without_coercion(node.children[0])
                value = self._materialize_operand_without_coercion(node.children[1])
                rhs_type = node.children[1].type_info if hasattr(node.children[1], 'type_info') else None
                instr = TACInstruction("=", arg1=value, result=target, type_info=rhs_type)
                self.instructions.append(instr)
                if target.startswith("id"):
                    self.temp_types[target] = rhs_type
                return target
        elif node.node_type == "op":
            return self._gen_op_without_coercion(node)
        elif node.node_type == "id":
            return f"id{node.value}"
        elif node.node_type == "num":
            return str(node.value)

        return None

    def _gen_op_without_coercion(self, node: ParseNode) -> str:
        """Generate operation code without processing coercions."""
        if len(node.children) == 0:
            return None

        if len(node.children) == 1:
            operand = self._materialize_operand_without_coercion(node.children[0])
            result = self._new_temp()
            result_type = node.type_info if hasattr(node, 'type_info') else None
            instr = TACInstruction(node.value, arg1=operand, result=result, type_info=result_type)
            self.instructions.append(instr)
            self.temp_types[result] = result_type
            return result

        if len(node.children) >= 2:
            left = self._materialize_operand_without_coercion(node.children[0])
            right = self._materialize_operand_without_coercion(node.children[1])
            
            result = self._new_temp()
            result_type = node.type_info if hasattr(node, 'type_info') else None
            op_map = {"+": "+", "-": "-", "*": "*", "/": "/"}
            op = op_map.get(node.value, node.value)

            instr = TACInstruction(op, arg1=left, arg2=right, result=result, type_info=result_type)
            self.instructions.append(instr)
            self.temp_types[result] = result_type
            return result

        return None

    def _gen_assign(self, node: ParseNode) -> str:
        if len(node.children) >= 2:
            target = self._visit(node.children[0], None)
            value = self._materialize_operand(node.children[1])

            # Get type info from RHS 
            rhs_type = node.children[1].type_info if hasattr(node.children[1], 'type_info') else None
            
            instr = TACInstruction("=", arg1=value, result=target, type_info=rhs_type)
            self.instructions.append(instr)
            
            # Track type for this variable
            if target.startswith("id"):
                self.temp_types[target] = rhs_type
            
            return target
        return None

    def _gen_op(self, node: ParseNode) -> str:
        if len(node.children) == 0:
            return None

        if len(node.children) == 1:
            operand = self._materialize_operand(node.children[0])
            result = self._new_temp()
            result_type = node.type_info if hasattr(node, 'type_info') else None
            instr = TACInstruction(node.value, arg1=operand, result=result, type_info=result_type)
            self.instructions.append(instr)
            self.temp_types[result] = result_type
            return result

        if len(node.children) >= 2:
            # Process left and right operands (coercions handled in _visit)
            left = self._materialize_operand(node.children[0])
            right = self._materialize_operand(node.children[1])
            
            result = self._new_temp()
            result_type = node.type_info if hasattr(node, 'type_info') else None

            op_map = {"+": "+", "-": "-", "*": "*", "/": "/"}
            op = op_map.get(node.value, node.value)

            instr = TACInstruction(op, arg1=left, arg2=right, result=result, type_info=result_type)
            self.instructions.append(instr)
            self.temp_types[result] = result_type
            return result

        return None


def generate_intermediate_code(ast: ParseNode) -> List[TACInstruction]:
    generator = IntermediateCodeGenerator(ast)
    return generator.generate()
