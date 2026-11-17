"""
Sinclair ZX Spectrum Color Palette and Attribute helper definitions.
"""

# ZX Spectrum 16 colors (8 normal + 8 bright)
PALETTE_RGB = [
    # Normal (Bright = 0)
    (0, 0, 0),        # 0: Black
    (0, 0, 215),      # 1: Blue
    (215, 0, 0),      # 2: Red
    (215, 0, 215),    # 3: Magenta
    (0, 215, 0),      # 4: Green
    (0, 215, 215),    # 5: Cyan
    (215, 215, 0),    # 6: Yellow
    (215, 215, 215),  # 7: White
    # Bright (Bright = 1)
    (0, 0, 0),        # 8: Bright Black
    (0, 0, 255),      # 9: Bright Blue
    (255, 0, 0),      # 10: Bright Red
    (255, 0, 255),    # 11: Bright Magenta
    (0, 255, 0),      # 12: Bright Green
    (0, 255, 255),    # 13: Bright Cyan
    (255, 255, 0),    # 14: Bright Yellow
    (255, 255, 255),  # 15: Bright White
]

PALETTE_HEX = [
    "#000000", "#0000D7", "#D70000", "#D700D7", "#00D700", "#00D7D7", "#D7D700", "#D7D7D7",
    "#000000", "#0000FF", "#FF0000", "#FF00FF", "#00FF00", "#00FFFF", "#FFFF00", "#FFFFFF"
]

COLOR_NAMES = [
    "Black", "Blue", "Red", "Magenta", "Green", "Cyan", "Yellow", "White"
]

def make_attr(ink: int, paper: int, bright: bool = False, flash: bool = False) -> int:
    """Pack ink (0-7), paper (0-7), bright (bool), flash (bool) into a ZX Spectrum attribute byte."""
    attr = (ink & 0x07) | ((paper & 0x07) << 3)
    if bright:
        attr |= 0x40
    if flash:
        attr |= 0x80
    return attr

def parse_attr(attr_byte: int) -> dict:
    """Unpack a ZX Spectrum attribute byte into ink, paper, bright, flash."""
    return {
        "ink": attr_byte & 0x07,
        "paper": (attr_byte >> 3) & 0x07,
        "bright": bool(attr_byte & 0x40),
        "flash": bool(attr_byte & 0x80),
    }
