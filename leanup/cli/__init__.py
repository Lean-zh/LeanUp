import click

from leanup.cli.assets import config_cmd, elan_cmd, init_cmd, lean_cmd
from leanup.cli.cache_ops import create_cache, get_cache, list_cache, mathlib_check, pack_cache, serve_cache, unpack_cache
from leanup.cli.repo import repo
from leanup.cli.setup import setup_project
from leanup.cli.toolchains import toolchains
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("leanup_cli")


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """LeanUp - Lean project management tool"""
    ctx.ensure_object(dict)


@click.group()
def mathlib() -> None:
    """Manage mathlib projects and package caches."""


mathlib.add_command(setup_project)
mathlib.add_command(pack_cache)
mathlib.add_command(unpack_cache)
mathlib.add_command(list_cache)
mathlib.add_command(get_cache)
mathlib.add_command(create_cache)
mathlib.add_command(mathlib_check)


cli.add_command(init_cmd)
cli.add_command(elan_cmd)
cli.add_command(lean_cmd)
cli.add_command(config_cmd)
cli.add_command(setup_project)
cli.add_command(mathlib)
cli.add_command(serve_cache)
cli.add_command(toolchains)


cli.add_command(repo)
