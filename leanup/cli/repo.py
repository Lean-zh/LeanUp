import click
import shutil
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from leanup.const import LEANUP_CACHE_DIR
from leanup.repo.manager import RepoManager, LeanRepo, InstallConfig
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("repo_cli")

@click.group()
def repo():
    """Repository management commands"""
    pass


@repo.command()
@click.argument('suffix', required=False)
@click.option('--source', '-s', help='Repository source', default='https://github.com')
@click.option('--branch', '-b', help='Branch or tag to clone')
@click.option('--force', '-f', is_flag=True, help='Replace existing directory')
@click.option('--dest-dir', '-d', help='Destination directory', type=click.Path(path_type=Path), default=LEANUP_CACHE_DIR / "repos")
@click.option('--dest-name', '-n', help='Destination name')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--lake-update', is_flag=True, help='Run lake update after cloning', default=True)
@click.option('--lake-build', is_flag=True, help='Run lake build after cloning', default=True)
@click.option('--build-packages', help='Packages to build after cloning')
def install(suffix: str, source: str, branch: Optional[str], force: bool,
            dest_dir: Optional[Path], dest_name: Optional[str], interactive: bool, lake_update: bool, lake_build: bool, build_packages: str):
    """Install a repository"""
    if interactive:
        suffix = click.prompt("Repository name(required)", type=str, default=suffix)
        source = click.prompt("Repository source", type=str, default=source)
        branch = click.prompt("Branch or tag", type=str, default=branch or "")
        config = InstallConfig(
            suffix=suffix,
            source=source,
            branch=branch
        )
        if dest_dir:
            config.dest_dir = dest_dir
        config.dest_dir = click.prompt("Destination directory", type=click.Path(path_type=Path), default=config.dest_dir)
        config.dest_name = click.prompt("Destination name", type=str, default=config.dest_name)
        config.lake_update = click.confirm("Run lake update after cloning?", default=lake_update)
        config.lake_build = click.confirm("Run lake build after cloning?", default=lake_build)
        build_packages = click.prompt("Packages to build after cloning(e.g. REPL,REPL.Main)", type=str, default=build_packages or "" )
        if build_packages:
            config.build_packages = build_packages.split(',')
        if config.dest_path.exists():
            config.override = click.confirm(f"Repository {config.dest_name} already exists in {config.dest_dir}. Override?", default=False)
            if not config.override:
                click.echo(f"Aborted.", err=True)
                sys.exit(1)
    else:
        config = InstallConfig(
            suffix=suffix,
            source=source,
            branch=branch,
            dest_dir=dest_dir,
            dest_name=dest_name,
            lake_update=lake_update,
            lake_build=lake_build,
            build_packages=build_packages,
            override=force
        )
    if not config.is_valid:
        click.echo("Error: Repository name is required", err=True)
        sys.exit(1)
    config.install()

@repo.command()
@click.option('--name', '-n', help='Filter by repository name')
@click.option('--search-dir', '-s', help='Directory to search for repositories', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
              default=LEANUP_CACHE_DIR / "repos")
def list(name: Optional[str], search_dir: Path):
    """List repositories in the specified directory"""
    
    if not search_dir.exists():
        click.echo(f"Directory {search_dir} doesn't exist.", err=True)
        sys.exit(1)
    names = [dir.name for dir in search_dir.iterdir() if dir.is_dir()]

    if name:
        names = [n for n in names if name in n]
    
    for name in names:
        click.echo(name)
