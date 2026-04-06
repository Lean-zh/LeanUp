from __future__ import annotations

import click

from leanup.repo.elan import ElanManager


def ensure_elan_installed() -> ElanManager:
    elan_manager = ElanManager()
    if elan_manager.is_elan_installed():
        return elan_manager

    click.echo("Installing elan...")
    if not elan_manager.install_elan():
        raise click.ClickException("Failed to install elan")
    click.echo("✓ elan installed successfully")
    return elan_manager


def init_elan() -> None:
    elan_manager = ElanManager()
    if elan_manager.is_elan_installed():
        click.echo("✓ elan is already installed")
        return
    click.echo("Installing elan...")
    if not elan_manager.install_elan():
        raise click.ClickException("Failed to install elan")
    click.echo("✓ elan installed successfully")


def install_lean_toolchain(version: str | None) -> None:
    elan_manager = ensure_elan_installed()
    requested = version or "stable"
    if not elan_manager.install_lean(version):
        raise click.ClickException(f"Failed to install Lean toolchain {requested}")
    click.echo(f"✓ Lean toolchain {requested} installed")


def show_status() -> None:
    elan_manager = ElanManager()
    click.echo("=== LeanUp Status ===")
    if not elan_manager.is_elan_installed():
        click.echo("elan: ✗ not installed")
        return
    version = elan_manager.get_elan_version()
    click.echo(f"\nelan version: {version}")
    click.echo("---------------------\n")
    elan_manager.proxy_elan_command(["show"])


def proxy_elan(args: list[str]) -> int:
    elan_manager = ElanManager()
    if not elan_manager.is_elan_installed():
        raise click.ClickException("elan is not installed. Run 'leanup init' first.")
    return elan_manager.proxy_elan_command(list(args))
