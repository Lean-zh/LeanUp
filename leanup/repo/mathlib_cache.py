from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
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
    archive_path: Path | None

    @property
    def local_available(self) -> bool:
        return self.local_path.exists()

    @property
    def importable(self) -> bool:
        return self.archive_path is not None and self.archive_path.exists()


class MathlibCacheManager:
    def __init__(self, cache_root: Path | None = None):
        self.cache_root = cache_root or (LEANUP_CACHE_DIR / "setup" / "mathlib")

    def get_local_packages_dir(self, version: str) -> Path:
        return self.cache_root / normalize_lean_version(version) / "packages"

    def discover_reference_cache_dir(self) -> Path | None:
        explicit = os.getenv("LEANUP_MATHLIB_CACHE_SOURCE")
        candidates = []
        if explicit:
            candidates.append(Path(explicit).expanduser())

        here = Path(__file__).resolve()
        for parent in [Path.cwd().resolve(), *Path.cwd().resolve().parents, *here.parents]:
            candidates.append(parent / "reference" / "Projects" / "cache")

        seen = set()
        for candidate in candidates:
            resolved = str(candidate)
            if resolved in seen:
                continue
            seen.add(resolved)
            if candidate.exists() and candidate.is_dir():
                return candidate
        return None

    def get_reference_archive(self, version: str, source_dir: Path | None = None) -> Path | None:
        normalized = normalize_lean_version(version)
        source_root = source_dir or self.discover_reference_cache_dir()
        if not source_root:
            return None
        archive = source_root / normalized / "packages.tar.gz"
        return archive if archive.exists() else None

    def list_entries(self, source_dir: Path | None = None) -> list[CacheEntry]:
        versions = set()
        if self.cache_root.exists():
            for child in self.cache_root.iterdir():
                if child.is_dir() and LEAN_VERSION_PATTERN.match(child.name):
                    versions.add(normalize_lean_version(child.name))

        reference_root = source_dir or self.discover_reference_cache_dir()
        if reference_root and reference_root.exists():
            for child in reference_root.iterdir():
                if child.is_dir() and LEAN_VERSION_PATTERN.match(child.name):
                    versions.add(normalize_lean_version(child.name))

        return [
            CacheEntry(
                version=version,
                local_path=self.get_local_packages_dir(version),
                archive_path=self.get_reference_archive(version, source_dir=source_dir),
            )
            for version in sorted(versions)
        ]

    def ensure_local_cache(self, version: str, source_dir: Path | None = None) -> Path | None:
        local_path = self.get_local_packages_dir(version)
        if local_path.exists():
            return local_path
        archive = self.get_reference_archive(version, source_dir=source_dir)
        if not archive:
            return None
        self.import_archive(version, archive)
        return local_path

    def import_archive(
        self,
        version: str,
        archive_path: Path | None = None,
        source_dir: Path | None = None,
        force: bool = False,
    ) -> Path:
        normalized = normalize_lean_version(version)
        archive = archive_path or self.get_reference_archive(normalized, source_dir=source_dir)
        if not archive:
            raise ValueError(f"No reference cache archive found for {normalized}.")

        version_root = self.cache_root / normalized
        packages_dir = version_root / "packages"
        if packages_dir.exists():
            if not force:
                return packages_dir
            remove_path(packages_dir)

        version_root.mkdir(parents=True, exist_ok=True)
        temp_root = version_root / ".importing"
        remove_path(temp_root)
        temp_root.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(path=temp_root, filter="data")
            extracted_packages = temp_root / "packages"
            if not extracted_packages.exists():
                raise ValueError(f"Archive {archive} does not contain a packages directory.")
            remove_path(packages_dir)
            os.replace(extracted_packages, packages_dir)
            logger.info(f"Imported mathlib cache {normalized} from {archive}")
            return packages_dir
        finally:
            remove_path(temp_root)
