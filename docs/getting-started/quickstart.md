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

# Force reinstall
leanup install --force
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
# Install a repository (format: owner/repo)
leanup repo install leanprover-community/mathlib4

# Install with specific options
leanup repo install leanprover-community/mathlib4 --branch main --force

# Install to specific directory
leanup repo install leanprover-community/mathlib4 --dest-dir ./my-mathlib

# Install from custom URL
leanup repo install owner/repo --url https://github.com/owner/repo.git

# List installed repositories
leanup repo list

# List repositories with filter
leanup repo list --name mathlib

# Interactive installation
leanup repo install -i
```

## Using the RepoManager

The `RepoManager` class provides functionality for managing directories and git repositories:

```python
from leanup.repo import RepoManager

# Create a repo manager
repo = RepoManager("/path/to/your/directory")

# Check if it's a git repository
if repo.is_gitrepo:
    print("This is a git repository")
    status = repo.git_status()
    print(f"Current branch: {status['branch']}")

# File operations
repo.write_file("test.txt", "Hello world")
content = repo.read_file("test.txt")
repo.edit_file("test.txt", "world", "universe")

# List files and directories
files = repo.list_files("*.lean")
dirs = repo.list_dirs()
```

## Using LeanRepo for Lean Projects

```python
from leanup.repo import LeanRepo

# Create a Lean repo manager
lean_repo = LeanRepo("/path/to/lean/project")

# Get project information
info = lean_repo.get_project_info()
print(f"Lean version: {info['lean_version']}")
print(f"Has lakefile: {info['has_lakefile_toml']}")

# Lake operations (execute commands directly)
stdout, stderr, returncode = lean_repo.lake(["build"])
stdout, stderr, returncode = lean_repo.lake_update()
stdout, stderr, returncode = lean_repo.lake_build()
```