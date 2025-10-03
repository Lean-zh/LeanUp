# Quick Start

## Installation

```bash
# Install from PyPI
pip install leanup

# Or clone the repository and install
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp
pip install -e .
```

## Basic Usage

### Initialize elan

```bash
# View help
leanup --help

# Install elan
leanup init

# View current status
leanup status
```

### Install Lean Toolchain

```bash
# Install latest stable Lean toolchain
leanup install

# Install specific Lean toolchain version
leanup install v4.14.0
```

### Manage Toolchains

```bash
# Proxy execute elan commands
leanup elan --help
leanup elan toolchain list
leanup elan toolchain install stable
leanup elan default stable
```

### Repository Management

```bash
# Install Mathlib
leanup repo install leanprover-community/mathlib4

# Install specific branch or tag
leanup repo install leanprover-community/mathlib4 -b v4.14.0

# Install to custom directory
leanup repo install Lean-zh/leanup -d /path/to/custom/dir

# Control build options
leanup repo install leanprover-community/mathlib4 --lake-build

# Interactive mode
leanup repo install leanprover-community/mathlib4 -i

# Specify packages to build
leanup repo install Lean-zh/repl --build-packages "REPL,REPL.Main"

# List installed repositories
leanup repo list

# Search repositories in specified directory
leanup repo list --search-dir /path/to/repos

# Filter repositories by name
leanup repo list -n mathlib
```

## Using InstallConfig

The `InstallConfig` class provides a programmatic way to configure repository installations:

```python
from pathlib import Path
from leanup.repo.manager import InstallConfig

# Create installation configuration
config = InstallConfig(
    suffix="leanprover-community/mathlib4",
    source="https://github.com",
    branch="main",
    dest_dir=Path("/path/to/repos"),
    dest_name="mathlib4_main",
    lake_update=True,
    lake_build=True,
    build_packages=["REPL", "REPL.Main"],
    override=False
)

# Check if configuration is valid
if config.is_valid:
    print(f"Will install to: {config.dest_path}")
    
# Execute installation
config.install()

# Update configuration
new_config = config.update(branch="v4.3.0", override=True)
```

## Using the RepoManager

The `RepoManager` class provides functionality for managing directories and git repositories:

```python
from leanup.repo.manager import RepoManager

# Create a repo manager
repo = RepoManager("/path/to/your/directory")

# Check if it's a git repository
if repo.is_gitrepo:
    print("This is a git repository")
    status = repo.git_status()
    print(f"Current branch: {status['branch']}")
    print(f"Is dirty: {status['is_dirty']}")

# Clone a repository
success = repo.clone_from(
    "https://github.com/owner/repo.git", 
    branch="main", 
    depth=1
)

# File operations
repo.write_file("test.txt", "Hello world")
content = repo.read_file("test.txt")
repo.edit_file("test.txt", "world", "universe", use_regex=False)

# List files and directories
files = repo.list_files("*.lean")
dirs = repo.list_dirs()

# Execute commands
stdout, stderr, returncode = repo.execute_command(["ls", "-la"])
```

## Using LeanRepo for Lean Projects

```python
from leanup.repo.manager import LeanRepo

# Create a Lean repo manager
lean_repo = LeanRepo("/path/to/lean/project")

# Get project information
info = lean_repo.get_project_info()
print(f"Lean version: {info['lean_version']}")
print(f"Has lakefile.toml: {info['has_lakefile_toml']}")
print(f"Has lakefile.lean: {info['has_lakefile_lean']}")
print(f"Has lake-manifest.json: {info['has_lake_manifest']}")
print(f"Build directory exists: {info['build_dir_exists']}")

# Lake operations
lean_repo.lake_init("my_project", "std", "lean")
lean_repo.lake_update()
lean_repo.lake_build("MyTarget")
lean_repo.lake_env_lean("Main.lean", json=True)
lean_repo.lake_clean()
lean_repo.lake_test()

# Install using configuration
config = InstallConfig(
    suffix="leanprover-community/mathlib4",
    lake_update=True,
    lake_build=False
)
lean_repo.install(config)
```