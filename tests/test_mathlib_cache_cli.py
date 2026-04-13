import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

from click.testing import CliRunner
from leanup.cli import cli
from leanup.repo.cache_server import create_cache_app, list_package_versions, resolve_ltar_path
from leanup.repo.mathlib_cache import MathlibCacheManager
from leanup.repo.project_setup import LeanProjectSetup


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
            "pack",
            "v4.22.0",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
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
            "pack",
            "v4.29.0",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
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
            "pack",
            "v4.22.0",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
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
            "pack",
            "v4.22.0",
            "--repo-dir",
            str(repo_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert captured["use_pigz"] is True


def test_mathlib_cache_list_prints_package_urls(monkeypatch, tmp_path):
    runner = CliRunner()
    cache_root = tmp_path / "cache"
    (cache_root / "v4.22.0" / "packages").mkdir(parents=True)
    (cache_root / "v4.27.0" / "packages").mkdir(parents=True)

    original_init = MathlibCacheManager.__init__

    def fake_cache_init(self, cache_root_arg=None):
        original_init(self, cache_root=cache_root)

    monkeypatch.setattr(MathlibCacheManager, "__init__", fake_cache_init)

    result = runner.invoke(
        cli,
        [
            "cache",
            "mathlib",
            "list",
            "--base-url",
            "http://127.0.0.1:8000/",
        ],
    )

    assert result.exit_code == 0
    assert "v4.22.0 http://127.0.0.1:8000/packages/mathlib/v4.22.0/packages.tar.gz" in result.output
    assert "v4.27.0 http://127.0.0.1:8000/packages/mathlib/v4.27.0/packages.tar.gz" in result.output


def test_mathlib_cache_list_reads_remote_index(tmp_path):
    runner = CliRunner()
    packages_root = tmp_path / "packages-cache"
    (packages_root / "v4.22.0").mkdir(parents=True, exist_ok=True)
    (packages_root / "v4.22.0" / "packages.tar.gz").write_bytes(b"ok")
    (packages_root / "v4.27.0").mkdir(parents=True, exist_ok=True)
    (packages_root / "v4.27.0" / "packages.tar.gz").write_bytes(b"ok")

    ltar_root = tmp_path / "isolated-mathlib4-cache"
    ltar_root.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-c",
        "from leanup.cli import cli; cli()",
        "cache",
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        "18081",
        "--ltar-root",
        str(ltar_root),
        "--packages-root",
        str(packages_root),
    ]
    proc = subprocess.Popen(
        command,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        if proc.stdout:
            proc.stdout.readline()
            proc.stdout.readline()
            proc.stdout.readline()
        time.sleep(1)
        base_url = "http://127.0.0.1:18081"
        result = runner.invoke(
            cli,
            ["cache", "mathlib", "list", "--base-url", base_url],
        )
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    assert result.exit_code == 0
    assert f"v4.22.0 {base_url}/packages/mathlib/v4.22.0/packages.tar.gz" in result.output
    assert f"v4.27.0 {base_url}/packages/mathlib/v4.27.0/packages.tar.gz" in result.output


def test_cache_get_downloads_and_extracts_packages_archive(tmp_path):
    runner = CliRunner()
    packages_root = tmp_path / "packages-cache"
    archive_dir = packages_root / "v4.22.0"
    archive_dir.mkdir(parents=True, exist_ok=True)

    source_packages = tmp_path / "source-packages" / "mathlib"
    source_packages.mkdir(parents=True, exist_ok=True)
    (source_packages / "README.md").write_text("cached\n", encoding="utf-8")

    archive = archive_dir / "packages.tar.gz"
    MathlibCacheManager().pack_packages_archive(source_packages.parent, archive)

    target_dir = tmp_path / "Demo"
    target_dir.mkdir(parents=True, exist_ok=True)
    stale_packages = target_dir / ".lake" / "packages"
    stale_packages.mkdir(parents=True, exist_ok=True)
    (stale_packages / "STALE.txt").write_text("stale\n", encoding="utf-8")

    ltar_root = tmp_path / "isolated-mathlib4-cache"
    ltar_root.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-c",
        "from leanup.cli import cli; cli()",
        "cache",
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        "18082",
        "--ltar-root",
        str(ltar_root),
        "--packages-root",
        str(packages_root),
    ]
    proc = subprocess.Popen(
        command,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        if proc.stdout:
            proc.stdout.readline()
            proc.stdout.readline()
            proc.stdout.readline()
        time.sleep(1)
        result = runner.invoke(
            cli,
            [
                "cache",
                "get",
                "v4.22.0",
                "--base-url",
                "http://127.0.0.1:18082",
                "--target-dir",
                str(target_dir),
                "--cache-dir",
                str(tmp_path / "local-cache"),
            ],
        )
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    installed_readme = target_dir / ".lake" / "packages" / "mathlib" / "README.md"
    assert result.exit_code == 0
    assert installed_readme.read_text(encoding="utf-8") == "cached\n"
    assert not (target_dir / ".lake" / "packages" / "STALE.txt").exists()


def test_cache_server_resolves_ltar_and_packages_routes(tmp_path):
    packages_root = tmp_path / "packages-root"
    ltar_root = tmp_path / "isolated-mathlib4-cache"
    (packages_root / "v4.22.0").mkdir(parents=True, exist_ok=True)
    (ltar_root / "repos" / "owner" / "repo").mkdir(parents=True, exist_ok=True)

    assert resolve_ltar_path(ltar_root.resolve(), "abc.ltar") == ltar_root.resolve() / "abc.ltar"
    assert resolve_ltar_path(ltar_root.resolve(), "owner/repo/abc.ltar") == ltar_root.resolve() / "repos" / "owner" / "repo" / "abc.ltar"
    assert list_package_versions(packages_root.resolve()) == []


def test_cache_pack_honors_cleanup_cache_dir_env_in_subprocess(tmp_path):
    repo_dir = tmp_path / "Demo"
    packages_dir = repo_dir / ".lake" / "packages" / "mathlib"
    packages_dir.mkdir(parents=True, exist_ok=True)
    (packages_dir / "README.md").write_text("cached\n", encoding="utf-8")

    custom_cache_dir = tmp_path / "custom-cache-root"
    env = os.environ.copy()
    env["LEANUP_CACHE_DIR"] = str(custom_cache_dir)

    command = [
        sys.executable,
        "-c",
        "from leanup.cli import cli; cli()",
        "cache",
        "pack",
        "v4.22.0",
        "--repo-dir",
        str(repo_dir),
        "--no-pigz",
    ]
    result = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    expected_archive = custom_cache_dir / "setup" / "mathlib" / "v4.22.0" / "packages.tar.gz"
    assert result.returncode == 0, result.stderr
    assert expected_archive.exists()
    assert str(expected_archive) in result.stdout


def test_cache_serve_honors_explicit_roots_in_subprocess(tmp_path):
    ltar_root = tmp_path / "isolated-mathlib4-cache"
    packages_root = tmp_path / "isolated-leanup-cache"
    ltar_root.mkdir(parents=True, exist_ok=True)
    packages_root.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-c",
        "from leanup.cli import cli; cli()",
        "cache",
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        "18080",
        "--ltar-root",
        str(ltar_root),
        "--packages-root",
        str(packages_root),
    ]
    proc = subprocess.Popen(
        command,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout_line_1 = proc.stdout.readline().strip() if proc.stdout else ""
        stdout_line_2 = proc.stdout.readline().strip() if proc.stdout else ""
        stdout_line_3 = proc.stdout.readline().strip() if proc.stdout else ""
        time.sleep(1)
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    assert "Serving cache on http://127.0.0.1:18080" in stdout_line_1
    assert str(ltar_root) in stdout_line_2
    assert str(packages_root) in stdout_line_3


def test_cache_create_refreshes_shared_cache_and_archive(monkeypatch, tmp_path):
    runner = CliRunner()
    custom_cache_root = tmp_path / "leanup-cache"

    def fake_ensure_toolchain(self, version):
        return None

    def fake_run_lake_update(self, repo):
        packages_dir = repo.cwd / ".lake" / "packages" / "mathlib"
        packages_dir.mkdir(parents=True, exist_ok=True)
        (packages_dir / "README.md").write_text("cached\n", encoding="utf-8")

    def fake_run_lake_cache_get(self, repo):
        return None

    monkeypatch.setattr(LeanProjectSetup, "_ensure_toolchain", fake_ensure_toolchain)
    monkeypatch.setattr(LeanProjectSetup, "_run_lake_update", fake_run_lake_update)
    monkeypatch.setattr(LeanProjectSetup, "_run_lake_cache_get", fake_run_lake_cache_get)

    original_init = MathlibCacheManager.__init__

    def fake_cache_init(self, cache_root=None):
        original_init(self, cache_root=custom_cache_root)

    monkeypatch.setattr(MathlibCacheManager, "__init__", fake_cache_init)

    result = runner.invoke(cli, ["cache", "create", "v4.22.0", "--no-pigz"])

    expected_packages = custom_cache_root / "v4.22.0" / "packages"
    expected_archive = custom_cache_root / "v4.22.0" / "packages.tar.gz"
    assert result.exit_code == 0
    assert expected_packages.exists()
    assert expected_archive.exists()
    assert str(expected_packages) in result.output
    assert str(expected_archive) in result.output
