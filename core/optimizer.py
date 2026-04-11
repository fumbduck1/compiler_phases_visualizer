from typing import List, Dict, Set, Optional
from core.intermediate import TACInstruction


class Optimizer:
    def __init__(self, instructions: List[TACInstruction]):
        self.instructions = instructions
        self.temp_uses = {}  # Track uses of each temp/variable

    @staticmethod
    def _clone_instruction(instr: TACInstruction) -> TACInstruction:
        return TACInstruction(
            op=instr.op,
            arg1=instr.arg1,
            arg2=instr.arg2,
            result=instr.result,
            type_info=instr.type_info,
        )

    def _clone_instructions(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        return [self._clone_instruction(instr) for instr in instructions]

    def optimize(self) -> List[TACInstruction]:
        # Run optimization passes
        optimized = self._clone_instructions(self.instructions)
        optimized = self._constant_folding(optimized)
        optimized = self._operation_compacting(optimized)
        optimized = self._copy_propagation(optimized)
        optimized = self._dead_code_elimination(optimized)
        return optimized

    def _copy_propagation(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Collapse temporary copy chains such as `tN = ...; idX = tN` when safe."""
        if not instructions:
            return instructions

        uses = {}
        for instr in instructions:
            if instr.arg1:
                uses[instr.arg1] = uses.get(instr.arg1, 0) + 1
            if instr.arg2:
                uses[instr.arg2] = uses.get(instr.arg2, 0) + 1

        optimized = []
        i = 0
        while i < len(instructions):
            current = instructions[i]

            # Pattern: tN = a op b ; idX = tN  ->  idX = a op b
            if (
                i + 1 < len(instructions)
                and current.result
                and current.result.startswith("t")
                and current.op != "="
                and uses.get(current.result, 0) == 1
            ):
                nxt = instructions[i + 1]
                if (
                    nxt.op == "="
                    and nxt.arg1 == current.result
                    and nxt.result
                    and nxt.result.startswith("id")
                ):
                    merged = TACInstruction(
                        op=current.op,
                        arg1=current.arg1,
                        arg2=current.arg2,
                        result=nxt.result,
                        type_info=current.type_info,
                    )
                    optimized.append(merged)
                    i += 2
                    continue

            optimized.append(current)
            i += 1

        return optimized

    def _constant_folding(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Evaluate constant expressions and fold them."""
        optimized = []
        constants = {}  # Track constant values: {result: value}

        for instr in instructions:
            # Check if this is a constant expression
            if instr.op in ["+", "-", "*", "/"] and instr.arg1 and instr.arg2:
                try:
                    left = float(instr.arg1) if "." in str(instr.arg1) else int(instr.arg1)
                    right = float(instr.arg2) if "." in str(instr.arg2) else int(instr.arg2)

                    result = None
                    if instr.op == "+":
                        result = left + right
                    elif instr.op == "-":
                        result = left - right
                    elif instr.op == "*":
                        result = left * right
                    elif instr.op == "/" and right != 0:
                        result = left / right

                    if result is not None:
                        # Store constant and optimize
                        constants[instr.result] = result
                        result_val = str(int(result) if result == int(result) else result)
                        new_instr = TACInstruction(
                            "=",
                            arg1=result_val,
                            result=instr.result,
                            type_info=instr.type_info,
                        )
                        optimized.append(new_instr)
                        continue
                except (ValueError, TypeError):
                    pass

            # Check if we can resolve constants
            arg1 = str(constants[instr.arg1]) if instr.arg1 and instr.arg1 in constants else instr.arg1
            arg2 = str(constants[instr.arg2]) if instr.arg2 and instr.arg2 in constants else instr.arg2

            if arg1 != instr.arg1 or arg2 != instr.arg2:
                instr = TACInstruction(
                    op=instr.op,
                    arg1=arg1,
                    arg2=arg2,
                    result=instr.result,
                    type_info=instr.type_info,
                )

            # Handle intfloat() of constants
            if instr.op == "intfloat":
                try:
                    const_val = float(instr.arg1) if "." in str(instr.arg1) else int(instr.arg1)
                    # Mark as constant
                    constants[instr.result] = float(const_val)
                except (ValueError, TypeError):
                    pass

            optimized.append(instr)

        return optimized

    def _operation_compacting(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Compact operations by removing intermediate temps when possible."""
        optimized = []
        temp_defs = {}  # {temp: instruction that defines it}
        temp_uses = {}  # {temp: list of instructions that use it}

        # Build usage maps
        for i, instr in enumerate(instructions):
            if instr.result:
                temp_defs[instr.result] = i
            if instr.arg1:
                if instr.arg1 not in temp_uses:
                    temp_uses[instr.arg1] = []
                temp_uses[instr.arg1].append(i)
            if instr.arg2:
                if instr.arg2 not in temp_uses:
                    temp_uses[instr.arg2] = []
                temp_uses[instr.arg2].append(i)

        # Skip redundant temps that are used only once
        skip_temps = set()
        for temp, def_idx in temp_defs.items():
            if temp.startswith("t"):  # Only skip internal temps
                uses = temp_uses.get(temp, [])
                # If used only once and not in assignment target, can inline
                if len(uses) == 1:
                    use_idx = uses[0]
                    def_instr = instructions[def_idx]
                    use_instr = instructions[use_idx]
                    
                    # Can inline if definition is simple (not storing to variable)
                    if (def_instr.op in ["intfloat", "="] and 
                        not def_instr.result.startswith("id") and
                        use_idx == def_idx + 1):  # Consecutive instructions
                        skip_temps.add(temp)

        # Regenerate with compacting
        for i, instr in enumerate(instructions):
            # Skip if this temp is defined but not really used
            if instr.result in skip_temps and instr.result not in temp_uses:
                continue
            
            # Inline args if they're skipped temps
            if instr.arg1 in skip_temps and instr.arg1 in temp_defs:
                source_instr = instructions[temp_defs[instr.arg1]]
                if source_instr.arg1:
                    instr.arg1 = source_instr.arg1
            
            if instr.arg2 in skip_temps and instr.arg2 in temp_defs:
                source_instr = instructions[temp_defs[instr.arg2]]
                if source_instr.arg1:
                    instr.arg2 = source_instr.arg1

            optimized.append(instr)

        return optimized

    def _dead_code_elimination(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Remove assignments to temps that are never used."""
        optimized = []
        temp_uses = {}

        # Build usage map
        for instr in instructions:
            if instr.arg1 and instr.arg1.startswith("t"):
                temp_uses[instr.arg1] = temp_uses.get(instr.arg1, 0) + 1
            if instr.arg2 and instr.arg2.startswith("t"):
                temp_uses[instr.arg2] = temp_uses.get(instr.arg2, 0) + 1

        # Filter out dead assignments
        for instr in instructions:
            # Keep assignments to variables (id*)
            if instr.result and instr.result.startswith("id"):
                optimized.append(instr)
            # Keep other instructions
            elif instr.op in ["intfloat"]:
                optimized.append(instr)
            # Keep if the result is used
            elif instr.result in temp_uses and temp_uses[instr.result] > 0:
                optimized.append(instr)

        return optimized


def optimize(instructions: List[TACInstruction]) -> List[TACInstruction]:
    optimizer = Optimizer(instructions)
    return optimizer.optimize()
