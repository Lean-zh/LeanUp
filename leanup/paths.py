from __future__ import annotations

from pathlib import Path
import os


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def default_home() -> Path:
    return Path(os.environ.get("LEANUP_HOME", Path.home() / ".leanup")).expanduser()


def env_file(home: Path | None = None) -> Path:
    return (home or default_home()) / ".env"


def load_dotenv(home: Path | None = None) -> dict[str, str]:
    return _read_env_file(env_file(home))


def get_config_value(name: str, default: str | Path | None = None) -> str | None:
    if name in os.environ:
        return os.environ[name]
    values = load_dotenv()
    if name in values:
        return values[name]
    if default is None:
        return None
    return str(default)


def leanup_home() -> Path:
    return Path(get_config_value("LEANUP_HOME", Path.home() / ".leanup") or Path.home() / ".leanup").expanduser()


def cache_dir() -> Path:
    home = leanup_home()
    return Path(get_config_value("LEANUP_CACHE_DIR", home / "cache") or home / "cache").expanduser()


def config_dir() -> Path:
    home = leanup_home()
    return Path(get_config_value("LEANUP_CONFIG_DIR", home / "config") or home / "config").expanduser()


def tmp_dir() -> Path:
    home = leanup_home()
    return Path(get_config_value("LEANUP_TMP_DIR", home / "tmp") or home / "tmp").expanduser()


def elan_home() -> Path:
    default = os.environ.get("ELAN_HOME", str(Path.home() / ".elan"))
    return Path(get_config_value("LEANUP_ELAN_HOME", default) or default).expanduser()


def server_url() -> str | None:
    return get_config_value("LEANUP_SERVER_URL")


def ensure_base_dirs(home: Path | None = None) -> Path:
    root = home or leanup_home()
    for rel in [
        "config",
        "repos",
        "cache/serve/elan/base",
        "cache/serve/lean",
        "cache/serve/mathlib",
        "cache/local/mathlib",
        "cache/downloads",
        "tmp",
        "logs",
        "state/locks",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)
    env_path = root / ".env"
    if not env_path.exists():
        env_path.write_text(
            "# LeanUp environment configuration\n"
            f"LEANUP_HOME={root}\n"
            f"LEANUP_CACHE_DIR={root / 'cache'}\n"
            f"LEANUP_CONFIG_DIR={root / 'config'}\n"
            f"LEANUP_TMP_DIR={root / 'tmp'}\n"
            f"LEANUP_ELAN_HOME={Path.home() / '.elan'}\n",
            encoding="utf-8",
        )
    return root


def set_env_value(key: str, value: str, home: Path | None = None) -> Path:
    root = home or leanup_home()
    ensure_base_dirs(root)
    path = root / ".env"
    values = _read_env_file(path)
    values[key] = value
    lines = ["# LeanUp environment configuration"]
    for item_key in sorted(values):
        lines.append(f"{item_key}={values[item_key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
