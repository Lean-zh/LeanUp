from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
from urllib.parse import urljoin

import requests

from leanup.const import LEANUP_CACHE_DIR
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("mathlib_cache")

LEAN_VERSION_PATTERN = re.compile(r"^v?4\.\d+\.\d+$")


def normalize_lean_version(version: str) -> str:
    normalized = version.strip()
    if not LEAN_VERSION_PATTERN.match(normalized):
        raise ValueError("Lean version must look like v4.x.x or 4.x.x.")
    if not normalized.startswith("v"):
        normalized = f"v{normalized}"
    return normalized


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    shutil.rmtree(path)


@dataclass
class CacheEntry:
    version: str
    packages_path: Path
    archive_path: Path

    @property
    def local_available(self) -> bool:
        return self.packages_path.exists() or self.archive_path.exists()


class MathlibCacheManager:
    def __init__(self, cache_root: Path | None = None):
        self.cache_root = cache_root or (LEANUP_CACHE_DIR / "mathlib")
        self.packages_root = self.cache_root / "packages"
        self.archives_root = self.cache_root / "archives"

    def get_local_packages_dir(self, version: str) -> Path:
        return self.packages_root / normalize_lean_version(version) / "packages"

    def get_local_archive_path(self, version: str) -> Path:
        return self.archives_root / normalize_lean_version(version) / "packages.tar.gz"

    def list_entries(self) -> list[CacheEntry]:
        versions = set()
        for root in (self.packages_root, self.archives_root):
            if not root.exists():
                continue
            for child in root.iterdir():
                if child.is_dir() and LEAN_VERSION_PATTERN.match(child.name):
                    versions.add(normalize_lean_version(child.name))

        return [
            CacheEntry(
                version=version,
                packages_path=self.get_local_packages_dir(version),
                archive_path=self.get_local_archive_path(version),
            )
            for version in sorted(versions)
        ]

    def list_remote_entries(self, base_url: str) -> list[CacheEntry]:
        index_url = urljoin(base_url.rstrip("/") + "/", "packages/mathlib/index.json")
        try:
            response = requests.get(index_url, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        entries: list[CacheEntry] = []
        for version in payload.get("versions", []):
            try:
                normalized = normalize_lean_version(version)
            except ValueError:
                continue
            entries.append(
                CacheEntry(
                    version=normalized,
                    packages_path=self.get_local_packages_dir(normalized),
                    archive_path=self.get_local_archive_path(normalized),
                )
            )
        return entries

    def ensure_local_cache(self, version: str) -> Path | None:
        local_path = self.get_local_packages_dir(version)
        if local_path.exists():
            return local_path
        return None

    def refresh_local_cache(self, version: str, source_dir: Path, force: bool = True) -> Path:
        normalized = normalize_lean_version(version)
        version_root = self.packages_root / normalized
        packages_dir = version_root / "packages"
        if packages_dir.exists() and not force:
            return packages_dir

        version_root.mkdir(parents=True, exist_ok=True)
        temp_root = version_root / ".packages.tmp"
        remove_path(temp_root)
        shutil.copytree(source_dir, temp_root, symlinks=True)

        remove_path(packages_dir)
        temp_root.replace(packages_dir)
        logger.info(f"Refreshed mathlib cache {normalized} from {source_dir}")
        return packages_dir

    def pack_packages_archive(self, packages_dir: Path, output_file: Path, use_pigz: bool = False) -> Path:
        if not packages_dir.exists() or not packages_dir.is_dir():
            raise ValueError(f"Packages directory not found: {packages_dir}")

        source_dir = packages_dir.resolve() if packages_dir.is_symlink() else packages_dir
        logger.info(f"Preparing packages archive from {packages_dir}")
        if packages_dir.is_symlink():
            logger.info(f"Resolved root packages symlink to {source_dir}")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        temp_output = output_file.parent / f".{output_file.name}.tmp"
        remove_path(temp_output)

        if use_pigz and shutil.which("pigz"):
            logger.info("Using pigz for parallel compression")
            self._pack_with_pigz(source_dir, temp_output)
        else:
            if use_pigz:
                logger.info("pigz requested but not found; falling back to standard gzip")
            else:
                logger.info("Using standard gzip compression")
            logger.info(f"Writing tar.gz archive to temporary file {temp_output}")
            with tarfile.open(temp_output, "w:gz", dereference=False) as tar:
                tar.add(source_dir, arcname="packages", recursive=True)

        remove_path(output_file)
        temp_output.replace(output_file)

        logger.info(f"Packed {source_dir} -> {output_file}")
        return output_file

    def build_archive_url(self, version: str, base_url: str) -> str:
        normalized = normalize_lean_version(version)
        return urljoin(base_url.rstrip("/") + "/", f"packages/mathlib/{normalized}/packages.tar.gz")

    def download_archive(self, version: str, url: str) -> Path:
        output_file = self.get_local_archive_path(version)
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

    def extract_archive(self, archive_file: Path, target_packages_dir: Path) -> Path:
        if not archive_file.exists() or not archive_file.is_file():
            raise ValueError(f"Archive not found: {archive_file}")

        parent_dir = target_packages_dir.parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        temp_root = Path(
            tempfile.mkdtemp(prefix=f".{target_packages_dir.name}.", suffix=".tmp", dir=parent_dir)
        )

        try:
            with tarfile.open(archive_file, "r:gz") as tar:
                self._safe_extract(tar, temp_root)

            extracted_packages_dir = temp_root / "packages"
            if not extracted_packages_dir.exists() or not extracted_packages_dir.is_dir():
                raise ValueError(f"Archive does not contain top-level packages/ directory: {archive_file}")

            final_temp = parent_dir / f".{target_packages_dir.name}.replace-{os.getpid()}"
            remove_path(final_temp)
            extracted_packages_dir.replace(final_temp)

            remove_path(target_packages_dir)
            final_temp.replace(target_packages_dir)
            remove_path(temp_root)

            logger.info(f"Extracted {archive_file} -> {target_packages_dir}")
            return target_packages_dir
        except Exception:
            remove_path(temp_root)
            raise

    def fetch_packages(self, version: str, base_url: str) -> Path:
        archive = self.download_archive(version, self.build_archive_url(version, base_url))
        return self.extract_archive(archive, self.get_local_packages_dir(version))

    def _pack_with_pigz(self, source_dir: Path, output_file: Path) -> None:
        logger.info(f"Streaming tar archive from {source_dir.parent} into pigz")
        transform = f"s,^{re.escape(source_dir.name)},packages,"
        with output_file.open("wb") as output_handle:
            tar_proc = subprocess.Popen(
                [
                    "tar",
                    "-C",
                    str(source_dir.parent),
                    "--transform",
                    transform,
                    "-cf",
                    "-",
                    source_dir.name,
                ],
                stdout=subprocess.PIPE,
            )
            try:
                subprocess.run(["pigz", "-c"], check=True, stdin=tar_proc.stdout, stdout=output_handle)
            finally:
                if tar_proc.stdout is not None:
                    tar_proc.stdout.close()
                tar_returncode = tar_proc.wait()
                if tar_returncode != 0:
                    raise subprocess.CalledProcessError(tar_returncode, tar_proc.args)

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
