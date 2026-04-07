import click
import sys

from leanup.utils.custom_logger import setup_logger
from leanup.cli.mathlib import mathlib
from leanup.cli.repo import repo
from leanup.cli.setup import setup_project
from leanup.cli.elan_ops import (
    init_elan,
    install_lean_toolchain,
    proxy_elan,
    show_status,
)

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
    init_elan()


@cli.command()
@click.argument("version", required=False)
def install(version):
    """Install Lean toolchain version via elan"""
    install_lean_toolchain(version)


@cli.command()
def status():
    """Show status information"""
    show_status()


cli.add_command(setup_project)
cli.add_command(mathlib)


@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def elan(args):
    """Proxy elan commands"""
    try:
        result = proxy_elan(list(args))
        sys.exit(result)
    except KeyboardInterrupt:
        click.echo("\nInterrupted", err=True)
        sys.exit(1)


cli.add_command(repo)
