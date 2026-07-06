from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import click
import requests

from leanup.const import LEANUP_CACHE_DIR
from leanup.ops.environment import safe_extract, tar_directory
from leanup.paths import cache_dir as leanup_cache_dir
from leanup.repo.cache_server import run_cache_server
from leanup.repo.mathlib_cache import MathlibCacheManager, normalize_lean_version, remove_path
from leanup.repo.project_setup import LeanProjectSetup


PACKAGES_CACHE_ROOT = LEANUP_CACHE_DIR / "mathlib"


def _mathlib_local_lake_dir(version: str) -> Path:
    return leanup_cache_dir() / "local" / "mathlib" / normalize_lean_version(version) / ".lake"


def _mathlib_lake_archive(version: str) -> Path:
    return leanup_cache_dir() / "serve" / "mathlib" / normalize_lean_version(version) / "mathlib-lake.tar.gz"


def _extract_lake_archive(archive: Path, target_lake: Path) -> Path:
    if not archive.exists():
        raise ValueError(f"Archive not found: {archive}")
    parent = target_lake.parent
    parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix=".lake.", suffix=".tmp", dir=parent))
    try:
        safe_extract(archive, temp_root)
        extracted = temp_root / ".lake"
        if not extracted.exists() or not extracted.is_dir():
            raise ValueError(f"Archive does not contain top-level .lake/ directory: {archive}")
        final_temp = parent / ".lake.replace"
        remove_path(final_temp)
        extracted.replace(final_temp)
        remove_path(target_lake)
        final_temp.replace(target_lake)
        remove_path(temp_root)
        return target_lake
    except Exception:
        remove_path(temp_root)
        raise


@click.command(name="pack")
@click.argument("lean_version")
@click.option(
    "--source",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Mathlib workspace containing a .lake directory to archive.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=PACKAGES_CACHE_ROOT,
    help="Legacy mathlib packages cache root used when no .lake source/cache is available.",
)
@click.option(
    "--pigz/--no-pigz",
    default=True,
    help="Use pigz for legacy packages compression when it is available.",
)
def pack_cache(lean_version: str, source: Path | None, output_dir: Path, pigz: bool) -> None:
    """Pack Mathlib .lake when available, otherwise keep legacy packages cache behavior."""
    version = normalize_lean_version(lean_version)
    lake_dir = (source / ".lake") if source is not None else _mathlib_local_lake_dir(version)
    if lake_dir.exists():
        try:
            packed = tar_directory(lake_dir, ".lake", _mathlib_lake_archive(version))
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(str(packed))
        return

    manager = MathlibCacheManager(cache_root=output_dir)
    packages_dir = manager.ensure_local_cache(version)
    archive = manager.get_local_archive_path(version)

    if packages_dir is None:
        raise click.ClickException(
            f"Mathlib .lake not found: {lake_dir}. Legacy packages cache not found: {manager.get_local_packages_dir(version)}. "
            f"Run 'leanup cache create {version}' or 'leanup cache get {version} --base-url ...' first."
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
    help="Legacy mathlib packages cache root.",
)
def unpack_cache(lean_version: str, cache_dir: Path) -> None:
    """Unpack Mathlib .lake archive when present, otherwise use legacy packages cache."""
    version = normalize_lean_version(lean_version)
    lake_archive = _mathlib_lake_archive(version)
    if lake_archive.exists():
        try:
            lake_dir = _extract_lake_archive(lake_archive, _mathlib_local_lake_dir(version))
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(str(lake_dir))
        return

    manager = MathlibCacheManager(cache_root=cache_dir)
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


@click.command(name="check")
@click.argument("lean_version")
@click.option(
    "--source",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Mathlib workspace to check. Defaults to current directory.",
)
@click.option(
    "--lean-bin",
    type=click.Path(path_type=Path, dir_okay=False),
    help="Lean executable to use when lake is unavailable.",
)
def mathlib_check(lean_version: str, source: Path | None, lean_bin: Path | None) -> None:
    """Check that a Mathlib environment can import Mathlib."""
    normalize_lean_version(lean_version)
    workspace = source or Path.cwd()
    if not workspace.exists():
        raise click.ClickException(f"Workspace not found: {workspace}")

    check_content = "import Mathlib\n\n#check Nat\n"
    with tempfile.TemporaryDirectory(prefix="leanup-mathlib-check-") as tmp:
        check_file = Path(tmp) / "CheckMathlib.lean"
        check_file.write_text(check_content, encoding="utf-8")
        if (workspace / "lakefile.lean").exists() or (workspace / "lakefile.toml").exists():
            command = ["lake", "env", "lean", str(check_file)]
            cwd = workspace
        else:
            command = [str(lean_bin or "lean"), str(check_file)]
            cwd = workspace
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "import Mathlib check failed"
        raise click.ClickException(message)
    click.echo("import Mathlib ok")


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
