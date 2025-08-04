# LeanUp

A Python package for managing Lean mathematical proof language environments.

## Features

- **🔧 elan Management**: Install and manage the Lean toolchain manager elan with a single command
- **📦 Repository Management**: Install and manage Lean repositories with advanced configuration options
- **🌍 Cross-platform Support**: Works on Linux, macOS, and Windows
- **📦 Easy Installation**: Quick setup via `pip install leanup`

## Quick Start

Check the [Quick Start](getting-started/quickstart.md) guide to begin using LeanUp.

## Command Line Interface

LeanUp provides a comprehensive CLI with the following commands:

### Main Commands

- `leanup init` - Initialize elan installation
- `leanup install [version]` - Install Lean toolchain version via elan
- `leanup status` - Show current status and installed toolchains
- `leanup elan <args>` - Proxy elan commands

### Repository Management

- `leanup repo install <repository>` - Install Lean repositories with flexible configuration
- `leanup repo list` - List installed repositories with filtering options

#### Repository Install Options

- `--source` - Repository source URL (default: https://github.com)
- `--branch` - Branch or tag to clone
- `--force` - Replace existing directory
- `--dest-dir` - Destination directory
- `--dest-name` - Custom destination name
- `--interactive` - Interactive configuration mode
- `--lake-update` - Run lake update after cloning (default: true)
- `--lake-build` - Run lake build after cloning (default: true)
- `--build-packages` - Specific packages to build

## Modules

### CLI Module

The `leanup.cli` module provides the command-line interface:

- **Main CLI**: Core commands for elan management and status monitoring
- **Repository CLI**: Commands for managing Lean repositories with advanced options

### Utils Module

The `leanup.utils` module provides utility functions for the package:

- `execute_command`: Execute shell commands with proper error handling and cross-platform support
- `setup_logger`: Configure a logger with customizable output formats and color support

### Repo Module

The `leanup.repo` module provides repository management functionality:

- `InstallConfig`: Configuration class for repository installation with validation
- `RepoManager`: Base class for directory and git operations
- `LeanRepo`: Specialized class for Lean project management with lake support
- `ElanManager`: Manage elan installation and toolchain operations