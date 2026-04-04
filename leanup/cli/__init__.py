import click
import sys
from pathlib import Path
from typing import Optional

from leanup.repo.elan import ElanManager
from leanup.repo.manager import LeanRepo
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
def install(version: Optional[str]):
    """Install Lean toolchain version via elan"""
    elan_manager = ElanManager()
    
    if not elan_manager.is_elan_installed():
        click.echo("✗ elan is not installed, trying to install...")
        if not elan_manager.install_elan():
            click.echo("✗ Failed to install elan", err=True)
            sys.exit(1)
        click.echo("✓ elan installed successfully")
    
    requested_version = version or 'stable'
    if not elan_manager.install_lean(version):
        click.echo(f"✗ Failed to install Lean toolchain {requested_version}", err=True)
        sys.exit(1)
    
    click.echo(f"✓ Lean toolchain {requested_version} installed")


@cli.command()
@click.argument('version', required=False)
@click.option('--project-name', '-n', default='lean4web', show_default=True, help='Project name')
@click.option('--dest-dir', '-d', type=click.Path(path_type=Path), default=Path('.'), show_default=True, help='Destination directory')
@click.option('--dest-name', help='Destination directory name (defaults to Lean version)')
@click.option('--force', '-f', is_flag=True, help='Replace existing directory')
@click.option('--interactive', '-i', is_flag=True, help='Force interactive mode')
@click.option('--no-interactive', '-I', is_flag=True, help='Disable interactive prompts')
def create(
    version: Optional[str],
    project_name: str,
    dest_dir: Path,
    dest_name: Optional[str],
    force: bool,
    interactive: bool,
    no_interactive: bool,
):
    """Create a new Lean mathlib project."""
    if interactive and no_interactive:
        click.echo("Error: -i and -I cannot be used together", err=True)
        sys.exit(1)

    prompt_for_missing = not no_interactive
    if interactive or version is None:
        if not prompt_for_missing:
            click.echo("Error: Lean version is required", err=True)
            sys.exit(1)
        version = click.prompt("Lean version (required)", type=str, default=version or "")

    if version is None:
        click.echo("Error: Lean version is required", err=True)
        sys.exit(1)

    try:
        normalized_version = LeanRepo.normalize_lean_version(version)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if interactive:
        project_name = click.prompt("Project name", type=str, default=project_name)
        dest_dir = click.prompt(
            "Destination directory",
            type=click.Path(path_type=Path),
            default=dest_dir,
        )
        dest_name = click.prompt(
            "Destination name",
            type=str,
            default=dest_name or normalized_version,
        )
    elif dest_name is None:
        dest_name = normalized_version

    if dest_name is None:
        click.echo("Error: Destination name is required", err=True)
        sys.exit(1)

    target_dir = dest_dir / dest_name
    if target_dir.exists() and not force:
        if not prompt_for_missing:
            click.echo(f"Error: Directory {target_dir} already exists. Use --force to replace it.", err=True)
            sys.exit(1)
        force = click.confirm(
            f"Directory {target_dir} already exists. Overwrite?",
            default=False,
        )
        if not force:
            click.echo("Aborted.", err=True)
            sys.exit(1)

    click.echo("INFO: Start Lean project creation")
    click.echo(f"Creating new Lean 4 project of version {normalized_version}...")
    repo = LeanRepo(target_dir)
    try:
        repo.create_math_project(
            lean_version=normalized_version,
            project_name=project_name,
            force=force,
            progress=click.echo,
        )
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    click.echo(f"✓ Project created at {target_dir}")


@cli.command()
def status():
    """Show status information"""
    elan_manager = ElanManager()
    
    click.echo("=== LeanUp Status ===")
    
    # elan status
    if elan_manager.is_elan_installed():
        version = elan_manager.get_elan_version()
        click.echo(f"\nelan version: {version}")
        click.echo("---------------------\n")
        
        # Show toolchains
        elan_manager.proxy_elan_command(['show'])
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
