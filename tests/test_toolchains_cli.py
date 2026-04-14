from pathlib import Path
import tarfile

from click.testing import CliRunner

from leanup.cli import cli


def _create_base_elan(elan_home: Path) -> None:
    (elan_home / "bin").mkdir(parents=True, exist_ok=True)
    (elan_home / "settings.toml").write_text("default_toolchain = 'stable'\n", encoding="utf-8")
    (elan_home / "bin" / "elan").write_text("binary\n", encoding="utf-8")


def _create_toolchain(elan_home: Path, version: str) -> Path:
    toolchain_dir = elan_home / "toolchains" / f"leanprover--lean4---{version}"
    toolchain_dir.mkdir(parents=True, exist_ok=True)
    (toolchain_dir / "VERSION").write_text(version, encoding="utf-8")
    return toolchain_dir


def test_toolchains_list_local(tmp_path):
    runner = CliRunner()
    cache_dir = tmp_path / "toolchains"
    (cache_dir / "archives").mkdir(parents=True, exist_ok=True)
    (cache_dir / "archives" / "base-elan.tar.gz").write_bytes(b"ok")
    (cache_dir / "archives" / "v4.28.0").mkdir(parents=True, exist_ok=True)
    (cache_dir / "archives" / "v4.28.0" / "toolchain.tar.gz").write_bytes(b"ok")

    result = runner.invoke(cli, ["toolchains", "list", "--cache-dir", str(cache_dir)])

    assert result.exit_code == 0
    assert "base" in result.output
    assert "v4.28.0" in result.output


def test_toolchains_pack_without_version_packs_base_elan(tmp_path):
    runner = CliRunner()
    cache_dir = tmp_path / "toolchains"
    elan_home = tmp_path / "leanup-elan"
    _create_base_elan(elan_home)

    result = runner.invoke(
        cli,
        ["toolchains", "pack", "--cache-dir", str(cache_dir), "--elan-home", str(elan_home)],
    )

    archive = cache_dir / "archives" / "base-elan.tar.gz"
    assert result.exit_code == 0
    assert archive.exists()
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
    assert ".elan/settings.toml" in names
    assert ".elan/bin/elan" in names


def test_toolchains_pack_and_unpack_version_archive(tmp_path):
    runner = CliRunner()
    cache_dir = tmp_path / "toolchains"
    elan_home = tmp_path / "leanup-elan"
    _create_base_elan(elan_home)
    _create_toolchain(elan_home, "v4.28.0")

    pack_result = runner.invoke(
        cli,
        [
            "toolchains",
            "pack",
            "v4.28.0",
            "--cache-dir",
            str(cache_dir),
            "--elan-home",
            str(elan_home),
        ],
    )
    assert pack_result.exit_code == 0

    extracted_home = tmp_path / "restored-elan"
    unpack_result = runner.invoke(
        cli,
        [
            "toolchains",
            "unpack",
            "v4.28.0",
            "--cache-dir",
            str(cache_dir),
            "--elan-home",
            str(extracted_home),
        ],
    )
    assert unpack_result.exit_code == 0
    assert (extracted_home / "toolchains" / "leanprover--lean4---v4.28.0" / "VERSION").read_text(encoding="utf-8") == "v4.28.0"


def test_toolchains_init_with_url_downloads_base_archive(tmp_path, monkeypatch):
    runner = CliRunner()
    cache_dir = tmp_path / "toolchains"
    elan_home = tmp_path / "restored-elan"

    archive_source = tmp_path / "source-elan"
    _create_base_elan(archive_source)
    manager_runner = CliRunner()
    manager_runner.invoke(
        cli,
        ["toolchains", "pack", "--cache-dir", str(cache_dir), "--elan-home", str(archive_source)],
    )

    def fake_download(self, url: str):
        return self.get_base_archive_path()

    from leanup.repo.toolchain_cache import ToolchainCacheManager

    monkeypatch.setattr(ToolchainCacheManager, "download_base_archive", fake_download)

    result = runner.invoke(
        cli,
        [
            "toolchains",
            "init",
            "--url",
            "http://127.0.0.1:8000",
            "--cache-dir",
            str(cache_dir),
            "--elan-home",
            str(elan_home),
        ],
    )

    assert result.exit_code == 0
    assert (elan_home / "settings.toml").exists()
