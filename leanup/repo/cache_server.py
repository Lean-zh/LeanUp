from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


class CacheRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, ltar_root: Path, packages_root: Path, **kwargs):
        self.ltar_root = ltar_root
        self.packages_root = packages_root
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/healthz":
            payload = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        file_path = self._resolve_path(path)
        if file_path is None or not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File not found")
            return

        self.path = str(file_path)
        return super().do_GET()

    def translate_path(self, path: str) -> str:
        return path

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _resolve_path(self, path: str) -> Path | None:
        parts = [part for part in path.split("/") if part]
        if not parts:
            return None

        if len(parts) == 2 and parts[0] == "f" and parts[1].endswith(".ltar"):
            return self.ltar_root / parts[1]

        if len(parts) == 4 and parts[0] == "f" and parts[3].endswith(".ltar"):
            return self.ltar_root / "repos" / parts[1] / parts[2] / parts[3]

        if len(parts) == 4 and parts[0] == "packages" and parts[1] == "mathlib" and parts[3] == "packages.tar.gz":
            return self.packages_root / parts[2] / "packages.tar.gz"

        return None


def make_cache_server(host: str, port: int, ltar_root: Path, packages_root: Path) -> ThreadingHTTPServer:
    handler = partial(
        CacheRequestHandler,
        ltar_root=ltar_root.resolve(),
        packages_root=packages_root.resolve(),
    )
    return ThreadingHTTPServer((host, port), handler)
