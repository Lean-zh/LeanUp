import click

from leanup.cli.mathlib import mathlib
from leanup.cli.repo import repo
from leanup.cli.setup import setup_project
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("leanup_cli")


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """LeanUp - Lean project management tool"""
    ctx.ensure_object(dict)


@click.group()
def cache() -> None:
    """Manage reusable caches."""


cache.add_command(mathlib)


cli.add_command(setup_project)
cli.add_command(cache)


cli.add_command(repo)
