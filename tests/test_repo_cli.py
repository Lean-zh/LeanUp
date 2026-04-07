from pathlib import Path
import importlib

repo_cli_module = importlib.import_module("leanup.cli.repo")

from click.testing import CliRunner

from leanup.cli import cli


def test_repo_install_no_interactive_missing_suffix_fails(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(
        repo_cli_module,
        "resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (False, True, False, False, False),
    )

    result = runner.invoke(cli, ["repo", "install", "-I"])

    assert result.exit_code != 0
    assert "Missing required repository suffix" in result.output


def test_repo_install_interactive_prompts_and_installs(monkeypatch, tmp_path):
    runner = CliRunner()
    values = iter(
        [
            "leanprover-community/mathlib4",
            "https://github.com",
            "v4.14.0",
            str(tmp_path),
            "mathlib4_v4140",
            "REPL,REPL.Main",
        ]
    )
    confirmations = iter([True, False, False])
    captured = {}

    monkeypatch.setattr(
        repo_cli_module,
        "resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, True, True),
    )
    monkeypatch.setattr(
        repo_cli_module,
        "ask_text",
        lambda message, default="": next(values),
    )
    monkeypatch.setattr(
        repo_cli_module,
        "ask_confirm",
        lambda message, default=True: next(confirmations),
    )

    def fake_install(self):
        captured.update(
            {
                "suffix": self.suffix,
                "source": self.source,
                "branch": self.branch,
                "dest_dir": self.dest_dir,
                "dest_name": self.dest_name,
                "lake_update": self.lake_update,
                "lake_build": self.lake_build,
                "build_packages": self.build_packages,
            }
        )

    monkeypatch.setattr("leanup.repo.manager.InstallConfig.install", fake_install)

    result = runner.invoke(cli, ["repo", "install"])

    assert result.exit_code == 0
    assert captured["suffix"] == "leanprover-community/mathlib4"
    assert captured["source"] == "https://github.com"
    assert captured["branch"] == "v4.14.0"
    assert captured["dest_dir"] == Path(tmp_path)
    assert captured["dest_name"] == "mathlib4_v4140"
    assert captured["lake_update"] is True
    assert captured["lake_build"] is False
    assert captured["build_packages"] == ["REPL", "REPL.Main"]
