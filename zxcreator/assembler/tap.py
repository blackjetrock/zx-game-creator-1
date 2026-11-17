"""
ZX Spectrum TAP container and BASIC loader generator.
Complies with the Sinclair ZX Spectrum tape file format specification.
"""

import struct
from typing import Optional, List, Tuple


def _calc_checksum(flag: int, data: bytes) -> int:
    """Calculate the parity XOR checksum for a TAP block."""
    cs = flag
    for b in data:
        cs ^= b
    return cs


def make_tap_block(flag: int, payload: bytes) -> bytes:
    """
    Create a single TAP block.
    Format:
      - 2 bytes: total block length (len(payload) + 2) [little-endian]
      - 1 byte: flag (0x00 for header, 0xFF for data)
      - N bytes: payload
      - 1 byte: XOR checksum
    """
    checksum = _calc_checksum(flag, payload)
    block_data = bytes([flag]) + payload + bytes([checksum])
    length_prefix = struct.pack("<H", len(block_data))
    return length_prefix + block_data


def make_number_token(n: int) -> bytes:
    """
    Format a 16-bit unsigned integer into ZX Spectrum BASIC tokenized format:
    ASCII digits + 0x0E (number marker) + 5 bytes binary representation.
    For 16-bit integer N in 0..65535: [0x00, 0x00, lo, hi, 0x00].
    """
    s = str(n).encode("ascii")
    lo = n & 0xFF
    hi = (n >> 8) & 0xFF
    return s + bytes([0x0E, 0x00, 0x00, lo, hi, 0x00])


def make_basic_line(line_num: int, tokens: bytes) -> bytes:
    """
    Create a tokenized ZX Spectrum BASIC line:
      - 2 bytes line number (big-endian)
      - 2 bytes line length including 0x0D (little-endian)
      - line token contents
      - 0x0D (Enter)
    """
    content = tokens + b"\x0D"
    length = len(content)
    return struct.pack(">H", line_num) + struct.pack("<H", length) + content


def build_basic_loader(
    clear_addr: int = 24575,
    code_load_addr: Optional[int] = None,
    entry_addr: int = 24576,
    border_color: int = 0,
    has_screen: bool = False,
    title: str = "GAME"
) -> bytes:
    """
    Build a standard ZX Spectrum tokenized BASIC autoloader:
      10 BORDER n: PAPER n: INK 7: CLS
      [Optional: 15 LOAD "" SCREEN$]
      20 CLEAR clear_addr
      30 LOAD "" CODE [code_load_addr]
      40 RANDOMIZE USR entry_addr
    """
    # Tokens:
    # BORDER = 0xE7, PAPER = 0xDA, INK = 0xD9, CLS = 0xFB, ':' = 0x3A
    # CLEAR = 0xFD, LOAD = 0xEF, CODE = 0xAF, SCREEN$ = 0xAA
    # RANDOMIZE = 0xF9, USR = 0xC0
    lines = []
    
    # Line 10: BORDER c: PAPER c: INK 7: CLS
    l10 = (
        b"\xE7" + make_number_token(border_color) +
        b":\xDA" + make_number_token(border_color) +
        b":\xD9" + make_number_token(7 if border_color < 4 else 0) +
        b":\xFB"
    )
    lines.append(make_basic_line(10, l10))
    
    line_no = 20
    if has_screen:
        # LOAD "" SCREEN$
        l_scr = b"\xEF\"\"\xAA"
        lines.append(make_basic_line(line_no, l_scr))
        line_no += 10
        
    # CLEAR clear_addr
    l_clear = b"\xFD" + make_number_token(clear_addr)
    lines.append(make_basic_line(line_no, l_clear))
    line_no += 10
    
    # LOAD "" CODE
    if code_load_addr is not None:
        l_load = b"\xEF\"\"\xAF" + make_number_token(code_load_addr)
    else:
        l_load = b"\xEF\"\"\xAF"
    lines.append(make_basic_line(line_no, l_load))
    line_no += 10
    
    # RANDOMIZE USR entry_addr
    l_usr = b"\xF9\xC0" + make_number_token(entry_addr)
    lines.append(make_basic_line(line_no, l_usr))
    
    return b"".join(lines)


def make_header(
    block_type: int,
    filename: str,
    data_length: int,
    param1: int,
    param2: int
) -> bytes:
    """
    Create a 17-byte ZX Spectrum tape header payload.
      - Type: 0x00 Program, 0x01 Num array, 0x02 Char array, 0x03 Bytes/Code
      - Filename: 10 chars (ASCII, padded with spaces)
      - Data Length: 2 bytes
      - Param 1: 2 bytes (Autostart line for Program, Start Address for Bytes)
      - Param 2: 2 bytes (Program variable offset, or 32768 for Bytes)
    """
    clean_name = filename.upper()[:10].ljust(10).encode("ascii", errors="replace")
    return (
        bytes([block_type]) +
        clean_name +
        struct.pack("<H", data_length) +
        struct.pack("<H", param1) +
        struct.pack("<H", param2)
    )


def create_tap(
    code_bytes: bytes,
    start_addr: int = 24576,
    entry_addr: Optional[int] = None,
    program_name: str = "GAME",
    border_color: int = 0,
    screen_bytes: Optional[bytes] = None,
    clear_addr: Optional[int] = None
) -> bytes:
    """
    Generate a complete, bootable .TAP file containing:
      1. BASIC Loader header & data
      2. (Optional) Loading screen header & data
      3. Machine code header & data
    """
    if entry_addr is None:
        entry_addr = start_addr
    if clear_addr is None:
        clear_addr = start_addr - 1

    blocks = []
    
    # 1. BASIC autoloader
    has_screen = (screen_bytes is not None and len(screen_bytes) == 6912)
    basic_prog = build_basic_loader(
        clear_addr=clear_addr,
        code_load_addr=None,
        entry_addr=entry_addr,
        border_color=border_color,
        has_screen=has_screen,
        title=program_name
    )
    
    # BASIC header (Type 0, Autostart line 10)
    basic_header = make_header(
        block_type=0x00,
        filename=program_name,
        data_length=len(basic_prog),
        param1=10,  # Autostart line 10
        param2=len(basic_prog)
    )
    blocks.append(make_tap_block(0x00, basic_header))
    blocks.append(make_tap_block(0xFF, basic_prog))
    
    # 2. Loading screen (optional)
    if has_screen:
        scr_header = make_header(
            block_type=0x03,
            filename=program_name[:7] + "SCR",
            data_length=len(screen_bytes),
            param1=16384,
            param2=32768
        )
        blocks.append(make_tap_block(0x00, scr_header))
        blocks.append(make_tap_block(0xFF, screen_bytes))
        
    # 3. Machine Code block
    code_header = make_header(
        block_type=0x03,
        filename=program_name,
        data_length=len(code_bytes),
        param1=start_addr,
        param2=32768
    )
    blocks.append(make_tap_block(0x00, code_header))
    blocks.append(make_tap_block(0xFF, code_bytes))
    
    return b"".join(blocks)
