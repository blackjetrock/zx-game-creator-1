"""
ZX Spectrum Project Data Model and Serialization.
Stores all game assets, maps, configurations, and behaviors.
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from zxcreator.core.palette import make_attr


@dataclass
class SpriteFrame:
    """A single frame of an 8x8 or 16x16 sprite."""
    # List of rows, each row is a list of 0 or 1 integers (8 or 16 ints)
    pixels: List[List[int]]

    def to_bytes(self) -> bytes:
        """Convert pixel matrix into ZX Spectrum bitmap bytes."""
        out = bytearray()
        for row in self.pixels:
            val = 0
            for col_idx, pixel in enumerate(row):
                bit_pos = 7 - (col_idx % 8)
                if pixel:
                    val |= (1 << bit_pos)
                if (col_idx % 8) == 7:
                    out.append(val)
                    val = 0
            # If row length wasn't multiple of 8
            if len(row) % 8 != 0:
                out.append(val)
        return bytes(out)

    def to_mask_bytes(self) -> bytes:
        """Generate inverted mask bytes (0 where sprite is solid, 1 where transparent)."""
        sprite_bytes = self.to_bytes()
        return bytes((~b) & 0xFF for b in sprite_bytes)


@dataclass
class Sprite:
    id: str
    name: str
    width: int = 16   # 8 or 16
    height: int = 16  # 8 or 16
    frames: List[SpriteFrame] = field(default_factory=list)
    ink: int = 7
    paper: int = 0
    bright: bool = True
    mask_mode: str = "xor"  # "xor", "or", "mask"

    @property
    def attr_byte(self) -> int:
        return make_attr(self.ink, self.paper, self.bright)


@dataclass
class Tile:
    id: int
    name: str
    width: int = 16   # 16x16 is standard for 16x11 screen, or 8x8
    height: int = 16
    pixels: List[List[int]] = field(default_factory=list)
    ink: int = 7
    paper: int = 0
    bright: bool = False
    collision: str = "empty"  # empty, solid, platform, ladder, hazard, collectible, pushable, door, key, exit
    score_value: int = 0

    @property
    def attr_byte(self) -> int:
        return make_attr(self.ink, self.paper, self.bright)

    def to_bytes(self) -> bytes:
        """Convert pixel matrix to bytes."""
        frame = SpriteFrame(pixels=self.pixels)
        return frame.to_bytes()


@dataclass
class EntityInstance:
    """Instance of an enemy, NPC, or dynamic object placed in a room."""
    x: int  # Tile column or pixel X
    y: int  # Tile row or pixel Y
    sprite_id: str
    ai_type: str = "patrol_h"  # patrol_h, patrol_v, chaser, bouncer, static, wave
    patrol_min: int = 0
    patrol_max: int = 15
    speed: int = 1
    health: int = 1


@dataclass
class ItemInstance:
    """Instance of a pickup item, key, or interactive object in a room."""
    x: int
    y: int
    tile_id: int
    item_type: str = "coin"  # coin, gem, key, extra_life, goal


@dataclass
class Room:
    id: int
    name: str
    width_tiles: int = 16   # 16 tiles wide (for 16x16 tiles = 256 pixels)
    height_tiles: int = 11  # 11 tiles high (for 16x16 tiles = 176 pixels, leaves 16px for HUD)
    tile_grid: List[List[int]] = field(default_factory=list)
    player_start: Optional[Tuple[int, int]] = None
    enemies: List[EntityInstance] = field(default_factory=list)
    items: List[ItemInstance] = field(default_factory=list)
    exits: Dict[str, Optional[int]] = field(default_factory=lambda: {"north": None, "south": None, "west": None, "east": None})
    message: str = ""


@dataclass
class GameConfig:
    title: str = "SPECTRUM QUEST"
    author: str = "RETRO DEV"
    year: int = 1983
    game_type: str = "platformer"  # platformer, topdown, shmup, puzzle, adventure
    border_color: int = 0
    paper_color: int = 0
    ink_color: int = 7
    bright: bool = True
    controls: str = "qaop"  # qaop, kempston, sinclair
    start_lives: int = 3
    start_room: int = 0
    gravity: int = 2
    jump_strength: int = 6
    player_speed: int = 2
    hud_enabled: bool = True
    hud_position: str = "bottom"  # bottom, top, none
    sound_enabled: bool = True
    win_score: int = 1000
    collect_all_to_win: bool = False


class Project:
    """A complete ZX Spectrum game project."""
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or GameConfig()
        self.sprites: Dict[str, Sprite] = {}
        self.tiles: Dict[int, Tile] = {}
        self.rooms: List[Room] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to a serializable dictionary."""
        return {
            "config": asdict(self.config),
            "sprites": {
                s_id: {
                    "id": s.id,
                    "name": s.name,
                    "width": s.width,
                    "height": s.height,
                    "ink": s.ink,
                    "paper": s.paper,
                    "bright": s.bright,
                    "mask_mode": s.mask_mode,
                    "frames": [f.pixels for f in s.frames]
                }
                for s_id, s in self.sprites.items()
            },
            "tiles": {
                t_id: {
                    "id": t.id,
                    "name": t.name,
                    "width": t.width,
                    "height": t.height,
                    "ink": t.ink,
                    "paper": t.paper,
                    "bright": t.bright,
                    "collision": t.collision,
                    "score_value": t.score_value,
                    "pixels": t.pixels
                }
                for t_id, t in self.tiles.items()
            },
            "rooms": [
                {
                    "id": r.id,
                    "name": r.name,
                    "width_tiles": r.width_tiles,
                    "height_tiles": r.height_tiles,
                    "tile_grid": r.tile_grid,
                    "player_start": r.player_start,
                    "exits": r.exits,
                    "message": r.message,
                    "enemies": [asdict(e) for e in r.enemies],
                    "items": [asdict(i) for i in r.items],
                }
                for r in self.rooms
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Reconstruct project from dictionary."""
        cfg_data = data.get("config", {})
        config = GameConfig(**cfg_data)
        proj = cls(config=config)

        # Sprites
        for s_id, s_data in data.get("sprites", {}).items():
            frames = [SpriteFrame(pixels=p) for p in s_data.get("frames", [])]
            sprite = Sprite(
                id=s_data.get("id", s_id),
                name=s_data.get("name", s_id),
                width=s_data.get("width", 16),
                height=s_data.get("height", 16),
                frames=frames,
                ink=s_data.get("ink", 7),
                paper=s_data.get("paper", 0),
                bright=s_data.get("bright", True),
                mask_mode=s_data.get("mask_mode", "xor")
            )
            proj.sprites[s_id] = sprite

        # Tiles
        for t_id_str, t_data in data.get("tiles", {}).items():
            t_id = int(t_id_str)
            tile = Tile(
                id=t_id,
                name=t_data.get("name", f"Tile {t_id}"),
                width=t_data.get("width", 16),
                height=t_data.get("height", 16),
                pixels=t_data.get("pixels", []),
                ink=t_data.get("ink", 7),
                paper=t_data.get("paper", 0),
                bright=t_data.get("bright", False),
                collision=t_data.get("collision", "empty"),
                score_value=t_data.get("score_value", 0)
            )
            proj.tiles[t_id] = tile

        # Rooms
        for r_data in data.get("rooms", []):
            enemies = [EntityInstance(**e) for e in r_data.get("enemies", [])]
            items = [ItemInstance(**i) for i in r_data.get("items", [])]
            room = Room(
                id=r_data.get("id", 0),
                name=r_data.get("name", "Room"),
                width_tiles=r_data.get("width_tiles", 16),
                height_tiles=r_data.get("height_tiles", 11),
                tile_grid=r_data.get("tile_grid", []),
                player_start=tuple(r_data["player_start"]) if r_data.get("player_start") else None,
                enemies=enemies,
                items=items,
                exits=r_data.get("exits", {"north": None, "south": None, "west": None, "east": None}),
                message=r_data.get("message", "")
            )
            proj.rooms.append(room)

        return proj

    def save_json(self, path: str):
        """Save project to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: str) -> "Project":
        """Load project from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
