from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import tempfile

from leanup.repo.elan import ElanManager
from leanup.repo.mathlib_cache import MathlibCacheManager, normalize_lean_version, remove_path
from leanup.repo.manager import LeanRepo
from leanup.utils.basic import working_directory
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("project_setup")
TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "templates" / "mathlib" / "v4.xx.0"
BUNDLED_MANIFEST_ROOT = Path(__file__).resolve().parent.parent / "templates" / "mathlib" / "manifests"


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
        return "symlink"

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
            project_dir = temp_dir / config.project_name
            self._create_project_skeleton(config, project_dir)
            project = LeanRepo(project_dir)
            self._write_toolchain(project_dir, config.toolchain)
            self._copy_reference_manifest(config, project_dir)

            used_cache = False
            cache_dir = config.mathlib_cache_dir if config.mathlib else None

            if config.mathlib and config.resolved_dependency_mode == "symlink":
                used_cache = self._prepare_mathlib_cache(config, project_dir)

            if config.mathlib and self._should_run_lake_update(config, project_dir):
                self._run_lake_update(project)
                self._run_lake_cache_get(project)
                self._refresh_mathlib_cache(config, project_dir)
                if config.resolved_dependency_mode == "symlink":
                    self._link_mathlib_cache(config, project_dir)
                    used_cache = True

            self._run_lake_build(project)
            self._verify_mathlib_project(project_dir)

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

    def _create_project_skeleton(self, config: SetupConfig, project_dir: Path) -> None:
        project_dir.mkdir(parents=True, exist_ok=True)
        if config.mathlib:
            self._render_mathlib_template(config, project_dir)
            return

        repo = LeanRepo(project_dir)
        stdout, stderr, returncode = repo.lake_init(config.project_name, config.template)
        if returncode != 0:
            raise RuntimeError(stderr or stdout or "Failed to initialize Lean project.")

    def _render_mathlib_template(self, config: SetupConfig, project_dir: Path) -> None:
        context = {
            "project_name": config.project_name,
            "lean_version": config.lean_version,
        }
        templates = {
            "README.md.tmpl": project_dir / "README.md",
            "lakefile.lean.tmpl": project_dir / "lakefile.lean",
            "root.lean.tmpl": project_dir / f"{config.project_name}.lean",
            "Basic.lean.tmpl": project_dir / config.project_name / "Basic.lean",
        }
        for template_name, output_path in templates.items():
            content = (TEMPLATE_ROOT / template_name).read_text(encoding="utf-8")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content.format(**context), encoding="utf-8")

    def _bundled_manifest_path(self, version: str) -> Path | None:
        candidate = BUNDLED_MANIFEST_ROOT / normalize_lean_version(version) / "lake-manifest.json"
        if candidate.exists():
            return candidate
        return None

    def _copy_reference_manifest(self, config: SetupConfig, project_dir: Path) -> None:
        if not config.mathlib:
            return
        bundled_manifest = self._bundled_manifest_path(config.lean_version)
        if bundled_manifest:
            manifest_path = project_dir / "lake-manifest.json"
            shutil.copy2(bundled_manifest, manifest_path)
            self._rewrite_manifest_name(manifest_path, config.project_name)

    def _rewrite_manifest_name(self, manifest_path: Path, project_name: str) -> None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["name"] = project_name
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    def _should_run_lake_update(self, config: SetupConfig, project_dir: Path) -> bool:
        if not config.mathlib:
            return False
        manifest = project_dir / "lake-manifest.json"
        packages = project_dir / ".lake" / "packages"
        return not (manifest.exists() and packages.exists())

    def _write_toolchain(self, project_dir: Path, toolchain: str) -> None:
        (project_dir / "lean-toolchain").write_text(toolchain + "\n", encoding="utf-8")

    def _run_lake_update(self, repo: LeanRepo) -> None:
        stdout, stderr, returncode = repo.lake_update()
        if returncode != 0:
            raise RuntimeError(stderr or stdout or "lake update failed.")

    def _run_lake_cache_get(self, repo: LeanRepo) -> None:
        stdout, stderr, returncode = repo.lake(["exe", "cache", "get"])
        if returncode != 0:
            raise RuntimeError(stderr or stdout or "lake exe cache get failed.")

    def _run_lake_build(self, repo: LeanRepo) -> None:
        stdout, stderr, returncode = repo.lake_build()
        if returncode != 0:
            raise RuntimeError(stderr or stdout or "lake build failed.")

    def _verify_mathlib_project(self, project_dir: Path) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".lean", delete=False, encoding="utf-8") as handle:
            handle.write("import Mathlib.Init\n#eval Lean.versionString\n")
            probe = Path(handle.name)
        try:
            repo = LeanRepo(project_dir)
            stdout, stderr, returncode = repo.lake_env_lean(probe, json=False)
            if returncode != 0:
                raise RuntimeError(stderr or stdout or "verification failed.")
        finally:
            if probe.exists():
                probe.unlink()

    def _prepare_mathlib_cache(self, config: SetupConfig, project_dir: Path) -> bool:
        cache_dir = self.cache_manager.ensure_local_cache(config.lean_version)
        if not cache_dir:
            return False

        self._link_mathlib_cache(config, project_dir)
        return True

    def _link_mathlib_cache(self, config: SetupConfig, project_dir: Path) -> None:
        cache_dir = self.cache_manager.get_local_packages_dir(config.lean_version)

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

        self.cache_manager.refresh_local_cache(config.lean_version, source_dir)
