from typing import List, Dict
from core.intermediate import TACInstruction


class RegisterAllocator:
    """Manages register allocation for code generation."""
    
    def __init__(self):
        self.registers = {}  # {operand: register}
        self.register_values = {}  # {register: operand}
        self.free_regs = []
        self.next_reg = 0
        self.max_regs = 32  # Maximum registers available
    
    def allocate(self, operand: str) -> str:
        """Allocate or get register for operand."""
        if operand in self.registers:
            return self.registers[operand]

        if self.free_regs:
            reg = self.free_regs.pop(0)
            self.registers[operand] = reg
            self.register_values[reg] = operand
            return reg
        
        if self.next_reg < self.max_regs:
            reg = f"R{self.next_reg}"
            self.next_reg += 1
            self.registers[operand] = reg
            self.register_values[reg] = operand
            return reg
        
        # Spill the first allocated register when no free register exists.
        reg = next(iter(self.register_values.keys()))
        old_operand = self.register_values[reg]
        self.registers.pop(old_operand, None)
        self.registers[operand] = reg
        self.register_values[reg] = operand
        return reg

    def release_operand(self, operand: str):
        """Release register bound to operand so it can be reused."""
        reg = self.registers.pop(operand, None)
        if reg is None:
            return

        self.register_values.pop(reg, None)
        if reg not in self.free_regs:
            self.free_regs.append(reg)
    
    def get_register(self, operand: str) -> str:
        """Get register for operand, allocating if necessary."""
        return self.allocate(operand)
    
    def spill(self, operand: str) -> str:
        """When register is full, spill least recently used."""
        if operand in self.registers:
            return self.registers[operand]
        return self.allocate(operand)


class CodeGenerator:
    def __init__(self, instructions: List[TACInstruction]):
        self.instructions = instructions
        self.assembly: List[str] = []
        self.allocator = RegisterAllocator()
        self.var_locations = {}  # {variable: memory_address}
        self.next_addr = 0
        self.remaining_uses = self._build_remaining_uses()

    def _build_remaining_uses(self) -> Dict[str, int]:
        """Count how many times each operand is used as an input."""
        uses: Dict[str, int] = {}
        for instr in self.instructions:
            if instr.arg1:
                uses[instr.arg1] = uses.get(instr.arg1, 0) + 1
            if instr.arg2:
                uses[instr.arg2] = uses.get(instr.arg2, 0) + 1
        return uses

    def _consume_operand(self, operand: str):
        """Decrement usage count and release register when operand is dead."""
        if not operand or operand not in self.remaining_uses:
            return

        self.remaining_uses[operand] -= 1
        if self.remaining_uses[operand] > 0:
            return

        self.allocator.release_operand(operand)
        if self._is_constant(operand):
            self.allocator.release_operand(f"const_{operand}")

    def generate(self) -> List[str]:
        self.assembly = []

        self.assembly.append("; Generated Floating-Point Assembly Code")
        self.assembly.append("; ========================================")

        for instr in self.instructions:
            self._gen_instruction(instr)

        self.assembly.append("; ========================================")
        return self.assembly

    def _gen_instruction(self, instr: TACInstruction):
        if instr.op == "=":
            self._gen_move(instr)
        elif instr.op == "intfloat":
            self._gen_intfloat(instr)
        elif instr.op in ["+", "-", "*", "/"]:
            self._gen_arithmetic(instr)

        self._consume_operand(instr.arg1)
        self._consume_operand(instr.arg2)

    def _store_if_variable(self, dst: str, src_reg: str):
        """Persist register value to memory when destination is a variable."""
        if dst and dst.startswith("id"):
            self._ensure_var_location(dst)
            mem = self._get_var_location(dst)
            self.assembly.append(f"  STF {mem}, {src_reg}")

    def _gen_move(self, instr: TACInstruction):
        """Generate load/store for assignment."""
        if not instr.result or not instr.arg1:
            return

        # Source operand
        src = instr.arg1
        # Destination operand
        dst = instr.result

        # If source is a constant, load it into a register
        if self._is_constant(src):
            reg = self.allocator.allocate(dst)
            self.assembly.append(f"  MOVF {reg}, {src}")
            self._store_if_variable(dst, reg)
        # If source is a temp, it's in a register
        elif src.startswith("t"):
            src_reg = self.allocator.get_register(src)
            if dst.startswith("id"):
                # Store to memory
                self._store_if_variable(dst, src_reg)
            else:
                # Move between registers
                dst_reg = self.allocator.allocate(dst)
                self.assembly.append(f"  MOVF {dst_reg}, {src_reg}")
        # If source is a variable, load from memory
        elif src.startswith("id"):
            self._ensure_var_location(src)
            mem = self._get_var_location(src)
            reg = self.allocator.allocate(dst)
            self.assembly.append(f"  LDF {reg}, {mem}")
            self._store_if_variable(dst, reg)

    def _gen_intfloat(self, instr: TACInstruction):
        """Generate type conversion instruction."""
        if not instr.result or not instr.arg1:
            return

        src = instr.arg1
        dst = instr.result

        # Allocate register for result
        reg = self.allocator.allocate(dst)

        if self._is_constant(src):
            # Convert constant at load time
            # Convert to float by appending .0 if needed
            float_const = src if "." in str(src) else f"{src}.0"
            self.assembly.append(f"  MOVF {reg}, {float_const}")
        elif src.startswith("t"):
            src_reg = self.allocator.get_register(src)
            # Type conversion - just move between registers
            self.assembly.append(f"  MOVF {reg}, {src_reg}")
        elif src.startswith("id"):
            # Load from memory and convert
            self._ensure_var_location(src)
            mem = self._get_var_location(src)
            self.assembly.append(f"  LDF {reg}, {mem}")

        self._store_if_variable(dst, reg)

    def _gen_arithmetic(self, instr: TACInstruction):
        """Generate floating-point arithmetic instruction."""
        if not instr.result or not instr.arg1 or not instr.arg2:
            return

        left = instr.arg1
        right = instr.arg2
        dst = instr.result

        # Load operands into registers
        left_reg = self._load_operand(left)
        right_reg = self._load_operand(right)
        
        # Allocate result register
        result_reg = self.allocator.allocate(dst)

        # Generate floating-point instruction
        op_map = {
            "+": "ADDF",
            "-": "SUBF",
            "*": "MULF",
            "/": "DIVF",
        }
        op = op_map.get(instr.op, instr.op)

        self.assembly.append(f"  {op} {result_reg}, {left_reg}, {right_reg}")
        self._store_if_variable(dst, result_reg)

    def _load_operand(self, operand: str) -> str:
        """Load operand into a register and return the register."""
        if self._is_constant(operand):
            # Create a temporary register for the constant
            reg = self.allocator.allocate(f"const_{operand}")
            float_const = operand if "." in str(operand) else f"{operand}.0"
            self.assembly.append(f"  MOVF {reg}, {float_const}")
            return reg
        elif operand.startswith("t"):
            # Temp is already in a register
            return self.allocator.get_register(operand)
        elif operand.startswith("id"):
            # Load variable from memory
            self._ensure_var_location(operand)
            mem = self._get_var_location(operand)
            reg = self.allocator.allocate(operand)
            self.assembly.append(f"  LDF {reg}, {mem}")
            return reg
        else:
            # Unknown operand, treat as constant or variable
            return operand

    def _is_constant(self, operand: str) -> bool:
        """Check if operand is a numeric constant."""
        try:
            float(operand)
            return not operand.startswith(("t", "id"))
        except (ValueError, TypeError):
            return False

    def _ensure_var_location(self, var: str):
        """Ensure variable has a memory location assigned."""
        if var not in self.var_locations:
            # Use variable name directly for readability
            self.var_locations[var] = var

    def _get_var_location(self, var: str) -> str:
        """Get memory location for variable."""
        self._ensure_var_location(var)
        return self.var_locations[var]


def generate_code(instructions: List[TACInstruction]) -> List[str]:
    generator = CodeGenerator(instructions)
    return generator.generate()
