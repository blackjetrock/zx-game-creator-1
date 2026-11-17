# ZX Spectrum Game Creator Studio 🕹️

A comprehensive, zero-dependency game creation suite for the **Sinclair ZX Spectrum 48K**. 

**ZX Spectrum Game Creator** generates high-performance **Z80 assembly language** (`.asm`) and compiles bootable machine code containers in Sinclair **TAP format** (`.tap`). It is designed to create **all genres of games** for the platform, including:

1. **Platformers** (*Manic Miner* / *Jet Set Willy* style: gravity, jumping, platforms, ladders, spikes, coins, moving enemies, exit gates).
2. **Top-Down Adventures** (*Sabre Wulf* / *Gauntlet* / *Zelda* style: 4-way movement, multi-room flick-screen transitions, keys, locked doors, enemy patrols).
3. **Shoot 'Em Ups** (*Space Invaders* / *Galaxian* / *R-Type* style: player starfighters, laser projectiles, alien waves, collision explosions, score targets).
4. **Grid Puzzles & Sokoban** (*Boulder Dash* style: pushable boulders, diamond gem collection, grid-aligned step mechanics, exit hatches).
5. **Graphic & Text Adventures** (*Illustrated narrative* style: room illustrations, inspection, inventory, conditional gate puzzles).

---

## Key Features

- **Z80 Assembly Code Generator**: Generates clean, modular, and extensively documented Z80 assembly source code. Compatible with the built-in assembler as well as external tools like Pasmo and Sjasmplus.
- **Built-in Pure-Python Z80 Assembler**: Assembles code in two passes with support for the full Z80 instruction set (8-bit/16-bit ALU, IX/IY index registers, bit operations, branch offset calculation, expressions, and directives). **Requires zero external compilers or C dependencies**.
- **Standard Sinclair `.TAP` Container Builder**: Produces authentic tape images with a tokenized Sinclair BASIC autoloader (`10 CLEAR 24575 : 20 LOAD "" CODE : 30 RANDOMIZE USR 24576`) followed by the binary machine code header and data blocks with parity checksums. Bootable in any emulator (Fuse, Speccy, RetroArch, QAOP) or on real hardware via DivMMC / SD card / cassette audio.
- **Interactive Web Studio**: Built-in visual IDE running on `localhost:8080`:
  - **Room & Level Designer**: Visual 16×11 tilemap painting, entity placement (player start, enemies, collectibles), multi-room linking.
  - **Sprite Editor**: 16×16 and 8×8 pixel editor, multi-frame animation manager, and INK/PAPER/BRIGHT palette selectors.
  - **Tile Editor**: 16×16 tile design with collision tagging (Solid, Platform, Ladder, Deadly Hazard, Collectible, Pushable Boulder, Key, Door, Exit).
  - **In-Browser Playable Simulator**: Real-time canvas simulation running at 50 FPS with authentic 1-bit Web Audio beeper sound synthesis.
  - **One-Click Export**: Instant download of `.TAP`, `.ASM`, and `.JSON` files.
- **Comprehensive Command-Line Interface (CLI)**: Automate project creation, assembly, compilation, disassembly, and sample exports directly from your terminal.

---

## Directory Structure

```
zx-spectrum-game-creator/
├── bin/
│   └── zxcreator                  # Executable CLI launcher
├── zxcreator/
│   ├── __init__.py
│   ├── cli.py                     # CLI commands (new, build, assemble, disassemble, serve)
│   ├── assembler/
│   │   ├── z80.py                 # Pure-Python 2-pass Z80 assembler
│   │   ├── tap.py                 # Sinclair ZX Spectrum TAP container generator
│   │   └── disassembler.py        # Z80 / TAP disassembler
│   ├── codegen/
│   │   └── generator.py           # Z80 assembly engine generator
│   ├── core/
│   │   ├── project.py             # Project data schema & JSON serialization
│   │   ├── palette.py             # ZX Spectrum color constants & attribute packers
│   │   └── presets.py             # Full game presets for all 5 archetypes
│   └── web/
│       ├── server.py              # Lightweight HTTP backend
│       └── static/
│           ├── index.html         # Visual Studio IDE
│           ├── style.css          # Retro Sinclair 1982 styling
│           └── app.js             # Canvas editors & live simulator
├── samples/                       # Pre-compiled sample games (JSON, ASM, TAP)
│   ├── platformer_castle_quest.*
│   ├── topdown_dungeon_explorer.*
│   ├── shmup_cosmic_defender.*
│   ├── puzzle_boulder_push.*
│   └── adventure_haunted_manor.*
├── setup.py
└── README.md
```

---

## Quick Start

### 1. Launch the Visual Web Studio
Start the local IDE server and open your browser:
```bash
./bin/zxcreator serve --port 8080
```
Navigate to `http://localhost:8080` to design rooms, paint sprites, edit tiles, test-play in the simulator, and download `.TAP` and `.ASM` files with one click.

### 2. Command-Line Usage

#### Create a New Game Project
```bash
# Available genres: platformer, topdown, shmup, puzzle, adventure
./bin/zxcreator new --type platformer --title "KNIGHT FALL" -o knight_fall.json
```

#### Build Project to Assembly (`.asm`) and Machine Code Tape (`.tap`)
```bash
./bin/zxcreator build knight_fall.json -o knight_fall
# Generates:
#   knight_fall.asm (Z80 assembly code)
#   knight_fall.tap (Bootable ZX Spectrum tape)
```

#### Assemble Any Standalone Z80 Assembly File
```bash
./bin/zxcreator assemble my_code.asm -o my_game.tap --name "MYGAME"
```

#### Disassemble a Binary or TAP File
```bash
./bin/zxcreator disassemble samples/platformer_castle_quest.tap -n 30
```

#### Export All 5 Complete Sample Games
```bash
./bin/zxcreator export-samples -d ./samples
```

---

## ZX Spectrum Technical Specifications

The generated games respect the Sinclair ZX Spectrum hardware constraints:

- **Target Machine**: ZX Spectrum 16K / 48K / 128K / +2 / +3.
- **Base Memory Address**: `24576` (`$6000`), safe above the BASIC system variables.
- **Screen Memory**: `16384` (`$4000`) - `22527` (`$57FF`) for pixel bitmaps (256×192 pixels).
- **Attribute Memory**: `22528` (`$5800`) - `23295` (`$5AFF`) for color attributes (32×24 cells, 8 colors with normal and bright levels).
- **Timing**: Synchronized with the 50 Hz VBLANK frame interrupt (`HALT`).
- **Sound**: Direct bit-toggling of speaker Port `254` (`$FE`) for pitch sweeps, arpeggios, and pseudo-random noise effects.
- **Controls**: QAOP + Space, Sinclair Interface 2, or Kempston Joystick (Port `31` / `$1F`).
