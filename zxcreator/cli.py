"""
Command Line Interface for the ZX Spectrum Game Creator.
"""

import sys
import os

# Ensure package root is in sys.path
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

import argparse
import json
from typing import Optional

from zxcreator.core.project import Project, GameConfig
from zxcreator.core.presets import get_preset_by_type
from zxcreator.codegen.generator import CodeGenerator
from zxcreator.assembler.z80 import Z80Assembler
from zxcreator.assembler.tap import create_tap
from zxcreator.assembler.disassembler import disassemble


def cmd_new(args):
    """Create a new game project from a template."""
    proj = get_preset_by_type(args.type)
    if args.title:
        proj.config.title = args.title
    if args.author:
        proj.config.author = args.author
    
    out_path = args.output or f"{proj.config.title.lower().replace(' ', '_')}.json"
    proj.save_json(out_path)
    print(f"[*] Created new {args.type.upper()} project: '{out_path}'")
    print(f"    Title: {proj.config.title}")
    print(f"    Rooms: {len(proj.rooms)}, Tiles: {len(proj.tiles)}, Sprites: {len(proj.sprites)}")


def cmd_build(args):
    """Build a game project into Z80 assembly and/or TAP machine code."""
    if not os.path.isfile(args.project):
        print(f"[!] Error: Project file not found: {args.project}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Loading project: {args.project}...")
    proj = Project.load_json(args.project)
    
    # 1. Generate Z80 Assembly
    print(f"[*] Generating Z80 assembly code for genre '{proj.config.game_type}'...")
    codegen = CodeGenerator(proj, org_addr=args.org)
    asm_source = codegen.generate()
    
    base_name = os.path.splitext(args.output or args.project)[0]
    asm_path = f"{base_name}.asm"
    tap_path = f"{base_name}.tap"

    # Always write ASM file
    with open(asm_path, "w", encoding="utf-8") as f:
        f.write(asm_source)
    print(f"    [+] Assembly written to: {asm_path} ({len(asm_source.splitlines())} lines)")

    # 2. Assemble to Machine Code
    print(f"[*] Assembling Z80 code at address ${args.org:04X} ({args.org})...")
    asm = Z80Assembler()
    binary, org, syms = asm.assemble(asm_source)
    print(f"    [+] Machine code assembled: {len(binary)} bytes (Entry: ${syms.get('GAME_START', org):04X})")

    # 3. Create bootable TAP file
    clean_name = proj.config.title[:10].upper()
    tap_data = create_tap(
        code_bytes=binary,
        start_addr=org,
        entry_addr=syms.get("GAME_START", org),
        program_name=clean_name,
        border_color=proj.config.border_color
    )
    with open(tap_path, "wb") as f:
        f.write(tap_data)
    print(f"    [+] Bootable TAP written to: {tap_path} ({len(tap_data)} bytes)")
    print(f"[+] Build complete! Game '{proj.config.title}' is ready to run on any ZX Spectrum emulator or real hardware.")


def cmd_assemble(args):
    """Assemble any standalone Z80 assembly source file into a TAP container."""
    if not os.path.isfile(args.source):
        print(f"[!] Error: Source file not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Assembling source file: {args.source}...")
    with open(args.source, "r", encoding="utf-8", errors="replace") as f:
        source_text = f.read()

    base_dir = os.path.dirname(os.path.abspath(args.source))
    asm = Z80Assembler(include_dirs=[base_dir])
    binary, org, syms = asm.assemble(source_text, base_dir=base_dir)
    print(f"    [+] Assembled {len(binary)} bytes at origin ${org:04X}")

    out_tap = args.output or f"{os.path.splitext(args.source)[0]}.tap"
    prog_name = (args.name or os.path.splitext(os.path.basename(args.source))[0])[:10].upper()
    tap_data = create_tap(
        code_bytes=binary,
        start_addr=org,
        entry_addr=syms.get("GAME_START", org),
        program_name=prog_name
    )
    with open(out_tap, "wb") as f:
        f.write(tap_data)
    print(f"    [+] Generated TAP file: {out_tap} ({len(tap_data)} bytes)")


def cmd_disassemble(args):
    """Disassemble a binary file or raw CODE block."""
    if not os.path.isfile(args.file):
        print(f"[!] Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    with open(args.file, "rb") as f:
        data = f.read()

    # Check if this is a TAP file
    if args.file.lower().endswith(".tap"):
        # Parse blocks in TAP to locate CODE block
        idx = 0
        code_data = None
        code_org = args.org or 24576
        while idx + 2 <= len(data):
            block_len = data[idx] | (data[idx+1] << 8)
            idx += 2
            block = data[idx:idx+block_len]
            idx += block_len
            if len(block) >= 2:
                flag = block[0]
                payload = block[1:-1]
                if flag == 0x00 and len(payload) == 17 and payload[0] == 0x03:
                    # CODE Header (Param 1 is start address at bytes 13-14)
                    code_org = payload[13] | (payload[14] << 8)
                elif flag == 0xFF and code_data is None and len(payload) > 100:
                    code_data = payload
        if code_data:
            data = code_data
            org = code_org
        else:
            org = args.org or 24576
    else:
        org = args.org or 24576

    count = args.lines or 50
    lines = disassemble(data, origin=org, count=count)
    print(f"--- Disassembly of {args.file} (Origin: ${org:04X}) ---")
    for addr, raw, text in lines:
        hex_dump = " ".join(f"{b:02X}" for b in raw).ljust(12)
        print(f"${addr:04X}:  {hex_dump} {text}")


def cmd_export_samples(args):
    """Export all 5 complete game genres with JSON, ASM, and TAP files."""
    dest = args.dir or "./samples"
    os.makedirs(dest, exist_ok=True)
    genres = ["platformer", "topdown", "shmup", "puzzle", "adventure"]

    print(f"[*] Exporting all {len(genres)} game presets to '{dest}'...")
    for g in genres:
        proj = get_preset_by_type(g)
        prefix = f"{dest}/{g}_{proj.config.title.lower().replace(' ', '_')}"
        
        # Save JSON
        json_path = f"{prefix}.json"
        proj.save_json(json_path)

        # Generate ASM
        codegen = CodeGenerator(proj)
        asm_src = codegen.generate()
        asm_path = f"{prefix}.asm"
        with open(asm_path, "w", encoding="utf-8") as f:
            f.write(asm_src)

        # Assemble and Save TAP
        asm = Z80Assembler()
        binary, org, syms = asm.assemble(asm_src)
        tap_path = f"{prefix}.tap"
        tap_bytes = create_tap(binary, start_addr=org, program_name=proj.config.title[:10].upper())
        with open(tap_path, "wb") as f:
            f.write(tap_bytes)

        print(f"    [+] {g.upper().ljust(10)} -> {os.path.basename(tap_path)} ({len(tap_bytes)} bytes)")
    print("[*] All samples successfully generated and exported!")


def cmd_serve(args):
    """Launch the interactive Web Studio server."""
    from zxcreator.web.server import run_server
    run_server(port=args.port, host=args.host)


def main():
    parser = argparse.ArgumentParser(
        prog="zxcreator",
        description="ZX Spectrum Game Creator Tool - Outputs Z80 Assembly & TAP Machine Code"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # new
    p_new = subparsers.add_parser("new", help="Create a new game project template")
    p_new.add_argument("--type", "-t", choices=["platformer", "topdown", "shmup", "puzzle", "adventure"], default="platformer", help="Game genre")
    p_new.add_argument("--title", help="Game title")
    p_new.add_argument("--author", help="Author name")
    p_new.add_argument("-o", "--output", help="Output JSON path")

    # build
    p_build = subparsers.add_parser("build", help="Build project into Z80 assembly and TAP file")
    p_build.add_argument("project", help="Path to project.json")
    p_build.add_argument("-o", "--output", help="Output base filename")
    p_build.add_argument("--org", type=int, default=24576, help="Z80 origin address (default: 24576 / $6000)")

    # assemble
    p_asm = subparsers.add_parser("assemble", help="Assemble any Z80 assembly file into TAP")
    p_asm.add_argument("source", help="Input .asm file")
    p_asm.add_argument("-o", "--output", help="Output .tap path")
    p_asm.add_argument("--name", help="Program name on tape (up to 10 chars)")

    # disassemble
    p_dis = subparsers.add_parser("disassemble", help="Disassemble a binary or TAP file")
    p_dis.add_argument("file", help="Input file (.tap or .bin)")
    p_dis.add_argument("--org", type=int, help="Origin memory address")
    p_dis.add_argument("-n", "--lines", type=int, default=50, help="Number of instructions to disassemble")

    # export-samples
    p_samples = subparsers.add_parser("export-samples", help="Export all 5 complete game samples (JSON, ASM, TAP)")
    p_samples.add_argument("-d", "--dir", default="./samples", help="Destination folder")

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch interactive browser visual studio")
    p_serve.add_argument("-p", "--port", type=int, default=8080, help="HTTP port (default: 8080)")
    p_serve.add_argument("--host", default="0.0.0.0", help="HTTP host interface (default: 0.0.0.0)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "new": cmd_new,
        "build": cmd_build,
        "assemble": cmd_assemble,
        "disassemble": cmd_disassemble,
        "export-samples": cmd_export_samples,
        "serve": cmd_serve
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
