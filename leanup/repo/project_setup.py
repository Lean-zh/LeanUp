from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlparse

from leanup.repo.elan import ElanManager
from leanup.repo.mathlib_cache import MathlibCacheManager, normalize_lean_version, remove_path
from leanup.repo.manager import LeanRepo
from leanup.utils.basic import working_directory
from leanup.utils.custom_logger import setup_logger

logger = setup_logger("project_setup")
TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "templates" / "mathlib"


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
            return "copy"
        return "symlink"

    @property
    def toolchain(self) -> str:
        return f"leanprover/lean4:{self.lean_version}"

    @property
    def mathlib_cache_dir(self) -> Path:
        return MathlibCacheManager().get_local_packages_dir(self.lean_version)

    def validate(self) -> None:
        if self.resolved_dependency_mode not in {"symlink", "copy"}:
            raise ValueError("Dependency mode must be either 'symlink' or 'copy'.")
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
        logger.info(f"Preparing Lean project at {config.target_dir}")
        self._ensure_target_available(config)
        self._ensure_toolchain(config.lean_version)

        with working_directory() as temp_dir:
            project_dir = temp_dir / config.project_name
            logger.info(f"Generating project skeleton for {config.project_name}")
            self._create_project_skeleton(config, project_dir)
            project = LeanRepo(project_dir)
            self._write_toolchain(project_dir, config.toolchain)

            used_cache = False
            cache_dir = config.mathlib_cache_dir if config.mathlib else None

            if config.mathlib and config.resolved_dependency_mode in {"symlink", "copy"}:
                logger.info("Checking reusable mathlib package cache")
                used_cache = self._prepare_mathlib_cache(config, project_dir)
                if used_cache:
                    self._write_manifest_from_packages(config, project_dir)

            if config.mathlib and self._should_run_lake_update(config, project_dir):
                logger.info("Running lake update")
                self._run_lake_update(project)
                logger.info("Running lake exe cache get")
                self._run_lake_cache_get(project)
                logger.info("Refreshing shared packages cache")
                self._refresh_mathlib_cache(config, project_dir)
                logger.info("Generating manifest from resolved packages")
                self._write_manifest_from_packages(config, project_dir)
                if config.resolved_dependency_mode == "symlink":
                    logger.info("Linking shared packages cache into project")
                    self._link_mathlib_cache(config, project_dir)
                    used_cache = True
                elif config.resolved_dependency_mode == "copy":
                    logger.info("Copying shared packages cache into project")
                    self._copy_mathlib_cache(config, project_dir)

            logger.info("Running lake build")
            self._run_lake_build(project)
            logger.info("Verifying project with Mathlib.Init and Lean.versionString")
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
        logger.info(f"Ensuring Lean toolchain {version} is installed")
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

    def _write_manifest_from_packages(self, config: SetupConfig, project_dir: Path) -> None:
        packages_dir = project_dir / ".lake" / "packages"
        if not packages_dir.exists():
            return
        if not self._can_generate_manifest_from_packages(packages_dir):
            logger.info("Skipping manifest generation from packages because git metadata is incomplete")
            return

        mathlib_manifest = self._read_mathlib_embedded_manifest(packages_dir)
        packages = []
        for package_dir in sorted(path for path in packages_dir.iterdir() if path.is_dir()):
            packages.append(
                self._build_manifest_entry(
                    package_dir=package_dir,
                    lean_version=config.lean_version,
                    mathlib_manifest=mathlib_manifest,
                )
            )

        manifest = {
            "version": "1.1.0",
            "packagesDir": ".lake/packages",
            "packages": packages,
            "name": config.project_name,
            "lakeDir": ".lake",
        }
        manifest_path = project_dir / "lake-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    def _can_generate_manifest_from_packages(self, packages_dir: Path) -> bool:
        package_dirs = [path for path in packages_dir.iterdir() if path.is_dir()]
        if not package_dirs:
            return False
        for package_dir in package_dirs:
            if not (package_dir / ".git").exists():
                return False
        return True

    def _read_mathlib_embedded_manifest(self, packages_dir: Path) -> dict[str, dict]:
        mathlib_manifest_path = packages_dir / "mathlib" / "lake-manifest.json"
        if not mathlib_manifest_path.exists():
            return {}
        manifest = json.loads(mathlib_manifest_path.read_text(encoding="utf-8"))
        return {entry["name"]: entry for entry in manifest.get("packages", [])}

    def _build_manifest_entry(
        self,
        package_dir: Path,
        lean_version: str,
        mathlib_manifest: dict[str, dict],
    ) -> dict:
        package_name = package_dir.name
        url = self._read_git_origin_url(package_dir)
        head_rev = self._read_git_head(package_dir)
        config_file = self._detect_config_file(package_dir)
        inherited = package_name != "mathlib"
        input_rev = lean_version if package_name == "mathlib" else mathlib_manifest.get(package_name, {}).get("inputRev", "main")

        return {
            "url": url,
            "type": "git",
            "subDir": None,
            "scope": self._infer_scope(url),
            "rev": head_rev,
            "name": package_name,
            "manifestFile": "lake-manifest.json",
            "inputRev": input_rev,
            "inherited": inherited,
            "configFile": config_file,
        }

    def _read_git_origin_url(self, package_dir: Path) -> str:
        from git import Repo

        repo = Repo(package_dir)
        return next(repo.remote("origin").urls)

    def _read_git_head(self, package_dir: Path) -> str:
        from git import Repo

        repo = Repo(package_dir)
        return repo.head.commit.hexsha

    def _detect_config_file(self, package_dir: Path) -> str:
        if (package_dir / "lakefile.lean").exists():
            return "lakefile.lean"
        if (package_dir / "lakefile.toml").exists():
            return "lakefile.toml"
        raise RuntimeError(f"No Lake config file found in package: {package_dir}")

    def _infer_scope(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 2:
            return parts[-2]
        return ""

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

        if config.resolved_dependency_mode == "symlink":
            self._link_mathlib_cache(config, project_dir)
        elif config.resolved_dependency_mode == "copy":
            self._copy_mathlib_cache(config, project_dir)
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

    def _copy_mathlib_cache(self, config: SetupConfig, project_dir: Path) -> None:
        cache_dir = self.cache_manager.get_local_packages_dir(config.lean_version)
        packages_dir = project_dir / ".lake" / "packages"
        packages_dir.parent.mkdir(parents=True, exist_ok=True)
        remove_path(packages_dir)
        shutil.copytree(cache_dir, packages_dir, symlinks=True)

    def _refresh_mathlib_cache(self, config: SetupConfig, project_dir: Path) -> None:
        source_dir = project_dir / ".lake" / "packages"
        if not source_dir.exists():
            logger.warning("Skipping cache refresh because .lake/packages does not exist.")
            return

        self.cache_manager.refresh_local_cache(config.lean_version, source_dir)
