from __future__ import annotations

from pathlib import Path

import click

from leanup.repo.mathlib_cache import MathlibCacheManager, normalize_lean_version


@click.group()
def mathlib() -> None:
    """Manage mathlib-specific helpers and caches."""


@mathlib.group()
def cache() -> None:
    """Manage reusable mathlib package caches."""


@cache.command(name="list")
def list_cache() -> None:
    """List available mathlib caches."""
    manager = MathlibCacheManager()
    entries = manager.list_entries()

    if not entries:
        click.echo("No mathlib caches found.")
        return

    for entry in entries:
        click.echo(entry.version)


@cache.command(name="pack")
@click.option(
    "--repo-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path.cwd,
    help="Lean repository directory containing .lake/packages.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    required=True,
    help="Directory where <version>/packages.tar.gz will be written.",
)
@click.option(
    "--lean-version",
    required=True,
    help="Lean version like v4.22.0.",
)
@click.option(
    "--pigz/--no-pigz",
    default=False,
    help="Use pigz for parallel compression when it is available.",
)
def pack_cache(repo_dir: Path, output_dir: Path, lean_version: str, pigz: bool) -> None:
    """Pack current repository .lake/packages into a versioned cache archive."""
    manager = MathlibCacheManager()
    version = normalize_lean_version(lean_version)
    packages_dir = repo_dir / ".lake" / "packages"
    archive = output_dir / version / "packages.tar.gz"

    try:
        packed = manager.pack_packages_archive(packages_dir, archive, use_pigz=pigz)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(str(packed))
