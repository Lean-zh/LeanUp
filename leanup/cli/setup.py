from __future__ import annotations

from pathlib import Path

import click

from leanup.cli.interaction import (
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    ask_confirm,
    ask_text,
    resolve_interactive_mode,
)
from leanup.repo.project_setup import LeanProjectSetup, SetupConfig


def _require_non_empty(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise click.ClickException(f"{field_name} is required.")
    return cleaned


@click.command(name="setup")
@click.argument("path", required=False, type=click.Path(path_type=Path))
@click.option(
    "--lean-version",
    "-v",
    help="Lean version like v4.27.0 or 4.27.0.",
)
@click.option("--name", help="Lake project name. Defaults to the target directory name.")
@click.option(
    "--mathlib/--no-mathlib",
    default=True,
    help="Enable or disable the mathlib dependency.",
)
@click.option(
    "--dependency-mode",
    "-m",
    type=click.Choice(["symlink", "copy"]),
    default=None,
    help="Attach cached mathlib packages via symlink, or copy them into the project.",
)
@click.option("--force", "-f", is_flag=True, help="Replace the target directory if it exists.")
@click.option(
    "--interactive/--no-interactive",
    "-i/-I",
    default=None,
    help="Auto prompt on missing args, -i forces interactive, -I disables it.",
)
def setup_project(
    path: Path | None,
    lean_version: str | None,
    name: str | None,
    mathlib: bool,
    dependency_mode: str | None,
    force: bool,
    interactive: bool | None,
) -> None:
    """Create a Lean project with a pinned toolchain and optional mathlib cache reuse."""
    usage = "Usage: leanup setup [PATH] --lean-version <version> [--name <name>] [--mathlib/--no-mathlib] [--dependency-mode symlink|copy] [--force] [-i|-I]"
    missing_required = path is None or not lean_version
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
        message="Missing required setup path or Lean version and no TTY is available for interactive prompts.",
        usage=usage,
    )

    if missing_required and not need_prompt:
        raise click.ClickException("Missing required setup path or Lean version.")

    if need_prompt:
        path_input = _require_non_empty(
            ask_text("Project directory", default=str(path) if path else ""),
            "Project directory",
        )
        path = Path(path_input)
        lean_version = _require_non_empty(
            ask_text("Lean version", default=lean_version or ""),
            "Lean version",
        )
        name = ask_text("Lake project name", default=name or path.name) or None
        mathlib = ask_confirm("Enable mathlib dependency?", default=mathlib)

        preview_mode = None
        try:
            preview_mode = SetupConfig(
                target_dir=path,
                lean_version=lean_version,
                project_name=name,
                mathlib=mathlib,
                dependency_mode=dependency_mode,
                force=force,
            ).resolved_dependency_mode
        except ValueError:
            preview_mode = dependency_mode

        default_mode = preview_mode or dependency_mode or ("copy" if not mathlib else "symlink")

        if mathlib:
            dependency_mode = ask_text(
                "Dependency mode (symlink/copy)",
                default=default_mode,
            ).strip() or default_mode
        else:
            dependency_mode = "copy"

        force = ask_confirm("Replace the target directory if it exists?", default=force)

    config = SetupConfig(
        target_dir=path,
        lean_version=lean_version,
        project_name=name,
        mathlib=mathlib,
        dependency_mode=dependency_mode,
        force=force,
    )
    manager = LeanProjectSetup()

    try:
        result = manager.setup(config)
    except (ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"✓ Project ready: {result.target_dir}")
    click.echo(f"  Lean version: {result.lean_version}")
    click.echo(f"  Mathlib: {'enabled' if result.mathlib else 'disabled'}")
    click.echo(f"  Dependency mode: {result.dependency_mode}")
    if result.cache_dir:
        click.echo(f"  Cache dir: {result.cache_dir}")
    if result.used_cache:
        click.echo(f"  Reused cached mathlib packages via {result.dependency_mode}.")
    else:
        click.echo("  Refreshed the shared mathlib package cache for this Lean version.")
