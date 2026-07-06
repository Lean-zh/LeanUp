from pathlib import Path
import tarfile

from click.testing import CliRunner

from leanup.cli import cli


def _create_elan_home(root: Path) -> Path:
    elan_home = root / "elan"
    (elan_home / "bin").mkdir(parents=True)
    elan_bin = elan_home / "bin" / "elan"
    elan_bin.write_text("#!/bin/sh\necho elan 0.0.0\n", encoding="utf-8")
    elan_bin.chmod(0o755)
    (elan_home / "settings.toml").write_text("default_toolchain = 'leanprover/lean4:v4.30.0'\n", encoding="utf-8")
    return elan_home


def _create_toolchain(elan_home: Path, version: str = "v4.30.0") -> Path:
    toolchain = elan_home / "toolchains" / f"leanprover--lean4---{version}"
    (toolchain / "bin").mkdir(parents=True)
    lean_bin = toolchain / "bin" / "lean"
    lean_bin.write_text(f"#!/bin/sh\necho Lean {version}\n", encoding="utf-8")
    lean_bin.chmod(0o755)
    target = toolchain / "lib-target"
    target.write_text("target\n", encoding="utf-8")
    (toolchain / "lib-link").symlink_to("lib-target")
    return toolchain


def test_init_creates_leanup_home(tmp_path):
    runner = CliRunner()
    home = tmp_path / "home"

    result = runner.invoke(cli, ["init", "--home", str(home), "--server", "http://cache.local:8000"])

    assert result.exit_code == 0, result.output
    assert (home / ".env").exists()
    assert (home / "cache" / "serve" / "elan" / "base").is_dir()
    assert (home / "cache" / "local" / "mathlib").is_dir()
    assert "LEANUP_SERVER_URL=http://cache.local:8000" in (home / ".env").read_text(encoding="utf-8")


def test_elan_pack_excludes_toolchains_and_preserves_symlinks(tmp_path, monkeypatch):
    runner = CliRunner()
    leanup_home = tmp_path / "leanup"
    elan_home = _create_elan_home(tmp_path)
    _create_toolchain(elan_home)
    (elan_home / "env-target").write_text("env\n", encoding="utf-8")
    (elan_home / "env-link").symlink_to("env-target")
    monkeypatch.setenv("LEANUP_HOME", str(leanup_home))

    result = runner.invoke(cli, ["elan", "pack", "--elan-home", str(elan_home)])

    archive = leanup_home / "cache" / "serve" / "elan" / "base" / "elan-base.tar.gz"
    assert result.exit_code == 0, result.output
    assert archive.exists()
    with tarfile.open(archive, "r:gz") as tar:
        names = tar.getnames()
        link = tar.getmember(".elan/env-link")
    assert ".elan/settings.toml" in names
    assert not any(name.startswith(".elan/toolchains") for name in names)
    assert link.issym()


def test_lean_pack_and_unpack_preserves_toolchain_symlinks(tmp_path, monkeypatch):
    runner = CliRunner()
    leanup_home = tmp_path / "leanup"
    elan_home = _create_elan_home(tmp_path)
    _create_toolchain(elan_home)
    restored_home = tmp_path / "restored-elan"
    monkeypatch.setenv("LEANUP_HOME", str(leanup_home))

    pack = runner.invoke(cli, ["lean", "pack", "v4.30.0", "--elan-home", str(elan_home)])
    unpack = runner.invoke(cli, ["lean", "unpack", "v4.30.0", "--elan-home", str(restored_home)])

    restored_toolchain = restored_home / "toolchains" / "leanprover--lean4---v4.30.0"
    assert pack.exit_code == 0, pack.output
    assert unpack.exit_code == 0, unpack.output
    assert (restored_toolchain / "bin" / "lean").exists()
    assert (restored_toolchain / "lib-link").is_symlink()
    assert (restored_toolchain / "lib-link").readlink() == Path("lib-target")
