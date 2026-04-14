from __future__ import annotations

from pathlib import Path

import click
import requests

from leanup.const import LEANUP_CACHE_DIR
from leanup.repo.cache_server import run_cache_server
from leanup.repo.mathlib_cache import MathlibCacheManager, normalize_lean_version
from leanup.repo.project_setup import LeanProjectSetup


PACKAGES_CACHE_ROOT = LEANUP_CACHE_DIR / "mathlib"


@click.command(name="pack")
@click.argument("lean_version")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=PACKAGES_CACHE_ROOT,
    help="Mathlib cache root containing packages/<version>/packages and archives/<version>/packages.tar.gz.",
)
@click.option(
    "--pigz/--no-pigz",
    default=True,
    help="Use pigz for parallel compression when it is available.",
)
def pack_cache(lean_version: str, output_dir: Path, pigz: bool) -> None:
    """Pack cached packages/<version>/packages into archives/<version>/packages.tar.gz."""
    manager = MathlibCacheManager(cache_root=output_dir)
    version = normalize_lean_version(lean_version)
    packages_dir = manager.ensure_local_cache(version)
    archive = manager.get_local_archive_path(version)

    if packages_dir is None:
        raise click.ClickException(
            f"Packages cache not found: {manager.get_local_packages_dir(version)}. Run 'leanup cache create {version}' or 'leanup cache get {version} --base-url ...' first."
        )

    try:
        packed = manager.pack_packages_archive(packages_dir, archive, use_pigz=pigz)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(str(packed))


@click.command(name="unpack")
@click.argument("lean_version")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=PACKAGES_CACHE_ROOT,
    help="Mathlib cache root containing packages/<version>/packages and archives/<version>/packages.tar.gz.",
)
def unpack_cache(lean_version: str, cache_dir: Path) -> None:
    """Unpack archives/<version>/packages.tar.gz into packages/<version>/packages."""
    manager = MathlibCacheManager(cache_root=cache_dir)
    version = normalize_lean_version(lean_version)
    archive = manager.get_local_archive_path(version)

    try:
        packages_dir = manager.extract_archive(archive, manager.get_local_packages_dir(version))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(str(packages_dir))


@click.command(name="list")
@click.option(
    "--local",
    "source",
    flag_value="local",
    default=True,
    help="List local mathlib package caches.",
)
@click.option(
    "--remote",
    "remote_url",
    help="List remote mathlib package caches using this base URL.",
)
def list_cache(source: str, remote_url: str | None) -> None:
    """List available mathlib package caches."""
    manager = MathlibCacheManager()
    entries = manager.list_remote_entries(remote_url) if remote_url else manager.list_entries()

    if not entries:
        click.echo("No mathlib caches found.")
        return

    for entry in entries:
        if remote_url:
            click.echo(f"{entry.version} {manager.build_archive_url(entry.version, remote_url)}")
        else:
            click.echo(entry.version)


@click.command(name="get")
@click.argument("lean_version")
@click.option("--remote", "remote_url", required=True, help="Base URL serving /packages/mathlib/<version>/packages.tar.gz.")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=PACKAGES_CACHE_ROOT,
    help="Mathlib cache root containing packages/<version>/packages and archives/<version>/packages.tar.gz.",
)
def get_cache(lean_version: str, remote_url: str, cache_dir: Path) -> None:
    """Download packages.tar.gz into local cache and extract packages/<version>/packages."""
    manager = MathlibCacheManager(cache_root=cache_dir)

    try:
        packages_dir = manager.fetch_packages(lean_version, remote_url)
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
    default=PACKAGES_CACHE_ROOT,
    help="Mathlib cache root containing packages/ and archives/ subdirectories.",
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
