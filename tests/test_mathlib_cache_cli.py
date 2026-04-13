from pathlib import Path
import tarfile

from click.testing import CliRunner

from leanup.cli import cli
from leanup.repo.mathlib_cache import MathlibCacheManager


def test_mathlib_cache_pack_archives_current_repo(tmp_path):
    runner = CliRunner()
    repo_dir = tmp_path / "Demo"
    packages_dir = repo_dir / ".lake" / "packages" / "mathlib"
    packages_dir.mkdir(parents=True, exist_ok=True)
    (packages_dir / "README.md").write_text("cached\n", encoding="utf-8")
    output_dir = tmp_path / "cache"

    result = runner.invoke(
        cli,
        [
            "cache",
            "mathlib",
            "pack",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
            "--lean-version",
            "v4.22.0",
        ],
    )

    archive = output_dir / "v4.22.0" / "packages.tar.gz"
    assert result.exit_code == 0
    assert archive.exists()
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert "packages/mathlib/README.md" in names


def test_mathlib_cache_pack_follows_root_packages_symlink(tmp_path):
    runner = CliRunner()
    source_dir = tmp_path / "shared-packages" / "mathlib"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "README.md").write_text("cached\n", encoding="utf-8")

    repo_dir = tmp_path / "Demo"
    lake_dir = repo_dir / ".lake"
    lake_dir.mkdir(parents=True, exist_ok=True)
    (lake_dir / "packages").symlink_to(source_dir.parent, target_is_directory=True)

    output_dir = tmp_path / "cache"
    result = runner.invoke(
        cli,
        [
            "cache",
            "mathlib",
            "pack",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
            "--lean-version",
            "v4.29.0",
        ],
    )

    archive = output_dir / "v4.29.0" / "packages.tar.gz"
    assert result.exit_code == 0
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert "packages/mathlib/README.md" in names


def test_mathlib_cache_pack_passes_pigz_option(monkeypatch, tmp_path):
    runner = CliRunner()
    repo_dir = tmp_path / "Demo"
    packages_dir = repo_dir / ".lake" / "packages" / "mathlib"
    packages_dir.mkdir(parents=True, exist_ok=True)
    (packages_dir / "README.md").write_text("cached\n", encoding="utf-8")
    output_dir = tmp_path / "cache"

    captured = {}

    def fake_pack(self, packages_dir, output_file, use_pigz=False):
        captured["packages_dir"] = packages_dir
        captured["output_file"] = output_file
        captured["use_pigz"] = use_pigz
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(b"ok")
        return output_file

    monkeypatch.setattr(MathlibCacheManager, "pack_packages_archive", fake_pack)

    result = runner.invoke(
        cli,
        [
            "cache",
            "mathlib",
            "pack",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
            "--lean-version",
            "v4.22.0",
            "--pigz",
        ],
    )

    assert result.exit_code == 0
    assert captured["packages_dir"] == repo_dir / ".lake" / "packages"
    assert captured["output_file"] == output_dir / "v4.22.0" / "packages.tar.gz"
    assert captured["use_pigz"] is True


def test_mathlib_cache_pack_uses_pigz_by_default(monkeypatch, tmp_path):
    runner = CliRunner()
    repo_dir = tmp_path / "Demo"
    packages_dir = repo_dir / ".lake" / "packages" / "mathlib"
    packages_dir.mkdir(parents=True, exist_ok=True)
    (packages_dir / "README.md").write_text("cached\n", encoding="utf-8")
    output_dir = tmp_path / "cache"

    captured = {}

    def fake_pack(self, packages_dir, output_file, use_pigz=False):
        captured["use_pigz"] = use_pigz
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(b"ok")
        return output_file

    monkeypatch.setattr(MathlibCacheManager, "pack_packages_archive", fake_pack)

    result = runner.invoke(
        cli,
        [
            "cache",
            "mathlib",
            "pack",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
            "--lean-version",
            "v4.22.0",
        ],
    )

    assert result.exit_code == 0
    assert captured["use_pigz"] is True
