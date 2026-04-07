from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil

from leanup.repo.elan import ElanManager
from leanup.repo.mathlib_cache import MathlibCacheManager, normalize_lean_version, remove_path
from leanup.repo.manager import LeanRepo
from leanup.utils.basic import working_directory
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("project_setup")


def sanitize_project_name(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_]", "", name.strip())
    if not sanitized:
        sanitized = "LeanProject"
    if sanitized[0].isdigit():
        sanitized = f"Lean{sanitized}"
    return sanitized


@dataclass
class SetupConfig:
    target_dir: Path
    lean_version: str
    project_name: str | None = None
    mathlib: bool = True
    dependency_mode: str | None = None
    force: bool = False

    def __post_init__(self) -> None:
        self.target_dir = Path(self.target_dir).expanduser().resolve()
        self.lean_version = normalize_lean_version(self.lean_version)
        default_name = self.project_name or self.target_dir.name
        self.project_name = sanitize_project_name(default_name)

    @property
    def template(self) -> str:
        return "math" if self.mathlib else "std"

    @property
    def resolved_dependency_mode(self) -> str:
        if self.dependency_mode:
            return self.dependency_mode
        if not self.mathlib:
            return "build"
        return "symlink" if self.mathlib_cache_dir.exists() else "build"

    @property
    def toolchain(self) -> str:
        return f"leanprover/lean4:{self.lean_version}"

    @property
    def mathlib_cache_dir(self) -> Path:
        return MathlibCacheManager().get_local_packages_dir(self.lean_version)

    def validate(self) -> None:
        if self.resolved_dependency_mode not in {"symlink", "build"}:
            raise ValueError("Dependency mode must be either 'symlink' or 'build'.")
        if self.resolved_dependency_mode == "symlink" and not self.mathlib:
            raise ValueError("Dependency symlink mode is only available when mathlib is enabled.")


@dataclass
class SetupResult:
    target_dir: Path
    lean_version: str
    mathlib: bool
    dependency_mode: str
    cache_dir: Path | None = None
    used_cache: bool = False


class LeanProjectSetup:
    def __init__(self, elan_manager: ElanManager | None = None):
        self.elan_manager = elan_manager or ElanManager()
        self.cache_manager = MathlibCacheManager()

    def setup(self, config: SetupConfig) -> SetupResult:
        config.validate()
        self._ensure_target_available(config)
        self._ensure_toolchain(config.lean_version)

        with working_directory() as temp_dir:
            temp_root = LeanRepo(temp_dir)
            stdout, stderr, returncode = temp_root.lake_init(
                config.project_name,
                config.template,
            )
            if returncode != 0:
                raise RuntimeError(stderr or stdout or "Failed to initialize Lean project.")

            project_dir = temp_dir / config.project_name
            project = LeanRepo(project_dir)
            self._write_toolchain(project_dir, config.toolchain)

            used_cache = False
            cache_dir = config.mathlib_cache_dir if config.mathlib else None

            if config.mathlib and config.resolved_dependency_mode == "symlink":
                self._link_mathlib_cache(config, project_dir)
                used_cache = True

            if config.mathlib:
                self._run_lake_update(project)

            self._run_lake_build(project)

            if config.mathlib and config.resolved_dependency_mode == "build":
                self._refresh_mathlib_cache(config, project_dir)

            shutil.move(str(project_dir), str(config.target_dir))

        return SetupResult(
            target_dir=config.target_dir,
            lean_version=config.lean_version,
            mathlib=config.mathlib,
            dependency_mode=config.resolved_dependency_mode,
            cache_dir=cache_dir,
            used_cache=used_cache,
        )

    def _ensure_target_available(self, config: SetupConfig) -> None:
        target = config.target_dir
        if target.exists() or target.is_symlink():
            if not config.force:
                raise ValueError(f"Target directory already exists: {target}")
            remove_path(target)

        target.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_toolchain(self, version: str) -> None:
        if not self.elan_manager.is_elan_installed() and not self.elan_manager.install_elan():
            raise RuntimeError("Failed to install elan.")
        if not self.elan_manager.install_lean(version):
            raise RuntimeError(f"Failed to install Lean toolchain {version}.")

    def _write_toolchain(self, project_dir: Path, toolchain: str) -> None:
        (project_dir / "lean-toolchain").write_text(toolchain + "\n", encoding="utf-8")

    def _run_lake_update(self, repo: LeanRepo) -> None:
        stdout, stderr, returncode = repo.lake_update()
        if returncode != 0:
            raise RuntimeError(stderr or stdout or "lake update failed.")

    def _run_lake_build(self, repo: LeanRepo) -> None:
        stdout, stderr, returncode = repo.lake_build()
        if returncode != 0:
            raise RuntimeError(stderr or stdout or "lake build failed.")

    def _link_mathlib_cache(self, config: SetupConfig, project_dir: Path) -> None:
        cache_dir = self.cache_manager.ensure_local_cache(config.lean_version)
        if not cache_dir:
            raise ValueError(
                "No cached mathlib packages found for this Lean version. "
                "Import one with `leanup mathlib cache import <version>` or run setup with --dependency-mode build first."
            )

        packages_dir = project_dir / ".lake" / "packages"
        packages_dir.parent.mkdir(parents=True, exist_ok=True)
        remove_path(packages_dir)

        try:
            packages_dir.symlink_to(cache_dir, target_is_directory=True)
        except OSError as exc:
            raise RuntimeError(f"Failed to create dependency symlink: {exc}") from exc

    def _refresh_mathlib_cache(self, config: SetupConfig, project_dir: Path) -> None:
        source_dir = project_dir / ".lake" / "packages"
        if not source_dir.exists():
            logger.warning("Skipping cache refresh because .lake/packages does not exist.")
            return

        cache_dir = self.cache_manager.get_local_packages_dir(config.lean_version)
        cache_parent = cache_dir.parent
        cache_parent.mkdir(parents=True, exist_ok=True)

        temp_cache_dir = cache_parent / f".{cache_dir.name}.tmp"
        remove_path(temp_cache_dir)
        shutil.copytree(source_dir, temp_cache_dir, symlinks=True)

        remove_path(cache_dir)
        os.replace(temp_cache_dir, cache_dir)
