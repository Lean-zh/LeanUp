from pathlib import Path
import tarfile

from click.testing import CliRunner

from leanup.cli import cli
from leanup.repo.mathlib_cache import MathlibCacheManager


def _write_reference_archive(root: Path, version: str) -> Path:
    archive_dir = root / version
    archive_dir.mkdir(parents=True, exist_ok=True)
    staging = root / ".staging" / version / "packages" / "mathlib"
    staging.mkdir(parents=True, exist_ok=True)
    (staging / "README.md").write_text(f"cache for {version}\n", encoding="utf-8")
    archive_path = archive_dir / "packages.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(staging.parent, arcname="packages")
    return archive_path


def test_mathlib_cache_import_command(monkeypatch, tmp_path):
    import importlib

    mathlib_cli_module = importlib.import_module("leanup.cli.mathlib")
    cache_module = importlib.import_module("leanup.repo.mathlib_cache")

    runner = CliRunner()
    source_dir = tmp_path / "reference-cache"
    _write_reference_archive(source_dir, "v4.22.0")

    original_cache_root = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "leanup-cache"

    try:
        result = runner.invoke(
            cli,
            ["mathlib", "cache", "import", "v4.22.0", "--source-dir", str(source_dir)],
        )

        assert result.exit_code == 0
        local_packages = cache_module.LEANUP_CACHE_DIR / "setup" / "mathlib" / "v4.22.0" / "packages"
        assert local_packages.exists()
        assert (local_packages / "mathlib" / "README.md").read_text(encoding="utf-8").strip() == "cache for v4.22.0"
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_root


def test_mathlib_cache_list_command(monkeypatch, tmp_path):
    import importlib

    cache_module = importlib.import_module("leanup.repo.mathlib_cache")
    runner = CliRunner()
    source_dir = tmp_path / "reference-cache"
    _write_reference_archive(source_dir, "v4.22.0")

    original_cache_root = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "leanup-cache"

    try:
        local_packages = cache_module.LEANUP_CACHE_DIR / "setup" / "mathlib" / "v4.21.0" / "packages"
        (local_packages / "mathlib").mkdir(parents=True, exist_ok=True)

        result = runner.invoke(
            cli,
            ["mathlib", "cache", "list", "--source-dir", str(source_dir)],
        )

        assert result.exit_code == 0
        assert "v4.21.0" in result.output
        assert "v4.22.0" in result.output
        assert "local" in result.output
        assert "importable" in result.output
    finally:
        cache_module.LEANUP_CACHE_DIR = original_cache_root


def test_setup_symlink_imports_reference_cache_when_available(tmp_path):
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

    from leanup.repo import mathlib_cache as cache_module
    from leanup.repo.manager import LeanRepo
    from leanup.repo.project_setup import LeanProjectSetup, SetupConfig

    source_dir = tmp_path / "reference-cache"
    _write_reference_archive(source_dir, "v4.22.0")

    original_cache_root = cache_module.LEANUP_CACHE_DIR
    cache_module.LEANUP_CACHE_DIR = tmp_path / "leanup-cache"
    original_source = cache_module.os.getenv("LEANUP_MATHLIB_CACHE_SOURCE")
    original_lake_init = LeanRepo.lake_init
    original_lake_update = LeanRepo.lake_update
    original_lake_build = LeanRepo.lake_build

    try:
        cache_module.os.environ["LEANUP_MATHLIB_CACHE_SOURCE"] = str(source_dir)
        LeanRepo.lake_init = fake_lake_init
        LeanRepo.lake_update = fake_lake_update
        LeanRepo.lake_build = fake_lake_build

        manager = LeanProjectSetup(elan_manager=FakeElanManager())
        manager.cache_manager = MathlibCacheManager()

        target = tmp_path / "ImportedDemo"
        config = SetupConfig(target_dir=target, lean_version="v4.22.0", dependency_mode="symlink")

        result = manager.setup(config)

        packages_link = target / ".lake" / "packages"
        assert result.used_cache is True
        assert packages_link.is_symlink()
        assert packages_link.resolve() == config.mathlib_cache_dir
        assert (packages_link / "mathlib" / "README.md").read_text(encoding="utf-8").strip() == "cache for v4.22.0"
    finally:
        if original_source is None:
            cache_module.os.environ.pop("LEANUP_MATHLIB_CACHE_SOURCE", None)
        else:
            cache_module.os.environ["LEANUP_MATHLIB_CACHE_SOURCE"] = original_source
        cache_module.LEANUP_CACHE_DIR = original_cache_root
        LeanRepo.lake_init = original_lake_init
        LeanRepo.lake_update = original_lake_update
        LeanRepo.lake_build = original_lake_build
