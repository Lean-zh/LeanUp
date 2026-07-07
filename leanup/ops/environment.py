from __future__ import annotations

from pathlib import Path
import os
import subprocess
import tarfile
import tempfile
from urllib.parse import urljoin

import requests

from leanup.paths import cache_dir, elan_home, ensure_base_dirs, server_url
from leanup.repo.mathlib_cache import normalize_lean_version, remove_path


def download_to(url: str, output_file: Path) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_file.parent, prefix=f".{output_file.name}.", suffix=".tmp", delete=False) as handle:
        temp_output = Path(handle.name)
    try:
        with requests.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()
            with temp_output.open("wb") as output_handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output_handle.write(chunk)
        temp_output.replace(output_file)
        return output_file
    except Exception:
        remove_path(temp_output)
        raise


def safe_extract(archive: Path, target_dir: Path) -> None:
    target_dir = target_dir.resolve()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            member_path = (target_dir / member.name).resolve()
            if not str(member_path).startswith(str(target_dir)):
                raise ValueError(f"Archive contains unsafe path: {member.name}")
        try:
            tar.extractall(target_dir, filter="data")
        except TypeError:
            tar.extractall(target_dir)


def atomic_replace_dir(source_dir: Path, target_dir: Path) -> Path:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    replacement = target_dir.parent / f".{target_dir.name}.replace-{os.getpid()}"
    remove_path(replacement)
    source_dir.replace(replacement)
    remove_path(target_dir)
    replacement.replace(target_dir)
    return target_dir


def tar_directory(source_dir: Path, arcname: str, output_file: Path, exclude: set[str] | None = None) -> Path:
    if not source_dir.exists():
        raise ValueError(f"Source directory not found: {source_dir}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_file.parent, prefix=f".{output_file.name}.", suffix=".tmp", delete=False) as handle:
        temp_output = Path(handle.name)
    try:
        with tarfile.open(temp_output, "w:gz", dereference=False) as tar:
            if exclude:
                for child in sorted(source_dir.iterdir()):
                    if child.name in exclude:
                        continue
                    tar.add(child, arcname=f"{arcname}/{child.name}", recursive=True)
            else:
                tar.add(source_dir, arcname=arcname, recursive=True)
        temp_output.replace(output_file)
        return output_file
    except Exception:
        remove_path(temp_output)
        raise


def resolve_server(explicit: str | None = None) -> str | None:
    return explicit or server_url()


def init_leanup_home(home: Path | None = None, server: str | None = None) -> Path:
    from leanup.paths import set_env_value

    root = home or Path(os.environ.get("LEANUP_HOME", Path.home() / ".leanup")).expanduser()
    ensure_base_dirs(root)
    if server:
        set_env_value("LEANUP_SERVER_URL", server, root)
    return root


def elan_archive_path() -> Path:
    return cache_dir() / "serve" / "elan" / "base" / "elan-base.tar.gz"


def lean_archive_path(version: str) -> Path:
    return cache_dir() / "serve" / "lean" / normalize_lean_version(version) / "toolchain.tar.gz"


def toolchain_name(version: str) -> str:
    return f"leanprover--lean4---{normalize_lean_version(version)}"


def pack_elan(source_home: Path | None = None) -> Path:
    source = source_home or elan_home()
    return tar_directory(source, ".elan", elan_archive_path(), exclude={"toolchains"})


def get_elan(server: str | None = None) -> Path:
    base = resolve_server(server)
    if not base:
        raise ValueError("No server configured. Use --server or leanup config set-server.")
    return download_to(urljoin(base.rstrip("/") + "/", "elan/base/elan-base.tar.gz"), elan_archive_path())


def unpack_elan(archive: Path | None = None, target_home: Path | None = None) -> Path:
    archive_path = archive or elan_archive_path()
    target = target_home or elan_home()
    with tempfile.TemporaryDirectory(prefix="leanup-elan-unpack-") as work:
        work_root = Path(work)
        safe_extract(archive_path, work_root)
        extracted = work_root / ".elan"
        if not extracted.exists():
            raise ValueError(f"Archive does not contain .elan/: {archive_path}")
        return atomic_replace_dir(extracted, target)


def install_elan(server: str | None = None, target_home: Path | None = None) -> Path:
    target = target_home or elan_home()
    if (target / "bin" / "elan").exists():
        return target
    get_elan(server)
    return unpack_elan(elan_archive_path(), target)


def check_elan(target_home: Path | None = None) -> str:
    target = target_home or elan_home()
    elan_bin = target / "bin" / "elan"
    if not elan_bin.exists():
        raise ValueError(f"elan not found: {elan_bin}")
    result = subprocess.run([str(elan_bin), "--version"], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "elan --version failed")
    return result.stdout.strip()


def pack_lean(version: str, source_home: Path | None = None) -> Path:
    source = (source_home or elan_home()) / "toolchains" / toolchain_name(version)
    return tar_directory(source, f".elan/toolchains/{source.name}", lean_archive_path(version))


def get_lean(version: str, server: str | None = None) -> Path:
    base = resolve_server(server)
    if not base:
        raise ValueError("No server configured. Use --server or leanup config set-server.")
    return download_to(urljoin(base.rstrip("/") + "/", f"lean/{normalize_lean_version(version)}/toolchain.tar.gz"), lean_archive_path(version))


def unpack_lean(version: str, archive: Path | None = None, target_home: Path | None = None) -> Path:
    archive_path = archive or lean_archive_path(version)
    home = target_home or elan_home()
    with tempfile.TemporaryDirectory(prefix="leanup-lean-unpack-") as work:
        work_root = Path(work)
        safe_extract(archive_path, work_root)
        toolchains_root = work_root / ".elan" / "toolchains"
        candidates = [path for path in toolchains_root.iterdir() if path.is_dir()] if toolchains_root.exists() else []
        if len(candidates) != 1:
            raise ValueError(f"Archive must contain exactly one toolchain directory: {archive_path}")
        target = home / "toolchains" / candidates[0].name
        return atomic_replace_dir(candidates[0], target)


def install_lean(version: str, server: str | None = None, target_home: Path | None = None) -> Path:
    home = target_home or elan_home()
    target = home / "toolchains" / toolchain_name(version)
    if target.exists():
        return target
    base = resolve_server(server)
    if base:
        try:
            get_lean(version, base)
            return unpack_lean(version, lean_archive_path(version), home)
        except requests.RequestException:
            pass
    elan_bin = home / "bin" / "elan"
    if not elan_bin.exists():
        raise ValueError(f"elan not found: {elan_bin}. Run leanup elan install first.")
    result = subprocess.run([str(elan_bin), "toolchain", "install", f"leanprover/lean4:{normalize_lean_version(version)}"], text=True)
    if result.returncode != 0:
        raise RuntimeError("elan toolchain install failed")
    return target


def list_installed_lean(target_home: Path | None = None) -> list[str]:
    root = (target_home or elan_home()) / "toolchains"
    if not root.exists():
        return []
    return [child.name for child in sorted(root.iterdir()) if child.is_dir()]


def check_lean(version: str, target_home: Path | None = None) -> str:
    home = target_home or elan_home()
    toolchain = home / "toolchains" / toolchain_name(version)
    if not toolchain.exists():
        raise ValueError(f"toolchain not found: {toolchain}")
    lean_bin = toolchain / "bin" / "lean"
    if not lean_bin.exists():
        raise ValueError(f"lean not found: {lean_bin}")
    result = subprocess.run([str(lean_bin), "--version"], text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "lean --version failed")
    return result.stdout.strip()
