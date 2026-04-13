from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
import uvicorn


def create_cache_app(ltar_root: Path, packages_root: Path) -> FastAPI:
    ltar_root = ltar_root.resolve()
    packages_root = packages_root.resolve()

    app = FastAPI(title="LeanUp Cache Server")

    @app.get("/healthz")
    def healthz() -> PlainTextResponse:
        return PlainTextResponse("ok\n")

    @app.get("/packages/mathlib/index.json")
    def package_index() -> JSONResponse:
        return JSONResponse({"versions": list_package_versions(packages_root)})

    @app.get("/f/{filename:path}")
    def ltar_file(filename: str) -> FileResponse:
        file_path = resolve_ltar_path(ltar_root, filename)
        return file_response(file_path)

    @app.get("/packages/mathlib/{version}/packages.tar.gz")
    def package_archive(version: str) -> FileResponse:
        return file_response(packages_root / version / "packages.tar.gz")

    return app


def run_cache_server(host: str, port: int, ltar_root: Path, packages_root: Path) -> None:
    app = create_cache_app(ltar_root, packages_root)
    uvicorn.run(app, host=host, port=port, log_level="info")


def list_package_versions(packages_root: Path) -> list[str]:
    if not packages_root.exists():
        return []

    versions: list[str] = []
    for child in sorted(packages_root.iterdir()):
        if child.is_dir() and (child / "packages.tar.gz").exists():
            versions.append(child.name)
    return versions


def resolve_ltar_path(ltar_root: Path, filename: str) -> Path:
    parts = [part for part in filename.split("/") if part]
    if len(parts) == 1 and parts[0].endswith(".ltar"):
        return ltar_root / parts[0]
    if len(parts) == 3 and parts[2].endswith(".ltar"):
        return ltar_root / "repos" / parts[0] / parts[1] / parts[2]
    raise HTTPException(status_code=404, detail="File not found")


def file_response(file_path: Path) -> FileResponse:
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
