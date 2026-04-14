from __future__ import annotations

import os
from pathlib import Path
import tarfile
import tempfile
from urllib.parse import urljoin

import requests

from leanup.const import LEANUP_CACHE_DIR
from leanup.repo.elan import ElanManager
from leanup.repo.mathlib_cache import normalize_lean_version, remove_path
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("toolchain_cache")


class ToolchainCacheManager:
    def __init__(self, cache_root: Path | None = None, elan_home: Path | None = None):
        self.cache_root = cache_root or (LEANUP_CACHE_DIR / "toolchains")
        self.archives_root = self.cache_root / "archives"
        self.elan_home = elan_home or Path(os.environ.get("ELAN_HOME", Path.home() / ".elan"))

    def get_base_archive_path(self) -> Path:
        return self.archives_root / "base-elan.tar.gz"

    def get_toolchain_archive_path(self, version: str) -> Path:
        return self.archives_root / normalize_lean_version(version) / "toolchain.tar.gz"

    def list_local_versions(self) -> list[str]:
        if not self.archives_root.exists():
            return []
        versions: list[str] = []
        for child in sorted(self.archives_root.iterdir()):
            if child.is_dir() and (child / "toolchain.tar.gz").exists():
                versions.append(child.name)
        return versions

    def has_local_base_archive(self) -> bool:
        return self.get_base_archive_path().exists()

    def list_remote(self, base_url: str) -> tuple[bool, list[str]]:
        index_url = urljoin(base_url.rstrip("/") + "/", "toolchains/index.json")
        try:
            response = requests.get(index_url, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return False, []
        versions = [normalize_lean_version(version) for version in payload.get("versions", [])]
        has_base = bool(payload.get("has_base"))
        return has_base, versions

    def build_base_url(self, base_url: str) -> str:
        return urljoin(base_url.rstrip("/") + "/", "toolchains/base-elan.tar.gz")

    def build_toolchain_url(self, version: str, base_url: str) -> str:
        normalized = normalize_lean_version(version)
        return urljoin(base_url.rstrip("/") + "/", f"toolchains/{normalized}/toolchain.tar.gz")

    def download_base_archive(self, url: str) -> Path:
        return self._download_to(url, self.get_base_archive_path())

    def download_toolchain_archive(self, version: str, url: str) -> Path:
        return self._download_to(url, self.get_toolchain_archive_path(version))

    def init_base(self, url: str | None = None) -> Path:
        if url:
            archive = self.download_base_archive(self.build_base_url(url))
            return self.unpack_base_archive(archive)

        manager = ElanManager(elan_home=self.elan_home)
        if not manager.install_elan():
            raise RuntimeError("Failed to install elan.")
        self.pack_base_archive()
        return self.elan_home

    def pack_base_archive(self) -> Path:
        if not self.elan_home.exists():
            raise ValueError(f"Elan home not found: {self.elan_home}")

        output_file = self.get_base_archive_path()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        temp_output = output_file.parent / f".{output_file.name}.tmp"
        remove_path(temp_output)

        with tarfile.open(temp_output, "w:gz", dereference=False) as tar:
            for child in sorted(self.elan_home.iterdir()):
                if child.name == "toolchains":
                    continue
                tar.add(child, arcname=f".elan/{child.name}", recursive=True)

        remove_path(output_file)
        temp_output.replace(output_file)
        logger.info(f"Packed base elan archive -> {output_file}")
        return output_file

    def unpack_base_archive(self, archive_path: Path | None = None) -> Path:
        archive_path = archive_path or self.get_base_archive_path()
        temp_root = Path(tempfile.mkdtemp(prefix=".elan-base.", dir=self.elan_home.parent))
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                self._safe_extract(tar, temp_root)
            extracted = temp_root / ".elan"
            if not extracted.exists():
                raise ValueError(f"Archive does not contain top-level .elan/ directory: {archive_path}")
            final_temp = self.elan_home.parent / f".{self.elan_home.name}.replace-{os.getpid()}"
            remove_path(final_temp)
            extracted.replace(final_temp)
            remove_path(self.elan_home)
            final_temp.replace(self.elan_home)
            remove_path(temp_root)
            logger.info(f"Unpacked base elan archive -> {self.elan_home}")
            return self.elan_home
        except Exception:
            remove_path(temp_root)
            raise

    def pack_toolchain_archive(self, version: str) -> Path:
        toolchain_dir = self._resolve_installed_toolchain_dir(version)
        if toolchain_dir is None:
            raise ValueError(f"Installed toolchain not found for {normalize_lean_version(version)}")

        output_file = self.get_toolchain_archive_path(version)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        temp_output = output_file.parent / f".{output_file.name}.tmp"
        remove_path(temp_output)

        with tarfile.open(temp_output, "w:gz", dereference=False) as tar:
            tar.add(toolchain_dir, arcname=f".elan/toolchains/{toolchain_dir.name}", recursive=True)

        remove_path(output_file)
        temp_output.replace(output_file)
        logger.info(f"Packed toolchain {version} -> {output_file}")
        return output_file

    def unpack_toolchain_archive(self, version: str, archive_path: Path | None = None) -> Path:
        archive_path = archive_path or self.get_toolchain_archive_path(version)
        temp_root = Path(tempfile.mkdtemp(prefix=".elan-toolchain.", dir=self.elan_home.parent))
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                self._safe_extract(tar, temp_root)
            toolchains_root = temp_root / ".elan" / "toolchains"
            toolchain_dirs = [path for path in toolchains_root.iterdir() if path.is_dir()] if toolchains_root.exists() else []
            if len(toolchain_dirs) != 1:
                raise ValueError(f"Archive must contain exactly one toolchain directory: {archive_path}")
            source_dir = toolchain_dirs[0]
            target_dir = self.elan_home / "toolchains" / source_dir.name
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            final_temp = target_dir.parent / f".{target_dir.name}.replace-{os.getpid()}"
            remove_path(final_temp)
            source_dir.replace(final_temp)
            remove_path(target_dir)
            final_temp.replace(target_dir)
            remove_path(temp_root)
            logger.info(f"Unpacked toolchain archive -> {target_dir}")
            return target_dir
        except Exception:
            remove_path(temp_root)
            raise

    def fetch_toolchain(self, version: str, base_url: str) -> Path:
        archive = self.download_toolchain_archive(version, self.build_toolchain_url(version, base_url))
        return self.unpack_toolchain_archive(version, archive)

    def _resolve_installed_toolchain_dir(self, version: str) -> Path | None:
        normalized = normalize_lean_version(version)
        toolchains_root = self.elan_home / "toolchains"
        if not toolchains_root.exists():
            return None
        for child in sorted(toolchains_root.iterdir()):
            if child.is_dir() and normalized in child.name:
                return child
        return None

    def _download_to(self, url: str, output_file: Path) -> Path:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=output_file.parent,
            prefix=f".{output_file.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_output = Path(handle.name)

        try:
            with requests.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()
                with temp_output.open("wb") as output_handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            output_handle.write(chunk)
            remove_path(output_file)
            temp_output.replace(output_file)
            logger.info(f"Downloaded {url} -> {output_file}")
            return output_file
        except Exception:
            remove_path(temp_output)
            raise

    def _safe_extract(self, tar: tarfile.TarFile, target_dir: Path) -> None:
        target_dir = target_dir.resolve()
        for member in tar.getmembers():
            member_path = (target_dir / member.name).resolve()
            if not str(member_path).startswith(str(target_dir)):
                raise ValueError(f"Archive contains unsafe path: {member.name}")
        try:
            tar.extractall(target_dir, filter="data")
        except TypeError:
            tar.extractall(target_dir)
