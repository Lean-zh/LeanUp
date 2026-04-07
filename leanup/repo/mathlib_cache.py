from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import tarfile

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
    local_path: Path

    @property
    def local_available(self) -> bool:
        return self.local_path.exists()


class MathlibCacheManager:
    def __init__(self, cache_root: Path | None = None):
        self.cache_root = cache_root or (LEANUP_CACHE_DIR / "setup" / "mathlib")

    def get_local_packages_dir(self, version: str) -> Path:
        return self.cache_root / normalize_lean_version(version) / "packages"

    def list_entries(self) -> list[CacheEntry]:
        versions = set()
        if self.cache_root.exists():
            for child in self.cache_root.iterdir():
                if child.is_dir() and LEAN_VERSION_PATTERN.match(child.name):
                    versions.add(normalize_lean_version(child.name))

        return [
            CacheEntry(
                version=version,
                local_path=self.get_local_packages_dir(version),
            )
            for version in sorted(versions)
        ]

    def ensure_local_cache(self, version: str) -> Path | None:
        local_path = self.get_local_packages_dir(version)
        if local_path.exists():
            return local_path
        return None

    def refresh_local_cache(self, version: str, source_dir: Path, force: bool = True) -> Path:
        normalized = normalize_lean_version(version)
        version_root = self.cache_root / normalized
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

    def pack_packages_archive(self, packages_dir: Path, output_file: Path) -> Path:
        if not packages_dir.exists() or not packages_dir.is_dir():
            raise ValueError(f"Packages directory not found: {packages_dir}")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        if output_file.exists():
            output_file.unlink()

        with tarfile.open(output_file, "w:gz", dereference=False) as tar:
            tar.add(packages_dir, arcname="packages", recursive=True)

        logger.info(f"Packed {packages_dir} -> {output_file}")
        return output_file
