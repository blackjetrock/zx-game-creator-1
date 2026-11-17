"""
Self-contained, two-pass Z80 Assembler in pure Python.
Supports standard Z80 mnemonics, expressions, labels, directives (ORG, EQU, DB/DW/DS),
and generates binary machine code.
"""

import re
import os
from typing import Dict, List, Tuple, Optional, Any, Union


# Standard 8-bit register encodings
REG8 = {'B': 0, 'C': 1, 'D': 2, 'E': 3, 'H': 4, 'L': 5, '(HL)': 6, 'A': 7}
REG16_SP = {'BC': 0, 'DE': 1, 'HL': 2, 'SP': 3}
REG16_AF = {'BC': 0, 'DE': 1, 'HL': 2, 'AF': 3}
CONDITIONS = {'NZ': 0, 'Z': 1, 'NC': 2, 'C': 3, 'PO': 4, 'PE': 5, 'P': 6, 'M': 7}
JR_CONDITIONS = {'NZ': 0x20, 'Z': 0x28, 'NC': 0x30, 'C': 0x38}


class AssemblyError(Exception):
    def __init__(self, message: str, line_no: int = 0, line: str = ""):
        self.line_no = line_no
        self.line = line
        super().__init__(f"Line {line_no}: {message} -> '{line}'")


import ast
import operator as op

_AST_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.FloorDiv: op.floordiv, ast.Div: op.floordiv, ast.Mod: op.mod,
    ast.BitAnd: op.and_, ast.BitOr: op.or_, ast.BitXor: op.xor,
    ast.LShift: op.lshift, ast.RShift: op.rshift,
    ast.Invert: op.invert, ast.USub: op.neg, ast.UAdd: op.pos
}


class ExpressionEvaluator:
    """Safe expression evaluator for assembly math, labels, and constants using Python AST."""
    def __init__(self, symbols: Dict[str, int], current_pc: int = 0):
        self.symbols = symbols
        self.current_pc = current_pc

    def _eval_node(self, node: ast.AST) -> int:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return int(node.value)
            elif isinstance(node.value, str) and len(node.value) == 1:
                return ord(node.value)
            return int(node.value)
        elif isinstance(node, ast.Name):
            name = node.id
            if name in self.symbols:
                return self.symbols[name]
            if name.upper() in self.symbols:
                return self.symbols[name.upper()]
            raise NameError(f"Undefined symbol: {name}")
        elif isinstance(node, ast.UnaryOp):
            op_fn = _AST_OPS.get(type(node.op))
            if op_fn:
                return op_fn(self._eval_node(node.operand))
            raise TypeError(f"Unsupported unary operator: {type(node.op)}")
        elif isinstance(node, ast.BinOp):
            op_fn = _AST_OPS.get(type(node.op))
            if op_fn:
                return op_fn(self._eval_node(node.left), self._eval_node(node.right))
            raise TypeError(f"Unsupported binary operator: {type(node.op)}")
        elif isinstance(node, ast.Call):
            func_name = getattr(node.func, 'id', '').upper()
            if not node.args:
                raise ValueError(f"{func_name} expects 1 argument")
            arg_val = self._eval_node(node.args[0])
            if func_name == 'HIGH':
                return (arg_val >> 8) & 0xFF
            elif func_name == 'LOW':
                return arg_val & 0xFF
            raise ValueError(f"Unknown function: {func_name}")
        raise TypeError(f"Unsupported expression syntax: {type(node)}")

    def eval(self, expr_str: str) -> int:
        expr = expr_str.strip()
        if not expr:
            return 0

        # Replace standalone $ with current PC value
        expr = re.sub(r'(?<![\w\$])\$(?![\w\da-fA-F])', str(self.current_pc), expr)
        
        # Replace hex $FF00 with 0xFF00
        expr = re.sub(r'\$([0-9a-fA-F]+)', r'0x\1', expr)
        # Replace hex FF00h or 0FFh with 0xFF00
        expr = re.sub(r'(?<![\w])([0-9][0-9a-fA-F]*)h\b', r'0x\1', expr, flags=re.IGNORECASE)
        # Replace binary %10101010 with 0b10101010
        expr = re.sub(r'%([01]+)', r'0b\1', expr)
        
        # Replace single-quoted characters: 'A' -> 65
        def char_repl(m):
            c = m.group(1)
            val = ord(c[0]) if c else 0
            return str(val)
        expr = re.sub(r"'([^'\\]|\\.)'", char_repl, expr)

        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree.body)
        except Exception as e:
            raise ValueError(f"Cannot evaluate expression '{expr_str}': {e}")


def parse_index_operand(op: str) -> Optional[Tuple[str, str]]:
    """
    Check if operand is (IX+d), (IX-d), (IY+d), (IY-d), (IX), (IY).
    Returns (reg, offset_expr) where reg is 'IX' or 'IY'.
    """
    op = op.strip().upper()
    m = re.match(r'^\(\s*(IX|IY)\s*([+-]\s*[^)]+)?\s*\)$', op)
    if m:
        reg = m.group(1)
        offset = m.group(2)
        if not offset:
            offset = "0"
        else:
            offset = offset.replace(" ", "")
        return (reg, offset)
    return None


def split_operands(ops_str: str) -> List[str]:
    """Split comma-separated operands while respecting quotes and parentheses."""
    res = []
    current = []
    paren_depth = 0
    in_quote = False
    quote_char = ''
    
    for c in ops_str:
        if in_quote:
            current.append(c)
            if c == quote_char:
                in_quote = False
        elif c in ("'", '"'):
            in_quote = True
            quote_char = c
            current.append(c)
        elif c == '(':
            paren_depth += 1
            current.append(c)
        elif c == ')':
            paren_depth -= 1
            current.append(c)
        elif c == ',' and paren_depth == 0:
            res.append("".join(current).strip())
            current = []
        else:
            current.append(c)
            
    if current:
        res.append("".join(current).strip())
    return [r for r in res if r]


class Z80Assembler:
    """Complete two-pass Z80 assembler."""

    def __init__(self, include_dirs: Optional[List[str]] = None):
        self.include_dirs = include_dirs or ["."]
        self.symbols: Dict[str, int] = {}
        self.pc = 0
        self.origin = 0
        self.code = bytearray()
        self.listing: List[str] = []

    def assemble(self, source_text: str, base_dir: str = ".") -> Tuple[bytearray, int, Dict[str, int]]:
        """
        Assemble source code.
        Returns: (binary_bytes, origin_address, symbol_table)
        """
        # Preprocess lines (handle includes, comments, strip whitespace)
        raw_lines = self._preprocess(source_text, base_dir)
        
        # Pass 1: Collect labels and symbols
        self._pass(raw_lines, pass_number=1)
        
        # Pass 2: Generate actual bytes
        self._pass(raw_lines, pass_number=2)
        
        return self.code, self.origin, self.symbols

    def _preprocess(self, text: str, base_dir: str) -> List[Tuple[int, str, str]]:
        """Splits lines, strips comments, handles INCLUDE directives."""
        lines = []
        for line_no, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            # Remove comments (semicolon or //)
            # Take care not to remove semicolons inside quotes
            clean_chars = []
            in_quote = False
            q_char = ''
            for idx, ch in enumerate(line):
                if in_quote:
                    clean_chars.append(ch)
                    if ch == q_char:
                        in_quote = False
                elif ch in ("'", '"'):
                    in_quote = True
                    q_char = ch
                    clean_chars.append(ch)
                elif ch == ';' or (ch == '/' and idx + 1 < len(line) and line[idx+1] == '/'):
                    break
                else:
                    clean_chars.append(ch)
            line = "".join(clean_chars).strip()
            if not line:
                continue
                
            # Check for INCLUDE directive
            m_inc = re.match(r'^(?:include|INCLUDE)\s+["\']([^"\']+)["\']', line)
            if m_inc:
                inc_filename = m_inc.group(1)
                full_path = None
                for d in [base_dir] + self.include_dirs:
                    cand = os.path.join(d, inc_filename)
                    if os.path.isfile(cand):
                        full_path = cand
                        break
                if not full_path:
                    raise AssemblyError(f"Include file not found: {inc_filename}", line_no, raw_line)
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    inc_text = f.read()
                inc_lines = self._preprocess(inc_text, os.path.dirname(full_path))
                lines.extend(inc_lines)
            else:
                lines.append((line_no, line, raw_line))
        return lines

    def _pass(self, lines: List[Tuple[int, str, str]], pass_number: int):
        self.pc = 0
        self.origin = 0
        if pass_number == 2:
            self.code = bytearray()
            self.listing = []
            
        for line_no, line, raw_line in lines:
            try:
                self._assemble_line(line, line_no, raw_line, pass_number)
            except AssemblyError:
                raise
            except Exception as e:
                raise AssemblyError(str(e), line_no, raw_line)

    def _assemble_line(self, line: str, line_no: int, raw_line: str, pass_num: int):
        # Check for label at beginning: label: or label EQU ...
        # Match label definition
        # Label can be "label:" or "label opcode ..." or "label EQU expr"
        label = None
        rest = line
        
        m_label_colon = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):(.*)$', rest)
        if m_label_colon:
            label = m_label_colon.group(1)
            rest = m_label_colon.group(2).strip()
        else:
            # Check for EQU without colon: LABEL EQU val
            m_equ = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:EQU|=)\s+(.*)$', rest, re.IGNORECASE)
            if m_equ:
                label = m_equ.group(1)
                rest = "EQU " + m_equ.group(2).strip()
            else:
                # Check if first word is an identifier and second is opcode or directive
                parts = rest.split(None, 1)
                if len(parts) > 1 and parts[0].upper() not in self._all_mnemonics():
                    # Could be label without colon
                    label = parts[0]
                    rest = parts[1].strip()

        if label:
            if pass_num == 1:
                # Store label address or placeholder
                self.symbols[label] = self.pc
            elif pass_num == 2 and label in self.symbols:
                # Check sanity in pass 2 unless EQU
                if not rest.upper().startswith("EQU"):
                    self.symbols[label] = self.pc

        if not rest:
            return

        # Parse opcode and operands
        parts = rest.split(None, 1)
        mnemonic = parts[0].upper()
        operands_str = parts[1].strip() if len(parts) > 1 else ""
        operands = split_operands(operands_str) if operands_str else []

        evaluator = ExpressionEvaluator(self.symbols, self.pc)

        # Handle Directives
        if mnemonic in ("ORG", ".ORG"):
            val = evaluator.eval(operands[0])
            self.pc = val
            if self.origin == 0:
                self.origin = val
            return

        if mnemonic in ("EQU", ".EQU", "="):
            if not label:
                raise AssemblyError("EQU directive requires a label", line_no, raw_line)
            val = evaluator.eval(operands[0])
            self.symbols[label] = val
            return

        if mnemonic in ("DB", "DEFB", "DEFM", ".BYTE"):
            bytes_out = bytearray()
            for op in operands:
                # Check for string literal
                if (op.startswith('"') and op.endswith('"')) or (op.startswith("'") and op.endswith("'")):
                    content = op[1:-1]
                    # Process escape sequences
                    content = content.encode("utf-8").decode("unicode_escape")
                    bytes_out.extend(content.encode("latin1", errors="replace"))
                else:
                    if pass_num == 1:
                        bytes_out.append(0)
                    else:
                        val = evaluator.eval(op) & 0xFF
                        bytes_out.append(val)
            self._emit(bytes_out, pass_num)
            return

        if mnemonic in ("DW", "DEFW", ".WORD"):
            bytes_out = bytearray()
            for op in operands:
                if pass_num == 1:
                    bytes_out.extend([0, 0])
                else:
                    val = evaluator.eval(op) & 0xFFFF
                    bytes_out.extend([val & 0xFF, (val >> 8) & 0xFF])
            self._emit(bytes_out, pass_num)
            return

        if mnemonic in ("DS", "DEFS", ".BLOCK"):
            if not operands:
                raise AssemblyError("DS requires size operand", line_no, raw_line)
            count = evaluator.eval(operands[0])
            fill = 0
            if len(operands) > 1:
                fill = evaluator.eval(operands[1]) & 0xFF
            bytes_out = bytearray([fill] * count)
            self._emit(bytes_out, pass_num)
            return

        if mnemonic in ("END", ".END"):
            return

        # Encode Instruction
        bytes_out = self._encode_instruction(mnemonic, operands, evaluator, pass_num, line_no, raw_line)
        self._emit(bytes_out, pass_num)

    def _emit(self, bytes_out: bytearray, pass_num: int):
        length = len(bytes_out)
        if pass_num == 2:
            self.code.extend(bytes_out)
        self.pc += length

    def _eval_offset(self, expr_str: str, evaluator: ExpressionEvaluator, pass_num: int) -> int:
        """Evaluate relative jump offset: target - (pc + 2)."""
        if pass_num == 1:
            return 0
        target = evaluator.eval(expr_str)
        offset = target - (self.pc + 2)
        if offset < -128 or offset > 127:
            raise ValueError(f"Relative jump out of range: offset {offset} from ${self.pc:04X} to ${target:04X}")
        return offset & 0xFF

    def _encode_instruction(
        self,
        mnemonic: str,
        ops: List[str],
        evaluator: ExpressionEvaluator,
        pass_num: int,
        line_no: int,
        raw_line: str
    ) -> bytearray:
        """Encode a single Z80 mnemonic into machine code bytes."""
        u_ops = [op.upper() for op in ops]

        # 0-operand instructions
        zero_ops = {
            'NOP': [0x00], 'RLCA': [0x07], 'RRCA': [0x0F], 'RLA': [0x17], 'RRA': [0x1F],
            'DAA': [0x27], 'CPL': [0x2F], 'SCF': [0x37], 'CCF': [0x3F], 'HALT': [0x76],
            'EXX': [0xD9], 'DI': [0xF3], 'EI': [0xFB], 'RET': [0xC9],
            'RETI': [0xED, 0x4D], 'RETN': [0xED, 0x45], 'NEG': [0xED, 0x44],
            'RLD': [0xED, 0x6F], 'RRD': [0xED, 0x67],
            'LDI': [0xED, 0xA0], 'CPI': [0xED, 0xA1], 'INI': [0xED, 0xA2], 'OUTI': [0xED, 0xA3],
            'LDD': [0xED, 0xA8], 'CPD': [0xED, 0xA9], 'IND': [0xED, 0xAA], 'OUTD': [0xED, 0xAB],
            'LDIR': [0xED, 0xB0], 'CPIR': [0xED, 0xB1], 'INIR': [0xED, 0xB2], 'OTIR': [0xED, 0xB3],
            'LDDR': [0xED, 0xB8], 'CPDR': [0xED, 0xB9], 'INDR': [0xED, 0xBA], 'OTDR': [0xED, 0xBB],
        }
        if not ops and mnemonic in zero_ops:
            return bytearray(zero_ops[mnemonic])

        # IM (Interrupt Mode: 0, 1, 2)
        if mnemonic == 'IM':
            mode = evaluator.eval(ops[0]) if pass_num == 2 else 1
            if mode == 0:
                return bytearray([0xED, 0x46])
            elif mode == 1:
                return bytearray([0xED, 0x56])
            elif mode == 2:
                return bytearray([0xED, 0x5E])
            raise AssemblyError(f"Invalid IM mode: {mode}", line_no, raw_line)

        # RET cc
        if mnemonic == 'RET' and len(ops) == 1 and u_ops[0] in CONDITIONS:
            cc = CONDITIONS[u_ops[0]]
            return bytearray([0xC0 | (cc << 3)])

        # RST n
        if mnemonic == 'RST':
            val = evaluator.eval(ops[0]) if pass_num == 2 else 0
            if val in (0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38):
                return bytearray([0xC7 | val])
            raise AssemblyError(f"Invalid RST address: {val}", line_no, raw_line)

        # DJNZ e
        if mnemonic == 'DJNZ':
            off = self._eval_offset(ops[0], evaluator, pass_num)
            return bytearray([0x10, off])

        # JR [cc,] e
        if mnemonic == 'JR':
            if len(ops) == 1:
                off = self._eval_offset(ops[0], evaluator, pass_num)
                return bytearray([0x18, off])
            elif len(ops) == 2 and u_ops[0] in JR_CONDITIONS:
                opcode = JR_CONDITIONS[u_ops[0]]
                off = self._eval_offset(ops[1], evaluator, pass_num)
                return bytearray([opcode, off])
            raise AssemblyError("Invalid JR syntax", line_no, raw_line)

        # JP [cc,] nn / JP (HL) / JP (IX) / JP (IY)
        if mnemonic == 'JP':
            if len(ops) == 1:
                op0 = u_ops[0]
                if op0 in ('(HL)', 'HL'):
                    return bytearray([0xE9])
                elif op0 in ('(IX)', 'IX'):
                    return bytearray([0xDD, 0xE9])
                elif op0 in ('(IY)', 'IY'):
                    return bytearray([0xFD, 0xE9])
                else:
                    nn = evaluator.eval(ops[0]) if pass_num == 2 else 0
                    return bytearray([0xC3, nn & 0xFF, (nn >> 8) & 0xFF])
            elif len(ops) == 2 and u_ops[0] in CONDITIONS:
                cc = CONDITIONS[u_ops[0]]
                nn = evaluator.eval(ops[1]) if pass_num == 2 else 0
                return bytearray([0xC2 | (cc << 3), nn & 0xFF, (nn >> 8) & 0xFF])
            raise AssemblyError("Invalid JP syntax", line_no, raw_line)

        # CALL [cc,] nn
        if mnemonic == 'CALL':
            if len(ops) == 1:
                nn = evaluator.eval(ops[0]) if pass_num == 2 else 0
                return bytearray([0xCD, nn & 0xFF, (nn >> 8) & 0xFF])
            elif len(ops) == 2 and u_ops[0] in CONDITIONS:
                cc = CONDITIONS[u_ops[0]]
                nn = evaluator.eval(ops[1]) if pass_num == 2 else 0
                return bytearray([0xC4 | (cc << 3), nn & 0xFF, (nn >> 8) & 0xFF])
            raise AssemblyError("Invalid CALL syntax", line_no, raw_line)

        # PUSH / POP
        if mnemonic in ('PUSH', 'POP'):
            is_push = (mnemonic == 'PUSH')
            target = u_ops[0]
            if target in REG16_AF:
                idx = REG16_AF[target]
                base = 0xC5 if is_push else 0xC1
                return bytearray([base | (idx << 4)])
            elif target == 'IX':
                return bytearray([0xDD, 0xE5 if is_push else 0xE1])
            elif target == 'IY':
                return bytearray([0xFD, 0xE5 if is_push else 0xE1])
            raise AssemblyError(f"Invalid {mnemonic} operand: {target}", line_no, raw_line)

        # INC / DEC
        if mnemonic in ('INC', 'DEC'):
            is_inc = (mnemonic == 'INC')
            target = u_ops[0]
            # 8-bit registers
            if target in REG8:
                r = REG8[target]
                base = 0x04 if is_inc else 0x05
                return bytearray([base | (r << 3)])
            # 16-bit registers
            elif target in REG16_SP:
                rr = REG16_SP[target]
                base = 0x03 if is_inc else 0x0B
                return bytearray([base | (rr << 4)])
            elif target == 'IX':
                return bytearray([0xDD, 0x23 if is_inc else 0x2B])
            elif target == 'IY':
                return bytearray([0xFD, 0x23 if is_inc else 0x2B])
            # (IX+d) / (IY+d)
            idx_op = parse_index_operand(target)
            if idx_op:
                prefix = 0xDD if idx_op[0] == 'IX' else 0xFD
                d = evaluator.eval(idx_op[1]) & 0xFF if pass_num == 2 else 0
                opcode = 0x34 if is_inc else 0x35
                return bytearray([prefix, opcode, d])
            raise AssemblyError(f"Invalid {mnemonic} operand: {target}", line_no, raw_line)

        # EX instructions
        if mnemonic == 'EX':
            if len(ops) == 2:
                op1, op2 = u_ops[0], u_ops[1]
                if (op1 == 'DE' and op2 == 'HL') or (op1 == 'HL' and op2 == 'DE'):
                    return bytearray([0xEB])
                if (op1 == 'AF' and op2 == "AF'") or (op1 == "AF'" and op2 == 'AF'):
                    return bytearray([0x08])
                if op1 == '(SP)':
                    if op2 == 'HL': return bytearray([0xE3])
                    if op2 == 'IX': return bytearray([0xDD, 0xE3])
                    if op2 == 'IY': return bytearray([0xFD, 0xE3])
            raise AssemblyError("Invalid EX operands", line_no, raw_line)

        # ALU operations: ADD, ADC, SUB, SBC, AND, XOR, OR, CP
        alu_ops = {'ADD': 0, 'ADC': 1, 'SUB': 2, 'SBC': 3, 'AND': 4, 'XOR': 5, 'OR': 6, 'CP': 7}
        if mnemonic in alu_ops:
            alu_idx = alu_ops[mnemonic]
            # Form: ADD A, src  or  ADD src
            if len(ops) == 2 and u_ops[0] == 'A':
                src = ops[1]
                u_src = u_ops[1]
            elif len(ops) == 1 and mnemonic != 'ADD' and mnemonic != 'ADC' and mnemonic != 'SBC':
                src = ops[0]
                u_src = u_ops[0]
            elif len(ops) == 2 and u_ops[0] in ('HL', 'IX', 'IY') and mnemonic in ('ADD', 'ADC', 'SBC'):
                # 16-bit ALU handled below
                src = None
                u_src = None
            elif len(ops) == 1 and mnemonic in ('ADD', 'ADC', 'SBC'):
                src = ops[0]
                u_src = u_ops[0]
            else:
                src = None
                u_src = None

            # 16-bit ADD/ADC/SBC
            if len(ops) == 2 and u_ops[0] in ('HL', 'IX', 'IY'):
                dest = u_ops[0]
                src_reg = u_ops[1]
                if dest == 'HL':
                    if mnemonic == 'ADD' and src_reg in REG16_SP:
                        rr = REG16_SP[src_reg]
                        return bytearray([0x09 | (rr << 4)])
                    elif mnemonic == 'ADC' and src_reg in REG16_SP:
                        rr = REG16_SP[src_reg]
                        return bytearray([0xED, 0x4A | (rr << 4)])
                    elif mnemonic == 'SBC' and src_reg in REG16_SP:
                        rr = REG16_SP[src_reg]
                        return bytearray([0xED, 0x42 | (rr << 4)])
                elif dest == 'IX' and mnemonic == 'ADD':
                    reg_map = {'BC': 0, 'DE': 1, 'IX': 2, 'SP': 3}
                    if src_reg in reg_map:
                        return bytearray([0xDD, 0x09 | (reg_map[src_reg] << 4)])
                elif dest == 'IY' and mnemonic == 'ADD':
                    reg_map = {'BC': 0, 'DE': 1, 'IY': 2, 'SP': 3}
                    if src_reg in reg_map:
                        return bytearray([0xFD, 0x09 | (reg_map[src_reg] << 4)])
                raise AssemblyError(f"Invalid 16-bit {mnemonic} operands", line_no, raw_line)

            if src is not None:
                # 8-bit register ALU
                if u_src in REG8:
                    r = REG8[u_src]
                    return bytearray([0x80 | (alu_idx << 3) | r])
                # Index register: (IX+d) / (IY+d)
                idx_op = parse_index_operand(u_src)
                if idx_op:
                    prefix = 0xDD if idx_op[0] == 'IX' else 0xFD
                    d = evaluator.eval(idx_op[1]) & 0xFF if pass_num == 2 else 0
                    return bytearray([prefix, 0x86 | (alu_idx << 3), d])
                # Immediate ALU
                n = evaluator.eval(src) & 0xFF if pass_num == 2 else 0
                return bytearray([0xC6 | (alu_idx << 3), n])

        # Bit operations: BIT, SET, RES
        if mnemonic in ('BIT', 'RES', 'SET'):
            if len(ops) != 2:
                raise AssemblyError(f"{mnemonic} requires 2 operands (bit, target)", line_no, raw_line)
            bit = evaluator.eval(ops[0]) if pass_num == 2 else 0
            if bit < 0 or bit > 7:
                raise AssemblyError(f"Bit index must be 0..7: {bit}", line_no, raw_line)
            target = u_ops[1]
            base_map = {'BIT': 0x40, 'RES': 0x80, 'SET': 0xC0}
            base = base_map[mnemonic] | (bit << 3)

            if target in REG8:
                r = REG8[target]
                return bytearray([0xCB, base | r])
            idx_op = parse_index_operand(target)
            if idx_op:
                prefix = 0xDD if idx_op[0] == 'IX' else 0xFD
                d = evaluator.eval(idx_op[1]) & 0xFF if pass_num == 2 else 0
                return bytearray([prefix, 0xCB, d, base | 6])
            raise AssemblyError(f"Invalid {mnemonic} target: {target}", line_no, raw_line)

        # Shifts and Rotates: RLC, RRC, RL, RR, SLA, SRA, SRL, SLL
        shift_ops = {'RLC': 0x00, 'RRC': 0x08, 'RL': 0x10, 'RR': 0x18, 'SLA': 0x20, 'SRA': 0x28, 'SLL': 0x30, 'SRL': 0x38}
        if mnemonic in shift_ops:
            base = shift_ops[mnemonic]
            target = u_ops[0]
            if target in REG8:
                r = REG8[target]
                return bytearray([0xCB, base | r])
            idx_op = parse_index_operand(target)
            if idx_op:
                prefix = 0xDD if idx_op[0] == 'IX' else 0xFD
                d = evaluator.eval(idx_op[1]) & 0xFF if pass_num == 2 else 0
                return bytearray([prefix, 0xCB, d, base | 6])
            raise AssemblyError(f"Invalid {mnemonic} operand: {target}", line_no, raw_line)

        # IN / OUT
        if mnemonic == 'IN':
            if len(ops) == 2:
                dest = u_ops[0]
                port = u_ops[1]
                if dest == 'A' and port.startswith('(') and port.endswith(')'):
                    inner = port[1:-1].strip()
                    if inner == 'C':
                        return bytearray([0xED, 0x78])
                    n = evaluator.eval(inner) & 0xFF if pass_num == 2 else 0
                    return bytearray([0xDB, n])
                elif port == '(C)' and dest in REG8:
                    r = REG8[dest]
                    return bytearray([0xED, 0x40 | (r << 3)])
            raise AssemblyError("Invalid IN instruction syntax", line_no, raw_line)

        if mnemonic == 'OUT':
            if len(ops) == 2:
                port = u_ops[0]
                src = u_ops[1]
                if port.startswith('(') and port.endswith(')'):
                    inner = port[1:-1].strip()
                    if inner == 'C' and src in REG8:
                        r = REG8[src]
                        return bytearray([0xED, 0x41 | (r << 3)])
                    elif src == 'A':
                        n = evaluator.eval(inner) & 0xFF if pass_num == 2 else 0
                        return bytearray([0xD3, n])
            raise AssemblyError("Invalid OUT instruction syntax", line_no, raw_line)

        # LD instructions
        if mnemonic == 'LD':
            if len(ops) != 2:
                raise AssemblyError("LD instruction requires 2 operands", line_no, raw_line)
            dst, src = ops[0], ops[1]
            u_dst, u_src = u_ops[0], u_ops[1]

            # Special registers I, R
            if u_dst == 'A' and u_src == 'I': return bytearray([0xED, 0x57])
            if u_dst == 'A' and u_src == 'R': return bytearray([0xED, 0x5F])
            if u_dst == 'I' and u_src == 'A': return bytearray([0xED, 0x47])
            if u_dst == 'R' and u_src == 'A': return bytearray([0xED, 0x4F])

            # SP loads
            if u_dst == 'SP' and u_src == 'HL': return bytearray([0xF9])
            if u_dst == 'SP' and u_src == 'IX': return bytearray([0xDD, 0xF9])
            if u_dst == 'SP' and u_src == 'IY': return bytearray([0xFD, 0xF9])

            # Direct register-indirect byte loads: LD A, (BC) / LD A, (DE) / LD (BC), A / LD (DE), A
            if u_dst == 'A' and u_src == '(BC)': return bytearray([0x0A])
            if u_dst == 'A' and u_src == '(DE)': return bytearray([0x1A])
            if u_dst == '(BC)' and u_src == 'A': return bytearray([0x02])
            if u_dst == '(DE)' and u_src == 'A': return bytearray([0x12])

            # LD (HL), n
            if u_dst == '(HL)':
                if u_src in REG8 and u_src != '(HL)':
                    rs = REG8[u_src]
                    return bytearray([0x70 | rs])
                n = evaluator.eval(src) & 0xFF if pass_num == 2 else 0
                return bytearray([0x36, n])

            # Check index operand in dst or src
            idx_dst = parse_index_operand(u_dst)
            idx_src = parse_index_operand(u_src)

            # LD r, (IX+d)
            if u_dst in REG8 and u_dst != '(HL)' and idx_src:
                r = REG8[u_dst]
                prefix = 0xDD if idx_src[0] == 'IX' else 0xFD
                d = evaluator.eval(idx_src[1]) & 0xFF if pass_num == 2 else 0
                return bytearray([prefix, 0x46 | (r << 3), d])

            # LD (IX+d), r
            if idx_dst and u_src in REG8 and u_src != '(HL)':
                r = REG8[u_src]
                prefix = 0xDD if idx_dst[0] == 'IX' else 0xFD
                d = evaluator.eval(idx_dst[1]) & 0xFF if pass_num == 2 else 0
                return bytearray([prefix, 0x70 | r, d])

            # LD (IX+d), n
            if idx_dst:
                prefix = 0xDD if idx_dst[0] == 'IX' else 0xFD
                d = evaluator.eval(idx_dst[1]) & 0xFF if pass_num == 2 else 0
                n = evaluator.eval(src) & 0xFF if pass_num == 2 else 0
                return bytearray([prefix, 0x36, d, n])

            # LD IX/IY, nn / LD IX/IY, (nn)
            if u_dst == 'IX':
                if u_src.startswith('(') and u_src.endswith(')'):
                    nn = evaluator.eval(u_src[1:-1]) if pass_num == 2 else 0
                    return bytearray([0xDD, 0x2A, nn & 0xFF, (nn >> 8) & 0xFF])
                nn = evaluator.eval(src) if pass_num == 2 else 0
                return bytearray([0xDD, 0x21, nn & 0xFF, (nn >> 8) & 0xFF])
            if u_dst == 'IY':
                if u_src.startswith('(') and u_src.endswith(')'):
                    nn = evaluator.eval(u_src[1:-1]) if pass_num == 2 else 0
                    return bytearray([0xFD, 0x2A, nn & 0xFF, (nn >> 8) & 0xFF])
                nn = evaluator.eval(src) if pass_num == 2 else 0
                return bytearray([0xFD, 0x21, nn & 0xFF, (nn >> 8) & 0xFF])

            # LD (nn), IX/IY
            if u_src in ('IX', 'IY') and u_dst.startswith('(') and u_dst.endswith(')'):
                prefix = 0xDD if u_src == 'IX' else 0xFD
                nn = evaluator.eval(u_dst[1:-1]) if pass_num == 2 else 0
                return bytearray([prefix, 0x22, nn & 0xFF, (nn >> 8) & 0xFF])

            # LD r, r'
            if u_dst in REG8 and u_src in REG8:
                if u_dst == '(HL)' and u_src == '(HL)':
                    raise AssemblyError("Invalid instruction: LD (HL), (HL)", line_no, raw_line)
                rd = REG8[u_dst]
                rs = REG8[u_src]
                return bytearray([0x40 | (rd << 3) | rs])

            # LD A, (nn) / LD (nn), A
            if u_dst == 'A' and u_src.startswith('(') and u_src.endswith(')'):
                nn = evaluator.eval(u_src[1:-1]) if pass_num == 2 else 0
                return bytearray([0x3A, nn & 0xFF, (nn >> 8) & 0xFF])
            if u_dst.startswith('(') and u_dst.endswith(')') and u_src == 'A':
                nn = evaluator.eval(u_dst[1:-1]) if pass_num == 2 else 0
                return bytearray([0x32, nn & 0xFF, (nn >> 8) & 0xFF])

            # 16-bit register loads: LD rr, (nn) / LD rr, nn
            if u_dst in REG16_SP:
                rr = REG16_SP[u_dst]
                if u_src.startswith('(') and u_src.endswith(')'):
                    nn = evaluator.eval(u_src[1:-1]) if pass_num == 2 else 0
                    if u_dst == 'HL':
                        return bytearray([0x2A, nn & 0xFF, (nn >> 8) & 0xFF])
                    else:
                        return bytearray([0xED, 0x4B | (rr << 4), nn & 0xFF, (nn >> 8) & 0xFF])
                nn = evaluator.eval(src) if pass_num == 2 else 0
                return bytearray([0x01 | (rr << 4), nn & 0xFF, (nn >> 8) & 0xFF])

            # 16-bit register store: LD (nn), rr
            if u_dst.startswith('(') and u_dst.endswith(')'):
                nn_expr = u_dst[1:-1].strip()
                if u_src in REG16_SP:
                    rr = REG16_SP[u_src]
                    nn = evaluator.eval(nn_expr) if pass_num == 2 else 0
                    if u_src == 'HL':
                        return bytearray([0x22, nn & 0xFF, (nn >> 8) & 0xFF])
                    else:
                        return bytearray([0xED, 0x43 | (rr << 4), nn & 0xFF, (nn >> 8) & 0xFF])

            # LD r, n
            if u_dst in REG8 and u_dst != '(HL)':
                rd = REG8[u_dst]
                n = evaluator.eval(src) & 0xFF if pass_num == 2 else 0
                return bytearray([0x06 | (rd << 3), n])

        raise AssemblyError(f"Unrecognized or unsupported instruction: {mnemonic} {', '.join(ops)}", line_no, raw_line)

    def _all_mnemonics(self):
        return {
            'NOP', 'RLCA', 'RRCA', 'RLA', 'RRA', 'DAA', 'CPL', 'SCF', 'CCF', 'HALT',
            'EXX', 'DI', 'EI', 'RET', 'RETI', 'RETN', 'NEG', 'RLD', 'RRD',
            'LDI', 'CPI', 'INI', 'OUTI', 'LDD', 'CPD', 'IND', 'OUTD',
            'LDIR', 'CPIR', 'INIR', 'OTIR', 'LDDR', 'CPDR', 'INDR', 'OTDR',
            'IM', 'RST', 'DJNZ', 'JR', 'JP', 'CALL', 'PUSH', 'POP', 'INC', 'DEC',
            'EX', 'ADD', 'ADC', 'SUB', 'SBC', 'AND', 'XOR', 'OR', 'CP',
            'BIT', 'RES', 'SET', 'RLC', 'RRC', 'RL', 'RR', 'SLA', 'SRA', 'SLL', 'SRL',
            'IN', 'OUT', 'LD', 'ORG', 'EQU', 'DB', 'DEFB', 'DEFM', 'DW', 'DEFW', 'DS', 'DEFS', 'END'
        }
