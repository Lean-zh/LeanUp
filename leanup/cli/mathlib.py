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
@click.option(
    "--local-only",
    is_flag=True,
    help="Show only caches already imported into LeanUp's cache directory.",
)
@click.option(
    "--importable-only",
    is_flag=True,
    help="Show only versions that can be imported from the reference cache source.",
)
@click.option(
    "--source-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Override the reference cache directory to scan for packages.tar.gz archives.",
)
def list_cache(local_only: bool, importable_only: bool, source_dir: Path | None) -> None:
    """List available mathlib caches."""
    manager = MathlibCacheManager()
    entries = manager.list_entries(source_dir=source_dir)

    filtered = []
    for entry in entries:
        if local_only and not entry.local_available:
            continue
        if importable_only and not entry.importable:
            continue
        filtered.append(entry)

    if not filtered:
        click.echo("No mathlib caches found.")
        return

    for entry in filtered:
        status = []
        if entry.local_available:
            status.append("local")
        if entry.importable:
            status.append("importable")
        click.echo(f"{entry.version}\t{', '.join(status) or 'unavailable'}")
        click.echo(f"  local: {entry.local_path}")
        if entry.archive_path:
            click.echo(f"  archive: {entry.archive_path}")


@cache.command(name="import")
@click.argument("version", required=False)
@click.option("--all", "import_all", is_flag=True, help="Import all importable cache archives.")
@click.option("--force", is_flag=True, help="Replace an existing imported cache.")
@click.option(
    "--source-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    help="Override the reference cache directory containing versioned packages.tar.gz archives.",
)
def import_cache(
    version: str | None,
    import_all: bool,
    force: bool,
    source_dir: Path | None,
) -> None:
    """Import mathlib package caches into LeanUp's default cache directory."""
    if import_all and version:
        raise click.ClickException("Use either VERSION or --all, not both.")
    if not import_all and not version:
        raise click.ClickException("Missing VERSION. Use `leanup mathlib cache import <version>` or --all.")

    manager = MathlibCacheManager()
    targets = []
    if import_all:
        targets = [entry.version for entry in manager.list_entries(source_dir=source_dir) if entry.importable]
        if not targets:
            raise click.ClickException("No importable mathlib caches found.")
    else:
        targets = [normalize_lean_version(version)]

    for target in targets:
        try:
            packages_dir = manager.import_archive(target, source_dir=source_dir, force=force)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(f"Imported {target} -> {packages_dir}")
