from __future__ import annotations

from pathlib import Path

import click
import requests

from leanup.const import LEANUP_CACHE_DIR
from leanup.repo.cache_server import run_cache_server
from leanup.repo.mathlib_cache import MathlibCacheManager, normalize_lean_version
from leanup.repo.project_setup import LeanProjectSetup


@click.command(name="pack")
@click.argument("lean_version")
@click.option(
    "--repo-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path.cwd,
    help="Lean repository directory containing .lake/packages.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=LEANUP_CACHE_DIR / "setup" / "mathlib",
    help="Directory where <version>/packages.tar.gz will be written.",
)
@click.option(
    "--pigz/--no-pigz",
    default=True,
    help="Use pigz for parallel compression when it is available.",
)
def pack_cache(lean_version: str, repo_dir: Path, output_dir: Path, pigz: bool) -> None:
    """Pack current repository packages as packages.tar.gz."""
    manager = MathlibCacheManager(cache_root=output_dir)
    version = normalize_lean_version(lean_version)
    packages_dir = repo_dir / ".lake" / "packages"
    archive = manager.get_local_archive_path(version)

    try:
        packed = manager.pack_packages_archive(packages_dir, archive, use_pigz=pigz)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(str(packed))


@click.command(name="get")
@click.argument("lean_version")
@click.option("--base-url", required=True, help="Base URL serving /packages/mathlib/<version>/packages.tar.gz.")
@click.option(
    "--target-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path.cwd,
    help="Lean project directory where .lake/packages will be replaced.",
)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=LEANUP_CACHE_DIR / "setup" / "mathlib",
    help="Local cache directory used for packages archives.",
)
def get_cache(lean_version: str, base_url: str, target_dir: Path, cache_dir: Path) -> None:
    """Download packages.tar.gz and extract it safely."""
    manager = MathlibCacheManager(cache_root=cache_dir)

    try:
        packages_dir = manager.fetch_packages(lean_version, base_url, target_dir)
    except (ValueError, requests.RequestException) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(str(packages_dir))


@click.command(name="serve")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind.")
@click.option("--port", default=8000, show_default=True, type=int, help="Port to bind.")
@click.option(
    "--ltar-root",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path.home() / ".cache" / "mathlib",
    help="Directory serving raw .ltar files for /f/... routes.",
)
@click.option(
    "--packages-root",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=LEANUP_CACHE_DIR / "setup" / "mathlib",
    help="Directory serving <version>/packages.tar.gz for /packages/... routes.",
)
def serve_cache(host: str, port: int, ltar_root: Path, packages_root: Path) -> None:
    """Serve .ltar and packages.tar.gz cache files."""
    click.echo(f"Serving cache on http://{host}:{port}")
    click.echo(f"  ltar root: {ltar_root}")
    click.echo(f"  packages root: {packages_root}")
    try:
        run_cache_server(host, port, ltar_root, packages_root)
    except KeyboardInterrupt:
        click.echo("\nStopped.", err=True)


@click.command(name="create")
@click.argument("lean_version")
@click.option(
    "--pigz/--no-pigz",
    default=True,
    help="Use pigz for parallel compression when it is available.",
)
def create_cache(lean_version: str, pigz: bool) -> None:
    """Create shared mathlib cache in a temporary workspace."""
    setup = LeanProjectSetup()
    try:
        result = setup.create_mathlib_cache(lean_version, use_pigz=pigz)
    except (ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(str(result.cache_dir))
    click.echo(str(result.archive_path))
