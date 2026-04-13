import os
from pathlib import Path

from click.testing import CliRunner
from git import Repo

from leanup.cli import cli
from leanup.repo.project_setup import LeanProjectSetup, SetupConfig


def _init_fake_package_repo(package_dir: Path, package_name: str = "mathlib") -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "README.md").write_text("cached\n", encoding="utf-8")
    (package_dir / "lakefile.lean").write_text(f"package {package_name} where\n", encoding="utf-8")
    repo = Repo.init(package_dir)
    with repo.config_writer() as config:
        config.set_value("user", "name", "LeanUp Test")
        config.set_value("user", "email", "leanup@example.com")
    if "origin" not in [remote.name for remote in repo.remotes]:
        repo.create_remote("origin", f"https://github.com/leanprover-community/{package_name}.git")
    repo.index.add(["README.md", "lakefile.lean"])
    repo.index.commit("init")


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
    assert captured["dependency_mode"] == "symlink"


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
        "symlink",
    ])
    confirmations = iter([True, False])
    monkeypatch.setattr(setup_cli_module, "ask_text", lambda message, default="": next(values))
    monkeypatch.setattr(setup_cli_module, "ask_confirm", lambda message, default=True: next(confirmations))
    monkeypatch.setattr(LeanProjectSetup, "setup", fake_setup)

    result = runner.invoke(cli, ["setup"])

    assert result.exit_code == 0
    assert captured["dependency_mode"] == "symlink"


def test_setup_interactive_rejects_blank_project_directory(monkeypatch):
    import importlib

    setup_cli_module = importlib.import_module("leanup.cli.setup")
    runner = CliRunner()

    monkeypatch.setattr(
        setup_cli_module,
        "resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, True, True),
    )
    monkeypatch.setattr(setup_cli_module, "ask_text", lambda message, default="": "   ")

    result = runner.invoke(cli, ["setup"])

    assert result.exit_code != 0
    assert "Project directory is required." in result.output


def test_setup_interactive_rejects_blank_lean_version(monkeypatch, tmp_path):
    import importlib

    setup_cli_module = importlib.import_module("leanup.cli.setup")
    runner = CliRunner()
    values = iter([str(tmp_path / "Demo"), "   "])

    monkeypatch.setattr(
        setup_cli_module,
        "resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, True, True),
    )
    monkeypatch.setattr(setup_cli_module, "ask_text", lambda message, default="": next(values))

    result = runner.invoke(cli, ["setup"])

    assert result.exit_code != 0
    assert "Lean version is required." in result.output


def test_setup_config_prefers_symlink_when_cache_exists(tmp_path):
    from leanup.repo.mathlib_cache import MathlibCacheManager
    from leanup.repo import mathlib_cache as cache_module

    original_cache_dir = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "cache"

    try:
        config = SetupConfig(target_dir=tmp_path / "Demo", lean_version="v4.27.0")
        assert config.resolved_dependency_mode == "symlink"

        MathlibCacheManager().get_local_packages_dir("v4.27.0").mkdir(parents=True, exist_ok=True)
        assert config.resolved_dependency_mode == "symlink"
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_dir


def test_setup_copy_mode_populates_shared_cache(tmp_path):
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

    def fake_lake_env_lean(self, filepath, json=True, options=None, nproc=None):
        assert Path(filepath).suffix == ".lean"
        return "4.27.0\n", "", 0

    def fake_lake(self, args):
        if args == ["exe", "cache", "get"]:
            packages_dir = self.cwd / ".lake" / "packages" / "mathlib"
            _init_fake_package_repo(packages_dir)
            (packages_dir / "README.md").write_text("cached from cache get\n", encoding="utf-8")
            repo = Repo(packages_dir)
            repo.index.add(["README.md", "lakefile.lean"])
            repo.index.commit("update readme")
            return "", "", 0
        raise AssertionError(f"unexpected lake args: {args}")

    from leanup.repo import mathlib_cache as cache_module

    original_cache_dir = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "cache"

    try:
        from leanup.repo.manager import LeanRepo

        original_lake_init = LeanRepo.lake_init
        original_lake_update = LeanRepo.lake_update
        original_lake_build = LeanRepo.lake_build
        original_lake_env_lean = LeanRepo.lake_env_lean
        original_lake = LeanRepo.lake
        LeanRepo.lake_init = fake_lake_init
        LeanRepo.lake_update = fake_lake_update
        LeanRepo.lake_build = fake_lake_build
        LeanRepo.lake_env_lean = fake_lake_env_lean
        LeanRepo.lake = fake_lake

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        target = tmp_path / "BuildDemo"
        config = SetupConfig(
            target_dir=target,
            lean_version="v4.27.0",
            dependency_mode="copy",
        )

        result = manager.setup(config)

        assert result.used_cache is False
        assert (target / "lean-toolchain").read_text(encoding="utf-8").strip() == "leanprover/lean4:v4.27.0"
        assert (target / "lakefile.lean").read_text(encoding="utf-8").find('require mathlib from git') >= 0
        assert (target / "BuildDemo.lean").exists()
        assert (target / "BuildDemo" / "Basic.lean").exists()
        assert (target / ".lake" / "packages").exists()
        assert not (target / ".lake" / "packages").is_symlink()
        assert config.mathlib_cache_dir.exists()
        assert (config.mathlib_cache_dir / "mathlib" / "README.md").exists()
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_dir
        LeanRepo.lake_init = original_lake_init
        LeanRepo.lake_update = original_lake_update
        LeanRepo.lake_build = original_lake_build
        LeanRepo.lake_env_lean = original_lake_env_lean
        LeanRepo.lake = original_lake


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

    calls = {"lake_update": 0, "cache_get": 0}

    def fake_lake_update(self):
        calls["lake_update"] += 1
        packages_dir = self.cwd / ".lake" / "packages"
        packages_dir.mkdir(parents=True, exist_ok=True)
        (self.cwd / "lake-manifest.json").write_text("{}\n", encoding="utf-8")
        return "", "", 0

    def fake_lake_build(self):
        return "", "", 0

    def fake_lake_env_lean(self, filepath, json=True, options=None, nproc=None):
        assert Path(filepath).suffix == ".lean"
        return "4.27.0\n", "", 0

    def fake_lake(self, args):
        if args == ["exe", "cache", "get"]:
            calls["cache_get"] += 1
            packages_dir = self.cwd / ".lake" / "packages" / "mathlib"
            packages_dir.mkdir(parents=True, exist_ok=True)
            (packages_dir / "README.md").write_text("cached\n", encoding="utf-8")
            return "", "", 0
        raise AssertionError(f"unexpected lake args: {args}")

    from leanup.repo import mathlib_cache as cache_module

    original_cache_dir = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "cache"

    try:
        from leanup.repo.manager import LeanRepo

        original_lake_init = LeanRepo.lake_init
        original_lake_update = LeanRepo.lake_update
        original_lake_build = LeanRepo.lake_build
        original_lake_env_lean = LeanRepo.lake_env_lean
        original_lake = LeanRepo.lake
        LeanRepo.lake_init = fake_lake_init
        LeanRepo.lake_update = fake_lake_update
        LeanRepo.lake_build = fake_lake_build
        LeanRepo.lake_env_lean = fake_lake_env_lean
        LeanRepo.lake = fake_lake

        cached_packages = cache_module.LEANUP_CACHE_DIR / "mathlib" / "packages" / "v4.27.0" / "packages" / "mathlib"
        _init_fake_package_repo(cached_packages)

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        target = tmp_path / "SymlinkDemo"
        config = SetupConfig(target_dir=target, lean_version="v4.27.0", dependency_mode="symlink")

        result = manager.setup(config)

        packages_link = target / ".lake" / "packages"
        assert result.used_cache is True
        assert packages_link.is_symlink()
        assert packages_link.resolve() == config.mathlib_cache_dir
        assert (packages_link / "mathlib" / "README.md").read_text(encoding="utf-8").strip() == "cached"
        assert (target / "lake-manifest.json").exists()
        assert calls["lake_update"] == 0
        assert calls["cache_get"] == 0
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_dir
        LeanRepo.lake_init = original_lake_init
        LeanRepo.lake_update = original_lake_update
        LeanRepo.lake_build = original_lake_build
        LeanRepo.lake_env_lean = original_lake_env_lean
        LeanRepo.lake = original_lake


def test_setup_copy_mode_reuses_shared_cache(tmp_path):
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

    def fake_lake_build(self):
        return "", "", 0

    def fake_lake_env_lean(self, filepath, json=True, options=None, nproc=None):
        assert Path(filepath).suffix == ".lean"
        return "4.22.0\n", "", 0

    from leanup.repo import mathlib_cache as cache_module

    original_cache_dir = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "cache"

    try:
        from leanup.repo.manager import LeanRepo

        original_lake_init = LeanRepo.lake_init
        original_lake_build = LeanRepo.lake_build
        original_lake_env_lean = LeanRepo.lake_env_lean
        LeanRepo.lake_init = fake_lake_init
        LeanRepo.lake_build = fake_lake_build
        LeanRepo.lake_env_lean = fake_lake_env_lean

        cached_packages = cache_module.LEANUP_CACHE_DIR / "mathlib" / "packages" / "v4.22.0" / "packages" / "mathlib"
        _init_fake_package_repo(cached_packages)

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        target = tmp_path / "CopyDemo"
        config = SetupConfig(target_dir=target, lean_version="v4.22.0", dependency_mode="copy")

        result = manager.setup(config)

        packages_dir = target / ".lake" / "packages"
        assert result.used_cache is True
        assert packages_dir.exists()
        assert not packages_dir.is_symlink()
        assert (packages_dir / "mathlib" / "README.md").exists()
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_dir
        LeanRepo.lake_init = original_lake_init
        LeanRepo.lake_build = original_lake_build
        LeanRepo.lake_env_lean = original_lake_env_lean


def test_setup_symlink_mode_skips_lake_update_when_manifest_exists(tmp_path):
    class FakeElanManager:
        def is_elan_installed(self):
            return True

        def install_elan(self):
            return True

        def install_lean(self, version):
            return True

    calls = {"lake_update": 0, "lake_build": 0}

    def fake_lake_update(self):
        calls["lake_update"] += 1
        return "", "", 0

    def fake_lake_build(self):
        calls["lake_build"] += 1
        return "", "", 0

    def fake_lake_env_lean(self, filepath, json=True, options=None, nproc=None):
        assert Path(filepath).suffix == ".lean"
        return "4.22.0\n", "", 0

    from leanup.repo import mathlib_cache as cache_module
    from leanup.repo.manager import LeanRepo

    original_cache_dir = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "cache"
    original_lake_update = LeanRepo.lake_update
    original_lake_build = LeanRepo.lake_build
    original_lake_env_lean = LeanRepo.lake_env_lean

    try:
        cached_packages = cache_module.LEANUP_CACHE_DIR / "setup" / "mathlib" / "v4.22.0" / "packages" / "mathlib"
        _init_fake_package_repo(cached_packages)

        LeanRepo.lake_update = fake_lake_update
        LeanRepo.lake_build = fake_lake_build
        LeanRepo.lake_env_lean = fake_lake_env_lean

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        target = tmp_path / "FastDemo"
        config = SetupConfig(target_dir=target, lean_version="v4.22.0", dependency_mode="symlink")

        manager.setup(config)

        assert calls["lake_update"] == 0
        assert calls["lake_build"] == 1
        assert (target / "lake-manifest.json").exists()
        assert '"name": "FastDemo"' in (target / "lake-manifest.json").read_text(encoding="utf-8")
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_dir
        LeanRepo.lake_update = original_lake_update
        LeanRepo.lake_build = original_lake_build
        LeanRepo.lake_env_lean = original_lake_env_lean


def test_setup_uses_bundled_manifest_without_external_reference(tmp_path):
    class FakeElanManager:
        def is_elan_installed(self):
            return True

        def install_elan(self):
            return True

        def install_lean(self, version):
            return True

    calls = {"lake_update": 0, "lake_build": 0}

    def fake_lake_update(self):
        calls["lake_update"] += 1
        return "", "", 0

    def fake_lake_build(self):
        calls["lake_build"] += 1
        return "", "", 0

    def fake_lake_env_lean(self, filepath, json=True, options=None, nproc=None):
        assert Path(filepath).suffix == ".lean"
        return "4.22.0\n", "", 0

    def fake_lake(self, args):
        if args == ["exe", "cache", "get"]:
            packages_dir = self.cwd / ".lake" / "packages" / "mathlib"
            _init_fake_package_repo(packages_dir)
            (packages_dir / "README.md").write_text("cached from cache get\n", encoding="utf-8")
            repo = Repo(packages_dir)
            repo.index.add(["README.md", "lakefile.lean"])
            repo.index.commit("update readme")
            return "", "", 0
        raise AssertionError(f"unexpected lake args: {args}")

    from leanup.repo import mathlib_cache as cache_module
    from leanup.repo.manager import LeanRepo

    original_cache_dir = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "cache"
    original_lake_update = LeanRepo.lake_update
    original_lake_build = LeanRepo.lake_build
    original_lake_env_lean = LeanRepo.lake_env_lean
    original_lake = LeanRepo.lake

    try:
        LeanRepo.lake_update = fake_lake_update
        LeanRepo.lake_build = fake_lake_build
        LeanRepo.lake_env_lean = fake_lake_env_lean
        LeanRepo.lake = fake_lake

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        target = tmp_path / "BundledDemo"
        config = SetupConfig(target_dir=target, lean_version="v4.22.0", dependency_mode="symlink")

        manager.setup(config)

        assert calls["lake_update"] == 1
        assert calls["lake_build"] == 1
        assert (target / "lake-manifest.json").exists()
        manifest_text = (target / "lake-manifest.json").read_text(encoding="utf-8")
        assert '"inputRev": "v4.22.0"' in manifest_text
        assert '"name": "BundledDemo"' in manifest_text
        assert '"rev": "' in manifest_text
        assert (cache_module.LEANUP_CACHE_DIR / "setup" / "mathlib" / "v4.22.0" / "packages").exists()
        assert (
            cache_module.LEANUP_CACHE_DIR / "setup" / "mathlib" / "v4.22.0" / "packages" / "mathlib" / "README.md"
        ).read_text(encoding="utf-8").strip() == "cached from cache get"
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_dir
        LeanRepo.lake_update = original_lake_update
        LeanRepo.lake_build = original_lake_build
        LeanRepo.lake_env_lean = original_lake_env_lean
        LeanRepo.lake = original_lake
