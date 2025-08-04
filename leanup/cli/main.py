import click
import sys
from pathlib import Path
from typing import Optional

from leanup.repo.elan import ElanManager
from leanup.utils.custom_logger import setup_logger
from leanup.cli.repo import repo

logger = setup_logger("leanup_cli")


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """LeanUp - Lean project management tool"""
    ctx.ensure_object(dict)


@cli.command()
def init():
    """Install latest elan"""
    # Install elan
    elan_manager = ElanManager()
    if not elan_manager.is_elan_installed():
        click.echo("Installing elan...")
        if elan_manager.install_elan():
            click.echo("✓ elan installed successfully")
        else:
            click.echo("✗ Failed to install elan", err=True)
            sys.exit(1)
    else:
        click.echo("✓ elan is already installed")


@cli.command()
@click.argument('version', required=False)
@click.option('--force', '-f', is_flag=True, help='Force reinstall')
def install(version: Optional[str], force: bool):
    """Install Lean toolchain version via elan"""
    elan_manager = ElanManager()
    
    if not elan_manager.is_elan_installed():
        click.echo("✗ elan is not installed, trying to install...")
        if not elan_manager.install_elan():
            click.echo("✗ Failed to install elan", err=True)
            sys.exit(1)
        click.echo("✓ elan installed successfully")
    
    if not version:
        # Install latest stable version
        click.echo("Installing latest Lean toolchain...")
        cmd = ['toolchain', 'install', 'stable']
    else:
        # Install specific version
        click.echo(f"Installing Lean toolchain {version}...")
        cmd = ['toolchain', 'install', version]
    if force:
        cmd.append('--force')
    try:
        result = elan_manager.proxy_elan_command(cmd)
        if result == 0:
            click.echo(f"✓ Lean toolchain {version} installed")
        else:
            click.echo(f"✗ Failed to install Lean toolchain {version}", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Failed to install Lean toolchain {version}: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Show status information"""
    elan_manager = ElanManager()
    
    click.echo("=== LeanUp Status ===")
    
    # elan status
    if elan_manager.is_elan_installed():
        version = elan_manager.get_elan_version()
        click.echo(f"elan: ✓ installed (version: {version})")
        
        # Show toolchains
        toolchains = elan_manager.get_installed_toolchains()
        if toolchains:
            click.echo(f"Toolchains: {', '.join(toolchains)}")
        else:
            click.echo("Toolchains: none")
    else:
        click.echo("elan: ✗ not installed")


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def elan(args):
    """Proxy elan commands"""
    elan_manager = ElanManager()
    
    if not elan_manager.is_elan_installed():
        click.echo("elan is not installed. Run 'leanup init' first.", err=True)
        sys.exit(1)
    
    # Execute elan command
    try:
        result = elan_manager.proxy_elan_command(list(args))
        sys.exit(result)
    except KeyboardInterrupt:
        click.echo("\nInterrupted", err=True)
        sys.exit(1)

cli.add_command(repo)

if __name__ == '__main__':
    cli()