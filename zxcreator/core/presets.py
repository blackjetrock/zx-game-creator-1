"""
Built-in Game Templates and Presets for all ZX Spectrum genres:
1. Platformer ("Castle Quest")
2. Top-Down Adventure ("Dungeon Explorer")
3. Shoot 'Em Up ("Cosmic Defender")
4. Grid Puzzle / Sokoban ("Boulder Push")
5. Graphic Adventure ("Haunted Manor")
"""

from typing import List
from zxcreator.core.project import (
    Project, GameConfig, Sprite, SpriteFrame, Tile, Room,
    EntityInstance, ItemInstance
)


def ascii_to_pixels(art_lines: List[str], width: int = 16, height: int = 16) -> List[List[int]]:
    """Convert ASCII art representation into 2D int matrix (0 or 1)."""
    grid = []
    for row_idx in range(height):
        if row_idx < len(art_lines):
            line = art_lines[row_idx].rstrip()
            row = [1 if (col_idx < len(line) and line[col_idx] not in (' ', '.', '0')) else 0 for col_idx in range(width)]
        else:
            row = [0] * width
        grid.append(row)
    return grid


def create_platformer_preset() -> Project:
    """Create a classic Jet Set Willy / Manic Miner style platformer."""
    cfg = GameConfig(
        title="CASTLE QUEST",
        author="ZX CREATOR",
        year=1983,
        game_type="platformer",
        border_color=0,  # Black
        paper_color=0,
        ink_color=7,     # White
        bright=True,
        controls="qaop",
        start_lives=3,
        start_room=0,
        gravity=2,
        jump_strength=7,
        player_speed=2,
        hud_enabled=True,
        hud_position="bottom",
        win_score=500
    )
    proj = Project(config=cfg)

    # Player Sprite (Knight with helmet and sword) - 16x16
    knight_f1 = [
        "   .########.   ",
        "  .##########.  ",
        "  .##..##..##.  ",
        "  .##########.  ",
        "   .########.   ",
        "    .######.    ",
        "  .##########.  ",
        " .############. ",
        " .############. ",
        "  .##########.  ",
        "  .###.  .###.  ",
        "  .###.  .###.  ",
        "  .###.  .###.  ",
        "  .##.    .##.  ",
        " .####.  .####. ",
        " ......  ...... "
    ]
    knight_f2 = [
        "   .########.   ",
        "  .##########.  ",
        "  .##..##..##.  ",
        "  .##########.  ",
        "   .########.   ",
        "    .######.    ",
        "  .##########.  ",
        " .############. ",
        " .############. ",
        "  .##########.  ",
        "   .##.  .##.   ",
        "   .##.  .##.   ",
        "  .###.  .###.  ",
        " .####.   .##.  ",
        " ......   .###. ",
        "          ....  "
    ]
    proj.sprites["player"] = Sprite(
        id="player",
        name="Knight",
        width=16,
        height=16,
        frames=[
            SpriteFrame(ascii_to_pixels(knight_f1)),
            SpriteFrame(ascii_to_pixels(knight_f2))
        ],
        ink=6,  # Yellow
        paper=0,
        bright=True
    )

    # Enemy Sprite (Bat/Monster)
    bat_f1 = [
        ".##.        .##.",
        "####.      .####",
        "#####......#####",
        ".##############.",
        " .############. ",
        "  .##..##..##.  ",
        "  .##########.  ",
        "   .########.   ",
        "    .######.    ",
        "     .####.     ",
        "      .##.      ",
        "       ..       ",
        "                ",
        "                ",
        "                ",
        "                "
    ]
    proj.sprites["enemy_bat"] = Sprite(
        id="enemy_bat",
        name="Bat",
        width=16,
        height=16,
        frames=[SpriteFrame(ascii_to_pixels(bat_f1))],
        ink=2,  # Red
        paper=0,
        bright=True
    )

    # Tiles (16x16)
    # Tile 0: Empty
    proj.tiles[0] = Tile(
        id=0, name="Empty Space", width=16, height=16,
        pixels=ascii_to_pixels([" " * 16] * 16),
        ink=7, paper=0, collision="empty"
    )

    # Tile 1: Castle Stone Brick (Solid Wall)
    brick_art = [
        "################",
        "#...#......#...#",
        "#...#......#...#",
        "################",
        "#......#......##",
        "#......#......##",
        "################",
        "#...#......#...#",
        "#...#......#...#",
        "################",
        "#......#......##",
        "#......#......##",
        "################",
        "#...#......#...#",
        "#...#......#...#",
        "################"
    ]
    proj.tiles[1] = Tile(
        id=1, name="Stone Wall", width=16, height=16,
        pixels=ascii_to_pixels(brick_art),
        ink=5, paper=0, bright=False, collision="solid"
    )

    # Tile 2: Wooden Platform (Jump through from underneath)
    plat_art = [
        "################",
        "################",
        "#..............#",
        "################",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                "
    ]
    proj.tiles[2] = Tile(
        id=2, name="Platform", width=16, height=16,
        pixels=ascii_to_pixels(plat_art),
        ink=6, paper=0, bright=True, collision="platform"
    )

    # Tile 3: Ladder
    ladder_art = [
        "##............##",
        "################",
        "##............##",
        "##............##",
        "################",
        "##............##",
        "##............##",
        "################",
        "##............##",
        "##............##",
        "################",
        "##............##",
        "##............##",
        "################",
        "##............##",
        "##............##"
    ]
    proj.tiles[3] = Tile(
        id=3, name="Ladder", width=16, height=16,
        pixels=ascii_to_pixels(ladder_art),
        ink=4, paper=0, bright=True, collision="ladder"
    )

    # Tile 4: Deadly Spikes
    spikes_art = [
        "                ",
        "                ",
        "                ",
        "                ",
        "   #      #     ",
        "  ###    ###    ",
        "  ###    ###    ",
        " #####  #####   ",
        " #####  #####   ",
        "####### ####### ",
        "####### ####### ",
        "################",
        "################",
        "################",
        "################",
        "################"
    ]
    proj.tiles[4] = Tile(
        id=4, name="Spikes", width=16, height=16,
        pixels=ascii_to_pixels(spikes_art),
        ink=2, paper=0, bright=True, collision="hazard"
    )

    # Tile 5: Golden Key / Coin (Collectible)
    coin_art = [
        "                ",
        "     ######     ",
        "    ########    ",
        "   ##########   ",
        "   ##.####.##   ",
        "   ##.####.##   ",
        "   ##########   ",
        "   ##########   ",
        "    ########    ",
        "     ######     ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                "
    ]
    proj.tiles[5] = Tile(
        id=5, name="Gold Coin", width=16, height=16,
        pixels=ascii_to_pixels(coin_art),
        ink=6, paper=0, bright=True, collision="collectible", score_value=100
    )

    # Tile 6: Exit Door
    door_art = [
        "  ############  ",
        " ############## ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        " ###.....#..### ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        " ###........### ",
        "################"
    ]
    proj.tiles[6] = Tile(
        id=6, name="Castle Gate", width=16, height=16,
        pixels=ascii_to_pixels(door_art),
        ink=3, paper=0, bright=True, collision="exit"
    )

    # Room 0: The Dungeon Cell
    # 16 columns x 11 rows
    room0_grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 1],
        [1, 0, 0, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # exit east
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    r0 = Room(
        id=0,
        name="The Castle Dungeon",
        width_tiles=16,
        height_tiles=11,
        tile_grid=room0_grid,
        player_start=(2, 7),
        enemies=[EntityInstance(x=6, y=2, sprite_id="enemy_bat", ai_type="patrol_h", patrol_min=4, patrol_max=9, speed=1)],
        exits={"north": None, "south": None, "west": None, "east": 1}
    )
    proj.rooms.append(r0)

    # Room 1: The Great Hall & Gate
    room1_grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 3, 1],
        [1, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],
        [1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],  # entry west
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1],
        [1, 1, 0, 0, 0, 4, 4, 4, 4, 0, 0, 0, 0, 0, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    r1 = Room(
        id=1,
        name="The Great Hall",
        width_tiles=16,
        height_tiles=11,
        tile_grid=room1_grid,
        player_start=None,
        enemies=[EntityInstance(x=8, y=7, sprite_id="enemy_bat", ai_type="patrol_h", patrol_min=2, patrol_max=12, speed=1)],
        exits={"north": None, "south": None, "west": 0, "east": None}
    )
    proj.rooms.append(r1)

    return proj


def create_topdown_preset() -> Project:
    """Create a Sabre Wulf / Gauntlet / Zelda style top-down adventure."""
    cfg = GameConfig(
        title="DUNGEON EXPLORER",
        author="ZX CREATOR",
        year=1984,
        game_type="topdown",
        border_color=0,
        paper_color=0,
        ink_color=7,
        bright=True,
        controls="qaop",
        start_lives=3,
        start_room=0,
        player_speed=2,
        hud_enabled=True,
        hud_position="bottom",
        win_score=1000
    )
    proj = Project(config=cfg)

    # Hero Sprite (Top-Down adventurer)
    hero_f1 = [
        "     ######     ",
        "    ########    ",
        "    ########    ",
        "     ######     ",
        "  ############  ",
        " ############## ",
        " ## ########## #",
        " ## ########## #",
        " ## ########## #",
        "  ############  ",
        "    ########    ",
        "    ###  ###    ",
        "    ###  ###    ",
        "    ###  ###    ",
        "    ###  ###    ",
        "   ####  ####   "
    ]
    proj.sprites["player"] = Sprite(
        id="player", name="Hero", width=16, height=16,
        frames=[SpriteFrame(ascii_to_pixels(hero_f1))],
        ink=4, paper=0, bright=True
    )

    # Slime Monster Sprite
    slime_f1 = [
        "                ",
        "                ",
        "                ",
        "     ######     ",
        "   ##########   ",
        "  ############  ",
        "  ##.######.##  ",
        "  ##.######.##  ",
        " ############## ",
        " ############## ",
        " ############## ",
        "  ############  ",
        "   ##########   ",
        "                ",
        "                ",
        "                "
    ]
    proj.sprites["slime"] = Sprite(
        id="slime", name="Slime", width=16, height=16,
        frames=[SpriteFrame(ascii_to_pixels(slime_f1))],
        ink=2, paper=0, bright=True
    )

    # Tiles: Floor, Wall, Tree/Rock, Chest, Door
    proj.tiles[0] = Tile(
        id=0, name="Dungeon Floor", width=16, height=16,
        pixels=ascii_to_pixels([
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................"
        ]),
        ink=7, paper=0, collision="empty"
    )

    proj.tiles[1] = Tile(
        id=1, name="Stone Wall", width=16, height=16,
        pixels=ascii_to_pixels([
            "################",
            "#..............#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#.############.#",
            "#..............#",
            "################"
        ]),
        ink=1, paper=0, bright=True, collision="solid"
    )

    proj.tiles[2] = Tile(
        id=2, name="Treasure Chest", width=16, height=16,
        pixels=ascii_to_pixels([
            "                ",
            "  ############  ",
            " ############## ",
            " ############## ",
            " ############## ",
            " ############## ",
            " #######..##### ",
            " #######..##### ",
            " ############## ",
            " ############## ",
            " ############## ",
            "  ############  ",
            "                ",
            "                ",
            "                ",
            "                "
        ]),
        ink=6, paper=0, bright=True, collision="collectible", score_value=250
    )

    proj.tiles[3] = Tile(
        id=3, name="Golden Key", width=16, height=16,
        pixels=ascii_to_pixels([
            "    ######      ",
            "   ########     ",
            "   ##....##     ",
            "   ##....##     ",
            "   ########     ",
            "    ######      ",
            "      ##        ",
            "      ##        ",
            "      ####      ",
            "      ##        ",
            "      ####      ",
            "      ##        ",
            "      ##        ",
            "                ",
            "                ",
            "                "
        ]),
        ink=6, paper=0, bright=True, collision="key"
    )

    proj.tiles[4] = Tile(
        id=4, name="Portal / Exit", width=16, height=16,
        pixels=ascii_to_pixels([
            "     ######     ",
            "   ##########   ",
            "  ############  ",
            "  ##........##  ",
            " #...######...# ",
            " #..########..# ",
            " #.##########.# ",
            " #.##########.# ",
            " #.##########.# ",
            " #..########..# ",
            " #...######...# ",
            "  ##........##  ",
            "  ############  ",
            "   ##########   ",
            "     ######     ",
            "                "
        ]),
        ink=5, paper=0, bright=True, collision="exit"
    )

    # 4-way Connected Dungeon Map
    # Room 0: Entrance Chamber
    grid0 = [
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1], # Exit North to Room 1
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
        [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], # Exit East to Room 2
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
        [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    r0 = Room(
        id=0, name="Dungeon Entrance", width_tiles=16, height_tiles=11,
        tile_grid=grid0, player_start=(7, 7),
        enemies=[EntityInstance(x=3, y=3, sprite_id="slime", ai_type="chaser", speed=1)],
        exits={"north": 1, "south": None, "west": None, "east": 2}
    )
    proj.rooms.append(r0)

    # Room 1: The North Sanctuary (Exit portal)
    grid1 = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1], # Exit South to Room 0
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    r1 = Room(
        id=1, name="Sanctuary Portal", width_tiles=16, height_tiles=11,
        tile_grid=grid1, player_start=None,
        enemies=[EntityInstance(x=10, y=3, sprite_id="slime", ai_type="patrol_h", patrol_min=2, patrol_max=13, speed=1)],
        exits={"north": None, "south": 0, "west": None, "east": None}
    )
    proj.rooms.append(r1)

    return proj


def create_shmup_preset() -> Project:
    """Create a Space Invaders / Galaxian / R-Type arcade shoot 'em up."""
    cfg = GameConfig(
        title="COSMIC DEFENDER",
        author="ZX CREATOR",
        year=1983,
        game_type="shmup",
        border_color=0,
        paper_color=0,
        ink_color=7,
        bright=True,
        controls="qaop",
        start_lives=3,
        start_room=0,
        player_speed=3,
        hud_enabled=True,
        hud_position="top",
        win_score=1500
    )
    proj = Project(config=cfg)

    # Player Fighter Ship Sprite (16x16)
    ship = [
        "       ##       ",
        "       ##       ",
        "      ####      ",
        "      ####      ",
        "     ######     ",
        "    ########    ",
        "    ########    ",
        "   ##########   ",
        "   ##.####.##   ",
        "  .##########.  ",
        " .############. ",
        "################",
        "###  ######  ###",
        "##    ####    ##",
        "#      ##      #",
        "       ##       "
    ]
    proj.sprites["player"] = Sprite(
        id="player", name="StarFighter", width=16, height=16,
        frames=[SpriteFrame(ascii_to_pixels(ship))],
        ink=5, paper=0, bright=True
    )

    # Alien Invader Sprite
    alien = [
        "   ##      ##   ",
        "    ##    ##    ",
        "   ##########   ",
        "  ############  ",
        " ############## ",
        " ####..##..#### ",
        " ############## ",
        "  ############  ",
        "   ##########   ",
        "  ##   ##   ##  ",
        " ##    ##    ## ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                "
    ]
    proj.sprites["alien"] = Sprite(
        id="alien", name="Alien", width=16, height=16,
        frames=[SpriteFrame(ascii_to_pixels(alien))],
        ink=4, paper=0, bright=True
    )

    # Laser projectile (8x8)
    laser = [
        "   ##   ",
        "   ##   ",
        "  ####  ",
        "  ####  ",
        "   ##   ",
        "   ##   ",
        "   ##   ",
        "   ##   "
    ]
    proj.sprites["laser"] = Sprite(
        id="laser", name="Laser", width=8, height=8,
        frames=[SpriteFrame(ascii_to_pixels(laser, 8, 8))],
        ink=6, paper=0, bright=True
    )

    # Empty space tile
    proj.tiles[0] = Tile(id=0, name="Deep Space", width=16, height=16,
        pixels=ascii_to_pixels([" "*16]*16), ink=7, paper=0, collision="empty")

    # Star tile
    star = [
        "                ",
        "       .        ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "                ",
        "             .  ",
        "                ",
        "                ",
        "                ",
        "                "
    ]
    proj.tiles[1] = Tile(id=1, name="Starfield", width=16, height=16,
        pixels=ascii_to_pixels(star), ink=7, paper=0, bright=True, collision="empty")

    # Shmup arena
    grid = [[1 if (r + c) % 5 == 0 else 0 for c in range(16)] for r in range(11)]
    r0 = Room(
        id=0, name="Sector Alpha", width_tiles=16, height_tiles=11,
        tile_grid=grid, player_start=(7, 9),
        enemies=[
            EntityInstance(x=2, y=1, sprite_id="alien", ai_type="patrol_h", patrol_min=1, patrol_max=14, speed=1),
            EntityInstance(x=6, y=2, sprite_id="alien", ai_type="patrol_h", patrol_min=2, patrol_max=13, speed=1),
            EntityInstance(x=10, y=1, sprite_id="alien", ai_type="patrol_h", patrol_min=3, patrol_max=14, speed=1),
            EntityInstance(x=4, y=3, sprite_id="alien", ai_type="patrol_h", patrol_min=1, patrol_max=12, speed=1)
        ]
    )
    proj.rooms.append(r0)
    return proj


def create_puzzle_preset() -> Project:
    """Create a Boulder Dash / Sokoban style grid puzzle game."""
    cfg = GameConfig(
        title="BOULDER PUSH",
        author="ZX CREATOR",
        year=1984,
        game_type="puzzle",
        border_color=0,
        paper_color=0,
        ink_color=7,
        bright=True,
        controls="qaop",
        start_lives=3,
        start_room=0,
        player_speed=2,
        hud_enabled=True,
        hud_position="bottom",
        win_score=1000
    )
    proj = Project(config=cfg)

    # Miner Sprite (16x16)
    miner = [
        "     ######     ",
        "   ##########   ",
        "  ############  ",
        "  ############  ",
        "   ##########   ",
        "    ########    ",
        "  ############  ",
        " ############## ",
        " ## ########## #",
        " ## ########## #",
        "  ############  ",
        "    ########    ",
        "    ###  ###    ",
        "    ###  ###    ",
        "   ####  ####   ",
        "   ####  ####   "
    ]
    proj.sprites["player"] = Sprite(
        id="player", name="Miner", width=16, height=16,
        frames=[SpriteFrame(ascii_to_pixels(miner))],
        ink=6, paper=0, bright=True
    )

    # Tile 0: Empty Space
    proj.tiles[0] = Tile(id=0, name="Tunnel", width=16, height=16,
        pixels=ascii_to_pixels([" "*16]*16), ink=7, paper=0, collision="empty")

    # Tile 1: Indestructible Wall
    wall = [
        "################",
        "#..............#",
        "#..##########..#",
        "#..#........#..#",
        "#..#........#..#",
        "#..#........#..#",
        "#..#........#..#",
        "#..##########..#",
        "#..##########..#",
        "#..#........#..#",
        "#..#........#..#",
        "#..#........#..#",
        "#..#........#..#",
        "#..##########..#",
        "#..............#",
        "################"
    ]
    proj.tiles[1] = Tile(id=1, name="Granite Wall", width=16, height=16,
        pixels=ascii_to_pixels(wall), ink=1, paper=0, bright=True, collision="solid")

    # Tile 2: Pushable Boulder
    boulder = [
        "     ######     ",
        "   ##########   ",
        "  ############  ",
        " ############## ",
        " ############## ",
        "################",
        "################",
        "################",
        "################",
        "################",
        "################",
        " ############## ",
        " ############## ",
        "  ############  ",
        "   ##########   ",
        "     ######     "
    ]
    proj.tiles[2] = Tile(id=2, name="Boulder", width=16, height=16,
        pixels=ascii_to_pixels(boulder), ink=7, paper=0, bright=False, collision="pushable")

    # Tile 3: Diamond Gem (Collectible)
    diamond = [
        "       ##       ",
        "      ####      ",
        "     ######     ",
        "    ########    ",
        "   ##########   ",
        "  ############  ",
        " ############## ",
        "################",
        " ############## ",
        "  ############  ",
        "   ##########   ",
        "    ########    ",
        "     ######     ",
        "      ####      ",
        "       ##       ",
        "                "
    ]
    proj.tiles[3] = Tile(id=3, name="Diamond", width=16, height=16,
        pixels=ascii_to_pixels(diamond), ink=5, paper=0, bright=True, collision="collectible", score_value=200)

    # Tile 4: Exit Hatch
    exit_tile = [
        "################",
        "#              #",
        "#  ##########  #",
        "#  # EXIT   #  #",
        "#  ##########  #",
        "#              #",
        "#  ..........  #",
        "#  ..........  #",
        "#  ..........  #",
        "#              #",
        "#  ##########  #",
        "#  #        #  #",
        "#  ##########  #",
        "#              #",
        "#              #",
        "################"
    ]
    proj.tiles[4] = Tile(id=4, name="Exit Ladder", width=16, height=16,
        pixels=ascii_to_pixels(exit_tile), ink=4, paper=0, bright=True, collision="exit")

    # Puzzle room
    puzzle_grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 1, 3, 0, 0, 0, 0, 1, 0, 0, 4, 1],
        [1, 0, 2, 0, 0, 1, 1, 1, 0, 2, 0, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 2, 0, 1],
        [1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1],
        [1, 3, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 2, 0, 1, 0, 3, 0, 1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 3, 0, 0, 1],
        [1, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    r0 = Room(
        id=0, name="Cavern 1", width_tiles=16, height_tiles=11,
        tile_grid=puzzle_grid, player_start=(1, 1)
    )
    proj.rooms.append(r0)
    return proj


def create_adventure_preset() -> Project:
    """Create a classic Graphic Adventure / Interactive Exploration game."""
    cfg = GameConfig(
        title="HAUNTED MANOR",
        author="ZX CREATOR",
        year=1984,
        game_type="adventure",
        border_color=0,
        paper_color=0,
        ink_color=7,
        bright=True,
        controls="qaop",
        start_lives=1,
        start_room=0,
        hud_enabled=True,
        hud_position="bottom",
        win_score=1000
    )
    proj = Project(config=cfg)

    # Empty tile
    proj.tiles[0] = Tile(id=0, name="Empty", width=16, height=16,
        pixels=ascii_to_pixels([" "*16]*16), ink=7, paper=0, collision="empty")

    # Manor Wall
    wall = [
        "################",
        "#..............#",
        "#..##########..#",
        "#..#        #..#",
        "#..#        #..#",
        "#..#        #..#",
        "#..#        #..#",
        "#..##########..#",
        "#..#        #..#",
        "#..#        #..#",
        "#..#        #..#",
        "#..##########..#",
        "#..............#",
        "################",
        "################",
        "################"
    ]
    proj.tiles[1] = Tile(id=1, name="Manor Wall", width=16, height=16,
        pixels=ascii_to_pixels(wall), ink=3, paper=0, bright=True, collision="solid")

    # Item: Brass Key
    key = [
        "     ######     ",
        "    ########    ",
        "    ##....##    ",
        "    ##....##    ",
        "    ########    ",
        "     ######     ",
        "       ##       ",
        "       ##       ",
        "       ####     ",
        "       ##       ",
        "       ####     ",
        "       ##       ",
        "       ##       ",
        "                ",
        "                ",
        "                "
    ]
    proj.tiles[2] = Tile(id=2, name="Brass Key", width=16, height=16,
        pixels=ascii_to_pixels(key), ink=6, paper=0, bright=True, collision="key")

    # Locked Iron Door
    door = [
        "  ############  ",
        " ############## ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        " ###..####..### ",
        "################"
    ]
    proj.tiles[3] = Tile(id=3, name="Iron Gate", width=16, height=16,
        pixels=ascii_to_pixels(door), ink=5, paper=0, bright=True, collision="door")

    # Victory Relic / Book
    book = [
        "                ",
        "  ############  ",
        " ############## ",
        " ###..........# ",
        " ###.SPELLBOOK# ",
        " ###..........# ",
        " ###.########## ",
        " ###..........# ",
        " ###.OF ANCIENT#",
        " ###..........# ",
        " ###.WISDOM#### ",
        " ###..........# ",
        " ############## ",
        "  ############  ",
        "                ",
        "                "
    ]
    proj.tiles[4] = Tile(id=4, name="Ancient Book", width=16, height=16,
        pixels=ascii_to_pixels(book), ink=4, paper=0, bright=True, collision="exit")

    # Rooms
    g0 = [
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    r0 = Room(
        id=0, name="Grand Foyer", width_tiles=16, height_tiles=11,
        tile_grid=g0, player_start=(7, 7),
        message="YOU STAND IN THE GRAND FOYER. A BRASS KEY LIES ON THE MARBLE FLOOR.",
        exits={"north": 1, "south": None, "west": None, "east": None}
    )
    proj.rooms.append(r0)

    g1 = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 3, 3, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    r1 = Room(
        id=1, name="The Secret Library", width_tiles=16, height_tiles=11,
        tile_grid=g1, player_start=None,
        message="AN IRON GATE BARS THE WAY TO THE ANCIENT SPELLBOOK.",
        exits={"north": None, "south": 0, "west": None, "east": None}
    )
    proj.rooms.append(r1)

    return proj


def get_preset_by_type(game_type: str) -> Project:
    """Return a ready-to-run project for the specified game type."""
    t = game_type.lower()
    if t == "platformer":
        return create_platformer_preset()
    elif t == "topdown":
        return create_topdown_preset()
    elif t == "shmup":
        return create_shmup_preset()
    elif t == "puzzle":
        return create_puzzle_preset()
    elif t == "adventure":
        return create_adventure_preset()
    else:
        return create_platformer_preset()
