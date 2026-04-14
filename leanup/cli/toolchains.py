from __future__ import annotations

from pathlib import Path
import tempfile

import click
import requests

from leanup.const import LEANUP_CACHE_DIR
from leanup.repo.toolchain_cache import ToolchainCacheManager


TOOLCHAIN_CACHE_ROOT = LEANUP_CACHE_DIR / "toolchains"


@click.group(name="toolchains")
def toolchains() -> None:
    """Manage elan and Lean toolchain archives."""


@toolchains.command(name="list")
@click.option("--local", "mode", flag_value="local", default=True, help="List local toolchain archives.")
@click.option("--remote", "remote_url", help="List remote toolchain archives using this base URL.")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=TOOLCHAIN_CACHE_ROOT,
    help="Toolchain cache root.",
)
def list_toolchains(mode: str, remote_url: str | None, cache_dir: Path) -> None:
    manager = ToolchainCacheManager(cache_root=cache_dir)
    if remote_url:
        has_base, versions = manager.list_remote(remote_url)
        if has_base:
            click.echo(f"base {manager.build_base_url(remote_url)}")
        for version in versions:
            click.echo(f"{version} {manager.build_toolchain_url(version, remote_url)}")
        if not has_base and not versions:
            click.echo("No toolchain archives found.")
        return

    entries = manager.list_local_versions()
    if manager.has_local_base_archive():
        click.echo("base")
    for version in entries:
        click.echo(version)
    if not manager.has_local_base_archive() and not entries:
        click.echo("No toolchain archives found.")


@toolchains.command(name="init")
@click.option("--url", help="Download base .elan archive from this service URL instead of official elan installer.")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=TOOLCHAIN_CACHE_ROOT,
    help="Toolchain cache root.",
)
@click.option(
    "--elan-home",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path(tempfile.gettempdir()) / "leanup-elan",
    help="Target .elan directory.",
)
def init_toolchains(url: str | None, cache_dir: Path, elan_home: Path) -> None:
    manager = ToolchainCacheManager(cache_root=cache_dir, elan_home=elan_home)
    try:
        result = manager.init_base(url)
    except (ValueError, RuntimeError, requests.RequestException) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(result))


@toolchains.command(name="pack")
@click.argument("lean_version", required=False)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=TOOLCHAIN_CACHE_ROOT,
    help="Toolchain cache root.",
)
@click.option(
    "--elan-home",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path(tempfile.gettempdir()) / "leanup-elan",
    help="Source .elan directory.",
)
def pack_toolchain(lean_version: str | None, cache_dir: Path, elan_home: Path) -> None:
    manager = ToolchainCacheManager(cache_root=cache_dir, elan_home=elan_home)
    try:
        archive = manager.pack_base_archive() if lean_version is None else manager.pack_toolchain_archive(lean_version)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(archive))


@toolchains.command(name="unpack")
@click.argument("lean_version")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=TOOLCHAIN_CACHE_ROOT,
    help="Toolchain cache root.",
)
@click.option(
    "--elan-home",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path(tempfile.gettempdir()) / "leanup-elan",
    help="Target .elan directory.",
)
def unpack_toolchain(lean_version: str, cache_dir: Path, elan_home: Path) -> None:
    manager = ToolchainCacheManager(cache_root=cache_dir, elan_home=elan_home)
    try:
        path = manager.unpack_toolchain_archive(lean_version)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(path))


@toolchains.command(name="get")
@click.argument("lean_version")
@click.option("--remote", required=True, help="Base URL serving /toolchains/<version>/toolchain.tar.gz.")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=TOOLCHAIN_CACHE_ROOT,
    help="Toolchain cache root.",
)
@click.option(
    "--elan-home",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=Path(tempfile.gettempdir()) / "leanup-elan",
    help="Target .elan directory.",
)
def get_toolchain(lean_version: str, remote: str, cache_dir: Path, elan_home: Path) -> None:
    manager = ToolchainCacheManager(cache_root=cache_dir, elan_home=elan_home)
    try:
        path = manager.fetch_toolchain(lean_version, remote)
    except (ValueError, requests.RequestException) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(path))
