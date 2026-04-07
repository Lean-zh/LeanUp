from pathlib import Path
import tarfile

from click.testing import CliRunner

from leanup.cli import cli


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
            "mathlib",
            "cache",
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
