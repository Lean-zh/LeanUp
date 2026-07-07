from __future__ import annotations

from pathlib import Path
import os

import click
import requests

from leanup.ops import environment as ops
from leanup.paths import cache_dir, elan_home, set_env_value


@click.command(name="init")
@click.option("--home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="LeanUp home directory.")
@click.option("--server", help="Default LeanUp server URL to write into .env.")
@click.option("--dry-run", is_flag=True, help="Show paths without writing.")
def init_cmd(home: Path | None, server: str | None, dry_run: bool) -> None:
    """Initialize LeanUp home/config/cache directories."""
    root = home or Path(os.environ.get("LEANUP_HOME", Path.home() / ".leanup")).expanduser()
    if dry_run:
        click.echo(str(root))
        for rel in [".env", "config", "repos", "cache/serve", "cache/local", "cache/downloads", "logs", "state/locks"]:
            click.echo(str(root / rel))
        return
    click.echo(str(ops.init_leanup_home(root, server)))


@click.group(name="config")
def config_cmd() -> None:
    """Manage LeanUp .env configuration."""


@config_cmd.command(name="show")
def config_show() -> None:
    ops.init_leanup_home()
    click.echo(f"LEANUP_HOME={Path(os.environ.get('LEANUP_HOME', Path.home() / '.leanup')).expanduser()}")
    click.echo(f"LEANUP_CACHE_DIR={cache_dir()}")
    click.echo(f"LEANUP_ELAN_HOME={elan_home()}")
    if ops.resolve_server():
        click.echo(f"LEANUP_SERVER_URL={ops.resolve_server()}")


@config_cmd.command(name="set-server")
@click.argument("url")
def config_set_server(url: str) -> None:
    click.echo(str(set_env_value("LEANUP_SERVER_URL", url)))


@click.group(name="elan")
def elan_cmd() -> None:
    """Manage base elan runtime archives and installation."""


@elan_cmd.command(name="pack")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="Source ELAN_HOME.")
def elan_pack(elan_home: Path | None) -> None:
    try:
        click.echo(str(ops.pack_elan(elan_home)))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@elan_cmd.command(name="get")
@click.option("--server", help="LeanUp server URL.")
def elan_get(server: str | None) -> None:
    try:
        click.echo(str(ops.get_elan(server)))
    except (ValueError, requests.RequestException) as exc:
        raise click.ClickException(str(exc)) from exc


@elan_cmd.command(name="unpack")
@click.option("--archive", type=click.Path(path_type=Path, dir_okay=False), help="elan archive path.")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="Target ELAN_HOME.")
def elan_unpack(archive: Path | None, elan_home: Path | None) -> None:
    try:
        click.echo(str(ops.unpack_elan(archive, elan_home)))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@elan_cmd.command(name="install")
@click.option("--server", help="LeanUp server URL.")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="Target ELAN_HOME.")
def elan_install(server: str | None, elan_home: Path | None) -> None:
    try:
        click.echo(str(ops.install_elan(server, elan_home)))
    except (ValueError, requests.RequestException) as exc:
        raise click.ClickException(str(exc)) from exc


@elan_cmd.command(name="check")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="ELAN_HOME to check.")
def elan_check(elan_home: Path | None) -> None:
    try:
        click.echo(ops.check_elan(elan_home))
    except (ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc


@click.group(name="lean")
def lean_cmd() -> None:
    """Manage Lean toolchains under ELAN_HOME."""


@lean_cmd.command(name="pack")
@click.argument("version")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="Source ELAN_HOME.")
def lean_pack(version: str, elan_home: Path | None) -> None:
    try:
        click.echo(str(ops.pack_lean(version, elan_home)))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@lean_cmd.command(name="get")
@click.argument("version")
@click.option("--server", help="LeanUp server URL.")
def lean_get(version: str, server: str | None) -> None:
    try:
        click.echo(str(ops.get_lean(version, server)))
    except (ValueError, requests.RequestException) as exc:
        raise click.ClickException(str(exc)) from exc


@lean_cmd.command(name="unpack")
@click.argument("version")
@click.option("--archive", type=click.Path(path_type=Path, dir_okay=False), help="toolchain archive path.")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="Target ELAN_HOME.")
def lean_unpack(version: str, archive: Path | None, elan_home: Path | None) -> None:
    try:
        click.echo(str(ops.unpack_lean(version, archive, elan_home)))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@lean_cmd.command(name="install")
@click.argument("version")
@click.option("--server", help="LeanUp server URL.")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="Target ELAN_HOME.")
def lean_install(version: str, server: str | None, elan_home: Path | None) -> None:
    try:
        click.echo(str(ops.install_lean(version, server, elan_home)))
    except (ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc


@lean_cmd.command(name="list")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="ELAN_HOME.")
def lean_list(elan_home: Path | None) -> None:
    for item in ops.list_installed_lean(elan_home):
        click.echo(item)


@lean_cmd.command(name="check")
@click.argument("version")
@click.option("--elan-home", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="ELAN_HOME.")
def lean_check(version: str, elan_home: Path | None) -> None:
    try:
        click.echo(ops.check_lean(version, elan_home))
    except (ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
