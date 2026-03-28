#!/usr/bin/env python3
"""Local dev server for the notes site with movies enrichment API."""

import json
import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

MOVIES_FILE = Path(__file__).parent.parent / "movies.log"
PORT = 8787


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/omdb-key":
            key = os.environ.get("OMDB_API_KEY", "")
            self._json_response(200, {"key": key})
        else:
            super().do_GET()

    def end_headers(self):
        if self.path and self.path.endswith(".log"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        if self.path == "/api/enrich":
            self._handle_enrich()
        else:
            self.send_error(404)

    def _handle_enrich(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            title = body["title"]
            indent = body["indent"]
            properties = body.get("properties", [])
            cast = body.get("cast", [])
            imdb_url = body.get("imdb_url")

            lines = MOVIES_FILE.read_text(encoding="utf-8").splitlines(keepends=True)

            # Find the movie line
            movie_idx = self._find_movie(lines, title, indent)
            if movie_idx is None:
                self._json_response(404, {"error": f"Movie '{title}' not found"})
                return

            # Find insertion point: after movie line + any existing children
            insert_idx = movie_idx + 1
            prop_indent = indent + 4
            while insert_idx < len(lines):
                line = lines[insert_idx]
                stripped = line.rstrip("\n")
                if not stripped.strip():
                    # blank line - check if next non-blank is still a child
                    insert_idx += 1
                    continue
                line_indent = len(stripped) - len(stripped.lstrip())
                if line_indent > indent:
                    insert_idx += 1
                else:
                    break

            # Build new lines
            pad = " " * prop_indent
            new_lines = []
            for prop in properties:
                new_lines.append(f"{pad}- {prop['key']}: {prop['value']}\n")
            if cast:
                new_lines.append(f"{pad}- Cast (IMDb):\n")
                cast_pad = " " * (prop_indent + 4)
                for actor in cast:
                    new_lines.append(f"{cast_pad}- {actor}\n")
            if imdb_url:
                new_lines.append(f"{pad}- IMDB: {imdb_url}\n")

            # Insert
            lines[insert_idx:insert_idx] = new_lines

            MOVIES_FILE.write_text("".join(lines), encoding="utf-8")

            self._json_response(200, {
                "ok": True,
                "added": len(new_lines),
                "at_line": insert_idx + 1,
            })

        except (json.JSONDecodeError, KeyError) as e:
            self._json_response(400, {"error": str(e)})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _find_movie(self, lines, title, indent):
        """Find the line index of a movie entry by title and indent."""
        title_lower = title.lower().strip()
        pattern = re.compile(
            r"^\s*\[[x\-? ]?\]\s*(.+?)\s*$", re.IGNORECASE
        )
        for i, line in enumerate(lines):
            stripped = line.rstrip("\n")
            line_indent = len(stripped) - len(stripped.lstrip())
            if line_indent != indent:
                continue
            m = pattern.match(stripped)
            if m and m.group(1).strip().lower() == title_lower:
                return i
        return None

    def _json_response(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        if "/api/" in (args[0] if args else ""):
            super().log_message(format, *args)


if __name__ == "__main__":
    print(f"Serving on http://localhost:{PORT}")
    print(f"Movies file: {MOVIES_FILE}")
    HTTPServer(("", PORT), Handler).serve_forever()
