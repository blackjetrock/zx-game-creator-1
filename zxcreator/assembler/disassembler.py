"""
ZX Spectrum / Z80 Disassembler for inspecting compiled machine code.
"""

from typing import List, Tuple, Dict, Optional

# Basic single-byte instruction map
_OPCODES_MAIN = {
    0x00: "NOP", 0x07: "RLCA", 0x0F: "RRCA", 0x17: "RLA", 0x1F: "RRA",
    0x27: "DAA", 0x2F: "CPL", 0x37: "SCF", 0x3F: "CCF", 0x76: "HALT",
    0xC9: "RET", 0xD9: "EXX", 0xE3: "EX (SP), HL", 0xE9: "JP (HL)",
    0xEB: "EX DE, HL", 0xF3: "DI", 0xF9: "LD SP, HL", 0xFB: "EI",
}

_R8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
_R16 = ["BC", "DE", "HL", "SP"]
_R16_AF = ["BC", "DE", "HL", "AF"]
_CC = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]
_ALU = ["ADD A,", "ADC A,", "SUB", "SBC A,", "AND", "XOR", "OR", "CP"]


def disassemble_one(data: bytes, pc: int) -> Tuple[str, int]:
    """Disassemble a single instruction from data at relative offset pc. Returns (text, byte_count)."""
    if pc >= len(data):
        return ("EOF", 0)

    b0 = data[pc]
    
    # 0xCB Prefix (Bit operations)
    if b0 == 0xCB:
        if pc + 1 >= len(data): return (f"DB $CB", 1)
        b1 = data[pc + 1]
        r = _R8[b1 & 0x07]
        bit = (b1 >> 3) & 0x07
        cat = b1 >> 6
        if cat == 0:
            rot_ops = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", "SLL", "SRL"]
            return (f"{rot_ops[bit]} {r}", 2)
        elif cat == 1:
            return (f"BIT {bit}, {r}", 2)
        elif cat == 2:
            return (f"RES {bit}, {r}", 2)
        else:
            return (f"SET {bit}, {r}", 2)

    # 0xED Prefix (Extended)
    if b0 == 0xED:
        if pc + 1 >= len(data): return (f"DB $ED", 1)
        b1 = data[pc + 1]
        ed_ops = {
            0x44: "NEG", 0x45: "RETN", 0x46: "IM 0", 0x47: "LD I, A",
            0x4D: "RETI", 0x4F: "LD R, A", 0x56: "IM 1", 0x57: "LD A, I",
            0x5E: "IM 2", 0x5F: "LD A, R", 0x67: "RRD", 0x6F: "RLD",
            0xA0: "LDI", 0xA1: "CPI", 0xA2: "INI", 0xA3: "OUTI",
            0xA8: "LDD", 0xA9: "CPD", 0xAA: "IND", 0xAB: "OUTD",
            0xB0: "LDIR", 0xB1: "CPIR", 0xB2: "INIR", 0xB3: "OTIR",
            0xB8: "LDDR", 0xB9: "CPDR", 0xBA: "INDR", 0xBB: "OTDR",
        }
        if b1 in ed_ops:
            return (ed_ops[b1], 2)
        # 16-bit loads with (nn)
        if (b1 & 0xC7) == 0x4B and pc + 3 < len(data):
            rr = _R16[(b1 >> 4) & 0x03]
            nn = data[pc+2] | (data[pc+3] << 8)
            return (f"LD {rr}, (${nn:04X})", 4)
        if (b1 & 0xC7) == 0x43 and pc + 3 < len(data):
            rr = _R16[(b1 >> 4) & 0x03]
            nn = data[pc+2] | (data[pc+3] << 8)
            return (f"LD (${nn:04X}), {rr}", 4)
        return (f"DB $ED, ${b1:02X}", 2)

    # 0xDD / 0xFD (IX / IY)
    if b0 in (0xDD, 0xFD):
        reg = "IX" if b0 == 0xDD else "IY"
        if pc + 1 >= len(data): return (f"DB ${b0:02X}", 1)
        b1 = data[pc + 1]
        if b1 == 0x21 and pc + 3 < len(data):
            nn = data[pc+2] | (data[pc+3] << 8)
            return (f"LD {reg}, ${nn:04X}", 4)
        if b1 == 0xE5: return (f"PUSH {reg}", 2)
        if b1 == 0xE1: return (f"POP {reg}", 2)
        if b1 == 0xE9: return (f"JP ({reg})", 2)
        if b1 == 0x23: return (f"INC {reg}", 2)
        if b1 == 0x2B: return (f"DEC {reg}", 2)
        if b1 == 0x36 and pc + 3 < len(data):
            d = data[pc+2]
            n = data[pc+3]
            offset = d if d < 128 else d - 256
            sign = "+" if offset >= 0 else ""
            return (f"LD ({reg}{sign}{offset}), ${n:02X}", 4)
        if (b1 & 0xF8) == 0x70 and pc + 2 < len(data):
            r = _R8[b1 & 0x07]
            d = data[pc+2]
            offset = d if d < 128 else d - 256
            sign = "+" if offset >= 0 else ""
            return (f"LD ({reg}{sign}{offset}), {r}", 3)
        if (b1 & 0xC7) == 0x46 and pc + 2 < len(data):
            r = _R8[(b1 >> 3) & 0x07]
            d = data[pc+2]
            offset = d if d < 128 else d - 256
            sign = "+" if offset >= 0 else ""
            return (f"LD {r}, ({reg}{sign}{offset})", 3)
        return (f"DB ${b0:02X}, ${b1:02X}", 2)

    # Main Instruction Set
    if b0 in _OPCODES_MAIN:
        return (_OPCODES_MAIN[b0], 1)

    # DJNZ e
    if b0 == 0x10 and pc + 1 < len(data):
        e = data[pc + 1]
        off = e if e < 128 else e - 256
        return (f"DJNZ ${pc + 2 + off:04X}", 2)

    # JR e / JR cc, e
    if b0 == 0x18 and pc + 1 < len(data):
        e = data[pc + 1]
        off = e if e < 128 else e - 256
        return (f"JR ${pc + 2 + off:04X}", 2)
    if (b0 & 0xE7) == 0x20 and pc + 1 < len(data):
        cc = _CC[(b0 >> 3) & 0x03]
        e = data[pc + 1]
        off = e if e < 128 else e - 256
        return (f"JR {cc}, ${pc + 2 + off:04X}", 2)

    # LD rr, nn
    if (b0 & 0xCF) == 0x01 and pc + 2 < len(data):
        rr = _R16[(b0 >> 4) & 0x03]
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"LD {rr}, ${nn:04X}", 3)

    # LD (BC/DE), A
    if b0 == 0x02: return ("LD (BC), A", 1)
    if b0 == 0x12: return ("LD (DE), A", 1)
    if b0 == 0x0A: return ("LD A, (BC)", 1)
    if b0 == 0x1A: return ("LD A, (DE)", 1)

    # LD (nn), HL / LD HL, (nn) / LD (nn), A / LD A, (nn)
    if b0 == 0x22 and pc + 2 < len(data):
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"LD (${nn:04X}), HL", 3)
    if b0 == 0x2A and pc + 2 < len(data):
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"LD HL, (${nn:04X})", 3)
    if b0 == 0x32 and pc + 2 < len(data):
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"LD (${nn:04X}), A", 3)
    if b0 == 0x3A and pc + 2 < len(data):
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"LD A, (${nn:04X})", 3)

    # INC / DEC rr
    if (b0 & 0xCF) == 0x03:
        rr = _R16[(b0 >> 4) & 0x03]
        return (f"INC {rr}", 1)
    if (b0 & 0xCF) == 0x0B:
        rr = _R16[(b0 >> 4) & 0x03]
        return (f"DEC {rr}", 1)

    # INC / DEC r
    if (b0 & 0xC7) == 0x04:
        r = _R8[(b0 >> 3) & 0x07]
        return (f"INC {r}", 1)
    if (b0 & 0xC7) == 0x05:
        r = _R8[(b0 >> 3) & 0x07]
        return (f"DEC {r}", 1)

    # LD r, n
    if (b0 & 0xC7) == 0x06 and pc + 1 < len(data):
        r = _R8[(b0 >> 3) & 0x07]
        n = data[pc + 1]
        return (f"LD {r}, ${n:02X}", 2)

    # LD r, r' (0x40 - 0x7F, except 0x76 is HALT)
    if 0x40 <= b0 <= 0x7F:
        rd = _R8[(b0 >> 3) & 0x07]
        rs = _R8[b0 & 0x07]
        return (f"LD {rd}, {rs}", 1)

    # ALU A, r (0x80 - 0xBF)
    if 0x80 <= b0 <= 0xBF:
        op = _ALU[(b0 >> 3) & 0x07]
        r = _R8[b0 & 0x07]
        return (f"{op} {r}", 1)

    # ALU A, n (0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE)
    if (b0 & 0xC7) == 0xC6 and pc + 1 < len(data):
        op = _ALU[(b0 >> 3) & 0x07]
        n = data[pc + 1]
        return (f"{op} ${n:02X}", 2)

    # PUSH / POP
    if (b0 & 0xCF) == 0xC5:
        rr = _R16_AF[(b0 >> 4) & 0x03]
        return (f"PUSH {rr}", 1)
    if (b0 & 0xCF) == 0xC1:
        rr = _R16_AF[(b0 >> 4) & 0x03]
        return (f"POP {rr}", 1)

    # JP nn / JP cc, nn
    if b0 == 0xC3 and pc + 2 < len(data):
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"JP ${nn:04X}", 3)
    if (b0 & 0xC7) == 0xC2 and pc + 2 < len(data):
        cc = _CC[(b0 >> 3) & 0x07]
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"JP {cc}, ${nn:04X}", 3)

    # CALL nn / CALL cc, nn
    if b0 == 0xCD and pc + 2 < len(data):
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"CALL ${nn:04X}", 3)
    if (b0 & 0xC7) == 0xC4 and pc + 2 < len(data):
        cc = _CC[(b0 >> 3) & 0x07]
        nn = data[pc+1] | (data[pc+2] << 8)
        return (f"CALL {cc}, ${nn:04X}", 3)

    # RET cc
    if (b0 & 0xC7) == 0xC0:
        cc = _CC[(b0 >> 3) & 0x07]
        return (f"RET {cc}", 1)

    # OUT (n), A / IN A, (n)
    if b0 == 0xD3 and pc + 1 < len(data):
        return (f"OUT (${data[pc+1]:02X}), A", 2)
    if b0 == 0xDB and pc + 1 < len(data):
        return (f"IN A, (${data[pc+1]:02X})", 2)

    return (f"DB ${b0:02X}", 1)


def disassemble(data: bytes, origin: int = 0, count: Optional[int] = None) -> List[Tuple[int, bytes, str]]:
    """Disassemble a buffer into [(address, raw_bytes, instruction_string)]."""
    lines = []
    pc = 0
    instructions_done = 0
    while pc < len(data):
        if count is not None and instructions_done >= count:
            break
        text, n_bytes = disassemble_one(data, pc)
        if n_bytes == 0:
            break
        raw = data[pc:pc+n_bytes]
        lines.append((origin + pc, raw, text))
        pc += n_bytes
        instructions_done += 1
    return lines
