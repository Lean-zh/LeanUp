# LeanUp

<div align="center">
    <a href="https://pypi.python.org/pypi/leanup">
        <img src="https://img.shields.io/pypi/v/leanup.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/Lean-zh/LeanUp/actions/workflows/ci.yaml">
        <img src="https://github.com/Lean-zh/LeanUp/actions/workflows/ci.yaml/badge.svg" alt="Tests" />
    </a>
    <a href="https://codecov.io/gh/Lean-zh/LeanUp">
        <img src="https://codecov.io/gh/Lean-zh/LeanUp/branch/main/graph/badge.svg" alt="Coverage" />
    </a>
</div>

<div align="center">

**A Python tool for managing Lean mathematical proof language environments**

[English](README-en.md) | [简体中文](README.md)

</div>

## 🎯 Features

- **📦 Repository Management**: Install and manage Lean repositories with interactive configuration
- **🌍 Cross-platform Support**: Works on Linux, macOS, and Windows
- **📦 Easy Installation**: Quick setup via `pip install leanup`
- **🔄 Command Proxy**: Transparent proxy for all elan commands with seamless experience

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install leanup

# Or clone the repository and install
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp
pip install -e .
```

### Basic Usage

```bash
# View help
leanup --help

# Install elan and initialize configuration
leanup init

# Install latest stable version
leanup install

# View status
leanup status

# Proxy execute elan commands
leanup elan --help
leanup elan toolchain list
leanup elan toolchain install stable
leanup elan default stable
```

## 📖 Detailed Usage Guide

### Managing Lean Toolchains

After installing elan, you can use `leanup elan` commands to manage Lean toolchains:

```bash
# List all available toolchains
leanup elan toolchain list

# Install stable toolchain
leanup elan toolchain install stable

# Install nightly build
leanup elan toolchain install leanprover/lean4:nightly

# Set default toolchain
leanup elan default stable

# Update all toolchains
leanup elan update

# Show current active toolchain
leanup elan show
```

### Repository Management

```bash
# Install a repository from default source
leanup repo install mathlib4

# Install with interactive configuration
leanup repo install mathlib4 --interactive

# Install from specific source
leanup repo install mathlib4 --source github

# Install from full URL
leanup repo install --url https://github.com/leanprover-community/mathlib4.git

# Install specific branch or tag
leanup repo install mathlib4 --branch v4.3.0

# Force replace existing directory
leanup repo install mathlib4 --force

# Install to custom directory
leanup repo install mathlib4 --dest-dir /path/to/custom/dir

# List installed repositories
leanup repo list
```

### Interactive Installation

When using `--interactive` flag with `leanup repo install`, you can configure:

- Repository prefix (e.g., `leanprover-community/`)
- Base URL for repository sources
- Cache directory for storing repositories
- Whether to run `lake update` after cloning
- Whether to run `lake build` after cloning
- Specific build packages to compile


## 🛠️ Development

### Environment Setup

```bash
# Clone repository
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp

# Install development dependencies
pip install -e ".[dev]"

# Install project (editable mode)
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage report
coverage run -m pytest tests/
coverage report -m
```

## ⚙️ Configuration

LeanUp uses a configuration file located at `~/.leanup/config.toml`. You can customize:

- Default repository source
- Cache directory for repositories
- Auto-installation settings for elan
- Repository prefixes and base URLs

## 🌍 Cross-platform Support

LeanUp is tested on the following platforms:

- **Linux**: Ubuntu 20.04+, CentOS 7+, Debian 10+
- **macOS**: macOS 10.15+ (Intel and Apple Silicon)
- **Windows**: Windows 10+

## 📊 Project Status

| Feature | Status | Description |
|---------|--------|-------------|
| elan Installation | ✅ | Supports automatic platform and version detection |
| Command Proxy | ✅ | Transparent forwarding of all elan commands |
| Repository Management | ✅ | Install and manage Lean repositories |
| Interactive Configuration | ✅ | User-friendly setup process |
| Cross-platform Support | ✅ | Linux/macOS/Windows |
| Unit Tests | ✅ | Coverage > 85% |
| CI/CD | ✅ | GitHub Actions multi-platform testing |

## 🤝 Contributing

Contributions are welcome! Please see the [Contributing Guide](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🔗 Related Links

- [Lean Official Website](https://leanprover.github.io/)
- [Lean Community Documentation](https://leanprover-community.github.io/)
- [elan Toolchain Manager](https://github.com/leanprover/elan)