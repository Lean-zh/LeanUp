from pathlib import Path

from click.testing import CliRunner

from leanup.cli import cli
from leanup.repo.project_setup import LeanProjectSetup, SetupConfig


def test_setup_command_rejects_symlink_without_mathlib():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "setup",
            "Demo",
            "--lean-version",
            "v4.27.0",
            "--no-mathlib",
            "--dependency-mode",
            "symlink",
        ],
    )

    assert result.exit_code != 0
    assert "only available when mathlib is enabled" in result.output


def test_setup_command_uses_expected_defaults(monkeypatch, tmp_path):
    runner = CliRunner()
    captured = {}

    def fake_setup(self, config):
        captured["target_dir"] = config.target_dir
        captured["lean_version"] = config.lean_version
        captured["mathlib"] = config.mathlib
        captured["dependency_mode"] = config.resolved_dependency_mode
        return type(
            "Result",
            (),
            {
                "target_dir": config.target_dir,
                "lean_version": config.lean_version,
                "mathlib": config.mathlib,
                "dependency_mode": config.resolved_dependency_mode,
                "cache_dir": config.mathlib_cache_dir,
                "used_cache": True,
            },
        )()

    monkeypatch.setattr(LeanProjectSetup, "setup", fake_setup)

    target = tmp_path / "Demo"
    result = runner.invoke(cli, ["setup", str(target), "--lean-version", "4.27.0"])

    assert result.exit_code == 0
    assert captured["target_dir"] == target.resolve()
    assert captured["lean_version"] == "v4.27.0"
    assert captured["mathlib"] is True
    assert captured["dependency_mode"] == "build"


def test_setup_interactive_uses_previewed_dependency_mode(monkeypatch, tmp_path):
    import importlib

    setup_cli_module = importlib.import_module("leanup.cli.setup")
    runner = CliRunner()
    captured = {}

    def fake_setup(self, config):
        captured["dependency_mode"] = config.resolved_dependency_mode
        return type(
            "Result",
            (),
            {
                "target_dir": config.target_dir,
                "lean_version": config.lean_version,
                "mathlib": config.mathlib,
                "dependency_mode": config.resolved_dependency_mode,
                "cache_dir": config.mathlib_cache_dir,
                "used_cache": False,
            },
        )()

    monkeypatch.setattr(
        setup_cli_module,
        "resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, True, True),
    )
    values = iter([
        str(tmp_path / "Demo"),
        "v4.27.0",
        "Demo",
        "build",
    ])
    confirmations = iter([True, False])
    monkeypatch.setattr(setup_cli_module, "ask_text", lambda message, default="": next(values))
    monkeypatch.setattr(setup_cli_module, "ask_confirm", lambda message, default=True: next(confirmations))
    monkeypatch.setattr(LeanProjectSetup, "setup", fake_setup)

    result = runner.invoke(cli, ["setup"])

    assert result.exit_code == 0
    assert captured["dependency_mode"] == "build"


def test_setup_config_prefers_symlink_when_cache_exists(tmp_path):
    from leanup.repo import project_setup as project_setup_module

    original_cache_dir = project_setup_module.LEANUP_CACHE_DIR
    project_setup_module.LEANUP_CACHE_DIR = tmp_path / "cache"

    try:
        config = SetupConfig(target_dir=tmp_path / "Demo", lean_version="v4.27.0")
        assert config.resolved_dependency_mode == "build"

        config.mathlib_cache_dir.mkdir(parents=True, exist_ok=True)
        assert config.resolved_dependency_mode == "symlink"
    finally:
        project_setup_module.LEANUP_CACHE_DIR = original_cache_dir


def test_setup_build_mode_populates_shared_cache(tmp_path):
    class FakeElanManager:
        def is_elan_installed(self):
            return True

        def install_elan(self):
            return True

        def install_lean(self, version):
            return True

    def fake_lake_init(self, name, template=None):
        project_dir = self.cwd / name
        project_dir.mkdir(parents=True)
        (project_dir / "lakefile.lean").write_text(f"template={template}\n", encoding="utf-8")
        return "", "", 0

    def fake_lake_update(self):
        packages_dir = self.cwd / ".lake" / "packages" / "mathlib"
        packages_dir.mkdir(parents=True, exist_ok=True)
        (packages_dir / "README.md").write_text("cached mathlib\n", encoding="utf-8")
        (self.cwd / "lake-manifest.json").write_text("{}\n", encoding="utf-8")
        return "", "", 0

    def fake_lake_build(self):
        build_dir = self.cwd / ".lake" / "build"
        build_dir.mkdir(parents=True, exist_ok=True)
        return "", "", 0

    from leanup.repo import project_setup as project_setup_module

    original_cache_dir = project_setup_module.LEANUP_CACHE_DIR
    project_setup_module.LEANUP_CACHE_DIR = tmp_path / "cache"

    try:
        from leanup.repo.manager import LeanRepo

        original_lake_init = LeanRepo.lake_init
        original_lake_update = LeanRepo.lake_update
        original_lake_build = LeanRepo.lake_build
        LeanRepo.lake_init = fake_lake_init
        LeanRepo.lake_update = fake_lake_update
        LeanRepo.lake_build = fake_lake_build

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        target = tmp_path / "BuildDemo"
        config = SetupConfig(
            target_dir=target,
            lean_version="v4.27.0",
            dependency_mode="build",
        )

        result = manager.setup(config)

        assert result.used_cache is False
        assert (target / "lean-toolchain").read_text(encoding="utf-8").strip() == "leanprover/lean4:v4.27.0"
        assert config.mathlib_cache_dir.exists()
        assert (config.mathlib_cache_dir / "mathlib" / "README.md").exists()
    finally:
        project_setup_module.LEANUP_CACHE_DIR = original_cache_dir
        LeanRepo.lake_init = original_lake_init
        LeanRepo.lake_update = original_lake_update
        LeanRepo.lake_build = original_lake_build


def test_setup_symlink_mode_reuses_shared_cache(tmp_path):
    class FakeElanManager:
        def is_elan_installed(self):
            return True

        def install_elan(self):
            return True

        def install_lean(self, version):
            return True

    def fake_lake_init(self, name, template=None):
        project_dir = self.cwd / name
        project_dir.mkdir(parents=True)
        (project_dir / "lakefile.lean").write_text(f"template={template}\n", encoding="utf-8")
        return "", "", 0

    def fake_lake_update(self):
        packages_dir = self.cwd / ".lake" / "packages"
        packages_dir.mkdir(parents=True, exist_ok=True)
        (self.cwd / "lake-manifest.json").write_text("{}\n", encoding="utf-8")
        return "", "", 0

    def fake_lake_build(self):
        return "", "", 0

    from leanup.repo import project_setup as project_setup_module

    original_cache_dir = project_setup_module.LEANUP_CACHE_DIR
    project_setup_module.LEANUP_CACHE_DIR = tmp_path / "cache"

    try:
        from leanup.repo.manager import LeanRepo

        original_lake_init = LeanRepo.lake_init
        original_lake_update = LeanRepo.lake_update
        original_lake_build = LeanRepo.lake_build
        LeanRepo.lake_init = fake_lake_init
        LeanRepo.lake_update = fake_lake_update
        LeanRepo.lake_build = fake_lake_build

        cached_packages = project_setup_module.LEANUP_CACHE_DIR / "setup" / "mathlib" / "v4.27.0" / "packages" / "mathlib"
        cached_packages.mkdir(parents=True, exist_ok=True)
        (cached_packages / "README.md").write_text("cached\n", encoding="utf-8")

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        target = tmp_path / "SymlinkDemo"
        config = SetupConfig(target_dir=target, lean_version="v4.27.0", dependency_mode="symlink")

        result = manager.setup(config)

        packages_link = target / ".lake" / "packages"
        assert result.used_cache is True
        assert packages_link.is_symlink()
        assert packages_link.resolve() == config.mathlib_cache_dir
        assert (packages_link / "mathlib" / "README.md").read_text(encoding="utf-8").strip() == "cached"
    finally:
        project_setup_module.LEANUP_CACHE_DIR = original_cache_dir
        LeanRepo.lake_init = original_lake_init
        LeanRepo.lake_update = original_lake_update
        LeanRepo.lake_build = original_lake_build
