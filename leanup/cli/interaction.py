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


def ask_text(message: str, default: str = "") -> str:
    return click.prompt(message, default=default, show_default=bool(default), err=True)


def ask_confirm(message: str, default: bool = True) -> bool:
    return click.confirm(message, default=default, err=True)
