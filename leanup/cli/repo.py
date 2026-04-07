import click
from pathlib import Path
from typing import Optional

from leanup.const import LEANUP_CACHE_DIR
from leanup.repo.manager import InstallConfig
from leanup.cli.interaction import (
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    ask_confirm,
    ask_text,
    resolve_interactive_mode,
)
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("repo_cli")


@click.group()
def repo():
    """Repository management commands"""
    pass


@repo.command()
@click.argument("suffix", required=False)
@click.option("--source", "-s", help="Repository source", default="https://github.com")
@click.option("--branch", "-b", help="Branch or tag to clone")
@click.option("--force", "-f", is_flag=True, help="Replace existing directory")
@click.option(
    "--dest-dir",
    "-d",
    help="Destination directory",
    type=click.Path(path_type=Path),
    default=LEANUP_CACHE_DIR / "repos",
)
@click.option("--dest-name", "-n", help="Destination name")
@click.option(
    "--interactive/--no-interactive",
    "-i/-I",
    default=None,
    help="Auto prompt on missing args, -i forces interactive, -I disables it.",
)
@click.option(
    "--lake-update", is_flag=True, help="Run lake update after cloning", default=True
)
@click.option(
    "--lake-build", is_flag=True, help="Run lake build after cloning", default=True
)
@click.option("--build-packages", help="Packages to build after cloning")
def install(
    suffix: str,
    source: str,
    branch: Optional[str],
    force: bool,
    dest_dir: Optional[Path],
    dest_name: Optional[str],
    interactive: bool,
    lake_update: bool,
    lake_build: bool,
    build_packages: str,
):
    """Install a repository"""
    usage = "Usage: leanup repo install [SUFFIX] [--source <url>] [--branch <branch>] [--dest-dir <path>] [--dest-name <name>] [--lake-update] [--lake-build] [--build-packages <csv>] [-i|-I]"
    missing_required = not suffix
    interactive, can_prompt, force_interactive, _, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=missing_required,
        )
    )

    abort_if_force_without_tty(force_interactive, can_prompt, usage)
    abort_if_missing_without_tty(
        missing_required=missing_required,
        interactive=interactive,
        can_prompt=can_prompt,
        message="Missing required repository suffix and no TTY is available for interactive prompts.",
        usage=usage,
    )

    if missing_required and not need_prompt:
        raise click.ClickException("Missing required repository suffix.")

    if need_prompt:
        suffix = ask_text("Suffix (user/repo)", default=suffix or "")
        source = ask_text("Repository source", default=source)
        branch = ask_text("Branch or tag", default=branch or "") or None
        dest_dir = Path(ask_text("Destination directory", default=str(dest_dir)))
        preview = InstallConfig(
            suffix=suffix,
            source=source,
            branch=branch,
            dest_dir=dest_dir,
            dest_name=dest_name,
        )
        dest_name = ask_text("Destination name", default=dest_name or preview.dest_name)
        lake_update = ask_confirm("Run lake update after cloning?", default=lake_update)
        lake_build = ask_confirm("Run lake build after cloning?", default=lake_build)
        build_packages = ask_text(
            "Packages to build after cloning (e.g. REPL,REPL.Main)",
            default=build_packages or "",
        )

    config = InstallConfig(
        suffix=suffix,
        source=source,
        branch=branch,
        dest_dir=dest_dir,
        dest_name=dest_name,
        lake_update=lake_update,
        lake_build=lake_build,
        build_packages=build_packages,
        override=force,
    )

    if need_prompt and config.dest_path.exists() and not config.override:
        config.override = ask_confirm(
            f"Repository {config.dest_name} already exists in {config.dest_dir}. Override?",
            default=False,
        )
        if not config.override:
            click.echo("Aborted.", err=True)
            raise click.Abort()

    if not config.is_valid:
        click.echo("Error: Repository name is required", err=True)
        raise click.Abort()
    config.install()


@repo.command()
@click.option("--name", "-n", help="Filter by repository name")
@click.option(
    "--search-dir",
    "-s",
    help="Directory to search for repositories",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=LEANUP_CACHE_DIR / "repos",
)
def list(name: Optional[str], search_dir: Path):
    """List repositories in the specified directory"""

    if not search_dir.exists():
        raise click.ClickException(f"Directory {search_dir} doesn't exist.")
    names = [dir.name for dir in search_dir.iterdir() if dir.is_dir()]

    if name:
        names = [n for n in names if name in n]

    for name in names:
        click.echo(name)
