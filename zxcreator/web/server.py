"""
Lightweight Web Studio Server for ZX Spectrum Game Creator.
Serves the visual IDE and provides REST endpoints for Z80 code generation and TAP compilation.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional

from zxcreator.core.project import Project, GameConfig
from zxcreator.core.presets import get_preset_by_type
from zxcreator.codegen.generator import CodeGenerator
from zxcreator.assembler.z80 import Z80Assembler, AssemblyError
from zxcreator.assembler.tap import create_tap


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class StudioRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving static IDE files and compiling ZX Spectrum games."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        query = urllib.parse.parse_qs(url.query)

        # API: Get list of preset game types
        if path == "/api/presets":
            presets = [
                {"type": "platformer", "name": "Platformer (Castle Quest)", "desc": "Side-scrolling / flick-screen platformer with gravity, ladders, spikes and keys"},
                {"type": "topdown", "name": "Top-Down (Dungeon Explorer)", "desc": "4-way dungeon adventure with multi-room exploration, locked doors and wandering monsters"},
                {"type": "shmup", "name": "Shoot 'Em Up (Cosmic Defender)", "desc": "Arcade space shooter with laser projectiles, alien waves and high scores"},
                {"type": "puzzle", "name": "Grid Puzzle (Boulder Push)", "desc": "Sokoban / Boulder Dash style puzzle game with pushable rocks and diamonds"},
                {"type": "adventure", "name": "Graphic Adventure (Haunted Manor)", "desc": "Classic illustrated exploration adventure with room graphics and story choices"}
            ]
            self._send_json(presets)
            return

        # API: Get full preset project data
        if path == "/api/preset":
            g_type = query.get("type", ["platformer"])[0]
            proj = get_preset_by_type(g_type)
            self._send_json(proj.to_dict())
            return

        # Serve static files
        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)

        # API: Generate Z80 Assembly code
        if path == "/api/build/asm":
            try:
                data = json.loads(body.decode("utf-8"))
                proj = Project.from_dict(data)
                codegen = CodeGenerator(proj)
                asm_src = codegen.generate()
                self._send_json({
                    "success": True,
                    "asm": asm_src,
                    "lines": len(asm_src.splitlines()),
                    "genre": proj.config.game_type
                })
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        # API: Compile Project to bootable TAP binary
        if path == "/api/build/tap":
            try:
                data = json.loads(body.decode("utf-8"))
                proj = Project.from_dict(data)
                codegen = CodeGenerator(proj)
                asm_src = codegen.generate()

                asm = Z80Assembler()
                binary, org, syms = asm.assemble(asm_src)

                clean_name = proj.config.title[:10].upper()
                tap_bytes = create_tap(
                    code_bytes=binary,
                    start_addr=org,
                    entry_addr=syms.get("GAME_START", org),
                    program_name=clean_name,
                    border_color=proj.config.border_color
                )

                safe_filename = "".join(c for c in proj.config.title if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
                if not safe_filename:
                    safe_filename = "game"

                self.send_response(200)
                self.send_header("Content-Type", "application/x-spectrum-tap")
                self.send_header("Content-Disposition", f'attachment; filename="{safe_filename}.tap"')
                self.send_header("Content-Length", str(len(tap_bytes)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(tap_bytes)
            except AssemblyError as ae:
                self._send_json({"success": False, "error": f"Assembly error: {ae}"}, status=400)
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        # API: Assemble raw Z80 text into TAP
        if path == "/api/assemble":
            try:
                asm_src = body.decode("utf-8")
                asm = Z80Assembler()
                binary, org, syms = asm.assemble(asm_src)
                tap_bytes = create_tap(binary, start_addr=org, program_name="GAME")

                self.send_response(200)
                self.send_header("Content-Type", "application/x-spectrum-tap")
                self.send_header("Content-Disposition", 'attachment; filename="assembled.tap"')
                self.send_header("Content-Length", str(len(tap_bytes)))
                self.end_headers()
                self.wfile.write(tap_bytes)
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
            return

        self.send_error(404, "Endpoint not found")

    def _send_json(self, data, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8080, host: str = "0.0.0.0"):
    server_addr = (host, port)
    httpd = HTTPServer(server_addr, StudioRequestHandler)
    print(f"============================================================")
    print(f"  ZX SPECTRUM GAME CREATOR STUDIO")
    print(f"  Running at http://localhost:{port}/")
    print(f"  Press Ctrl+C to stop.")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()
