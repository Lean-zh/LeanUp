from __future__ import annotations

from typing import Any

import click


def normalize_interactive(interactive):
    ctx = click.get_current_context(silent=True)
    if ctx:
        try:
            if (
                ctx.get_parameter_source("interactive")
                == click.core.ParameterSource.DEFAULT
            ):
                return None
        except Exception:
            pass
    return interactive


def is_interactive_available() -> bool:
    return (
        click.get_text_stream("stdin").isatty()
        and click.get_text_stream("stdout").isatty()
    )


def resolve_interactive_mode(interactive, auto_prompt_condition: bool):
    interactive = normalize_interactive(interactive)
    can_prompt = is_interactive_available()
    force_interactive = interactive is True
    auto_interactive = interactive is None and can_prompt and auto_prompt_condition
    need_prompt = force_interactive or auto_interactive
    return interactive, can_prompt, force_interactive, auto_interactive, need_prompt


def abort_if_force_without_tty(force_interactive, can_prompt, usage):
    if force_interactive and not can_prompt:
        click.echo("Interactive mode was requested, but no TTY is available.", err=True)
        click.echo(usage, err=True)
        raise click.Abort()


def abort_if_missing_without_tty(
    missing_required, interactive, can_prompt, message, usage
):
    if missing_required and interactive is None and not can_prompt:
        click.echo(message, err=True)
        click.echo(usage, err=True)
        raise click.Abort()


def resolve_value(*candidates: Any) -> Any:
    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, str) and not candidate.strip():
            continue
        return candidate
    return None


def _get_console():
    try:
        from rich.console import Console
    except ImportError:
        return None
    return Console(stderr=True)


def _render_heading(title: str, subtitle: str | None = None) -> None:
    console = _get_console()
    if not console:
        if subtitle:
            click.echo(f"\n{title}\n{subtitle}", err=True)
        else:
            click.echo(f"\n{title}", err=True)
        return

    try:
        from rich.panel import Panel
    except ImportError:
        if subtitle:
            click.echo(f"\n{title}\n{subtitle}", err=True)
        else:
            click.echo(f"\n{title}", err=True)
        return

    console.print(
        Panel.fit(
            subtitle or "",
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def _render_note(message: str) -> None:
    console = _get_console()
    if not console:
        click.echo(message, err=True)
        return
    console.print(f"[dim]{message}[/dim]")


def ask_text(message: str, default: str = "") -> str:
    _render_heading("Input", message)
    if default:
        _render_note(f"Press Enter to keep default: {default}")
    return click.prompt("Value", default=default, show_default=bool(default), err=True)


def ask_confirm(message: str, default: bool = True) -> bool:
    _render_heading("Confirm", message)
    return click.confirm("Continue", default=default, err=True)
