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
        if self.result:
            if self.op == "=" and self.arg1 is not None:
                return f"{self.result} = {self.arg1}"
            if self.arg2:
                return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
            elif self.arg1:
                return f"{self.result} = {self.op}({self.arg1})"
            return f"{self.result} = {self.op}"

        if self.op == "label" and self.arg1:
            return f"label {self.arg1}"
        if self.op in {"jmp", "return", "error"}:
            return f"{self.op} {self.arg1}" if self.arg1 is not None else self.op
        if self.op in {"jz", "jnz"}:
            return f"{self.op} {self.arg1} {self.arg2}"
        if self.arg1 is not None and self.arg2 is not None:
            return f"{self.op} {self.arg1} {self.arg2}"
        if self.arg1 is not None:
            return f"{self.op} {self.arg1}"
        return self.op

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
        self.label_counter = 0
        self.loop_stack: List[tuple[str, str]] = []

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

    def _new_label(self, prefix: str = "L") -> str:
        self.label_counter += 1
        return f"{prefix}{self.label_counter}"

    def _emit(self, op: str, arg1=None, arg2=None, result=None, type_info=None):
        instr = TACInstruction(op, arg1=arg1, arg2=arg2, result=result, type_info=type_info)
        self.instructions.append(instr)
        return instr

    def _visit(self, node: ParseNode, result: Optional[str]) -> Optional[str]:
        if node is None:
            return None

        # If this node has a coercion, emit it first and return the converted value
        if hasattr(node, 'coercion') and node.coercion:
            return self._handle_coercion(node)

        if node.node_type in {"program", "block"}:
            for child in node.children:
                self._visit(child, None)
            return None
        if node.node_type == "declaration":
            return self._gen_declaration(node)
        if node.node_type == "for":
            return self._gen_for(node)
        if node.node_type == "while":
            return self._gen_while(node)
        if node.node_type == "if":
            return self._gen_if(node)
        if node.node_type == "return":
            return self._gen_return(node)
        if node.node_type == "break":
            return self._gen_break()
        if node.node_type == "continue":
            return self._gen_continue()
        if node.node_type == "empty":
            return None
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

    def _gen_declaration(self, node: ParseNode) -> Optional[str]:
        if not node.children:
            return None

        target = self._visit(node.children[0], None)
        if len(node.children) > 1:
            value = self._materialize_operand(node.children[1])
            rhs_type = node.children[1].type_info if hasattr(node.children[1], "type_info") else None
            self._emit("=", arg1=value, result=target, type_info=rhs_type)
            if target and target.startswith("id"):
                self.temp_types[target] = rhs_type
        return target

    def _gen_for(self, node: ParseNode) -> Optional[str]:
        init = node.children[0] if len(node.children) > 0 else None
        cond = node.children[1] if len(node.children) > 1 else None
        incr = node.children[2] if len(node.children) > 2 else None
        body = node.children[3] if len(node.children) > 3 else None

        cond_label = self._new_label("for_cond_")
        body_label = self._new_label("for_body_")
        step_label = self._new_label("for_step_")
        end_label = self._new_label("for_end_")

        if init:
            self._visit(init, None)

        self._emit("label", arg1=cond_label)

        if cond and cond.node_type != "empty":
            cond_result = self._materialize_operand(cond)
            self._emit("jz", arg1=cond_result, arg2=end_label)

        self._emit("label", arg1=body_label)

        self.loop_stack.append((step_label, end_label))
        if body:
            self._visit(body, None)

        self._emit("label", arg1=step_label)
        if incr and incr.node_type != "empty":
            self._visit(incr, None)

        self._emit("jmp", arg1=cond_label)
        self._emit("label", arg1=end_label)
        self.loop_stack.pop()
        return None

    def _gen_while(self, node: ParseNode) -> Optional[str]:
        cond = node.children[0] if len(node.children) > 0 else None
        body = node.children[1] if len(node.children) > 1 else None

        start_label = self._new_label("while_start_")
        end_label = self._new_label("while_end_")

        self._emit("label", arg1=start_label)
        if cond and cond.node_type != "empty":
            cond_result = self._materialize_operand(cond)
            self._emit("jz", arg1=cond_result, arg2=end_label)

        self.loop_stack.append((start_label, end_label))
        if body:
            self._visit(body, None)
        self._emit("jmp", arg1=start_label)
        self._emit("label", arg1=end_label)
        self.loop_stack.pop()
        return None

    def _gen_if(self, node: ParseNode) -> Optional[str]:
        cond = node.children[0] if len(node.children) > 0 else None
        then_branch = node.children[1] if len(node.children) > 1 else None
        else_branch = node.children[2] if len(node.children) > 2 else None

        else_label = self._new_label("if_else_")
        end_label = self._new_label("if_end_")

        if cond and cond.node_type != "empty":
            cond_result = self._materialize_operand(cond)
            self._emit("jz", arg1=cond_result, arg2=else_label)

        if then_branch:
            self._visit(then_branch, None)

        self._emit("jmp", arg1=end_label)
        self._emit("label", arg1=else_label)
        if else_branch:
            self._visit(else_branch, None)
        self._emit("label", arg1=end_label)
        return None

    def _gen_return(self, node: ParseNode) -> Optional[str]:
        if node.children:
            value = self._materialize_operand(node.children[0])
            self._emit("return", arg1=value)
        else:
            self._emit("return")
        return None

    def _gen_break(self) -> Optional[str]:
        if not self.loop_stack:
            self._emit("error", arg1="break outside loop")
            return None
        _, break_label = self.loop_stack[-1]
        self._emit("jmp", arg1=break_label)
        return None

    def _gen_continue(self) -> Optional[str]:
        if not self.loop_stack:
            self._emit("error", arg1="continue outside loop")
            return None
        continue_label, _ = self.loop_stack[-1]
        self._emit("jmp", arg1=continue_label)
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
            result = self._new_temp()
            result_type = node.type_info if hasattr(node, 'type_info') else None
            if node.value in {"++", "--"}:
                child = node.children[0]
                if child.node_type == "id":
                    operand = self._visit_without_coercion(child)
                else:
                    operand = self._materialize_operand_without_coercion(child)
                op = "+" if node.value == "++" else "-"
                instr = TACInstruction(op, arg1=operand, arg2="1", result=operand, type_info=result_type)
                self.instructions.append(instr)
                self.temp_types[operand] = result_type
                return operand
            operand = self._materialize_operand_without_coercion(node.children[0])
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
            result_type = node.type_info if hasattr(node, 'type_info') else None
            if node.value in {"++", "--"}:
                child = node.children[0]
                if child.node_type == "id":
                    operand = self._visit(child, None)
                else:
                    operand = self._materialize_operand(child)
                op = "+" if node.value == "++" else "-"
                instr = TACInstruction(op, arg1=operand, arg2="1", result=operand, type_info=result_type)
                self.instructions.append(instr)
                self.temp_types[operand] = result_type
                return operand

            operand = self._materialize_operand(node.children[0])
            result = self._new_temp()
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

            op_map = {
                "+": "+",
                "-": "-",
                "*": "*",
                "/": "/",
                "%": "%",
                "<": "<",
                "<=": "<=",
                ">": ">",
                ">=": ">=",
                "==": "==",
                "!=": "!=",
                "&&": "&&",
                "||": "||",
            }
            op = op_map.get(node.value, node.value)

            instr = TACInstruction(op, arg1=left, arg2=right, result=result, type_info=result_type)
            self.instructions.append(instr)
            self.temp_types[result] = result_type
            return result

        return None


def generate_intermediate_code(ast: ParseNode) -> List[TACInstruction]:
    generator = IntermediateCodeGenerator(ast)
    return generator.generate()
