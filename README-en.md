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

- **🔧 elan Management**: One-click installation and management of Lean toolchain manager elan
- **🌍 Cross-platform Support**: Supports Linux, macOS, and Windows
- **📦 Easy Installation**: Quick setup via `pip install -e /path/to/LeanUp`
- **🔄 Command Proxy**: Transparent proxy for all elan commands, seamless experience
- **📊 Status Monitoring**: Real-time view of Lean environment status and installed toolchains

## 🚀 Quick Start

### Installation

```bash
# Install from source
pip install -e /path/to/LeanUp

# Or clone and install
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp
pip install -e .
```

### Basic Usage

```bash
# Show help
leanup --help

# Initialize Lean environment (install elan toolchain manager)
leanup init

# Check status
leanup status

# Proxy elan commands
leanup elan --help
leanup elan toolchain list
leanup elan toolchain install stable
leanup elan default stable
```

## 📖 Detailed Usage Guide

### Initializing Environment

```bash
# Initialize environment with latest version of elan
leanup init

# Force reinitialization
leanup init --force

# Initialize without modifying shell config files
leanup init --no-modify-path
```

### Managing Lean Toolchains

After initializing the environment, you can use `leanup elan` commands to manage Lean toolchains:

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

### Project Management

```bash
# Set specific toolchain for project
cd your-lean-project
leanup elan override set stable

# Remove project toolchain override
leanup elan override unset
```

## 🛠️ Development

### Environment Setup

```bash
# Clone repository
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp

# Install development dependencies
pip install -r requirements_dev.txt

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

### Code Quality Checks

```bash
# Code style check
ruff check .

# Type checking
mypy .
```

## 🌍 Cross-platform Support

LeanUp is tested on the following platforms:

- **Linux**: Ubuntu 20.04+, CentOS 7+, Debian 10+
- **macOS**: macOS 10.15+ (Intel and Apple Silicon)
- **Windows**: Windows 10+

## 📊 Project Status

| Feature | Status | Description |
|---------|--------|-------------|
| elan Installation | ✅ | Supports automatic platform and version detection |
| Command Proxy | ✅ | Transparent passthrough of all elan commands |
| Cross-platform | ✅ | Linux/macOS/Windows |
| Unit Tests | ✅ | Coverage > 85% |
| CI/CD | ✅ | GitHub Actions multi-platform testing |

## 🤝 Contributing

Contributions are welcome! Please see [Contributing Guide](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 🔗 Related Links

- [Lean Official Website](https://leanprover.github.io/)
- [Lean Community Documentation](https://leanprover-community.github.io/)
- [elan Toolchain Manager](https://github.com/leanprover/elan)