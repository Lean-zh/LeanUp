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

**一个用于管理 Lean 数学证明语言环境的 Python 工具**

[English](README-en.md) | [简体中文](README.md)

</div>

## 🎯 功能特性

- **🔧 elan 管理**: 一键安装和管理 Lean 工具链管理器 elan
- **🌍 跨平台支持**: 支持 Linux、macOS 和 Windows
- **📦 简单易用**: 通过 `pip install -e /path/to/LeanUp` 快速安装
- **🔄 命令代理**: 透明代理所有 elan 命令，无缝体验
- **📊 状态监控**: 实时查看 Lean 环境状态和已安装工具链

## 🚀 快速开始

### 安装

```bash
# 从源码安装
pip install -e /path/to/LeanUp

# 或者克隆仓库后安装
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp
pip install -e .
```

### 基础使用

```bash
# 查看帮助
leanup --help

# 初始化 Lean 环境（安装 elan 工具链管理器）
leanup init

# 查看状态
leanup status

# 代理执行 elan 命令
leanup elan --help
leanup elan toolchain list
leanup elan toolchain install stable
leanup elan default stable
```

## 📖 详细使用指南

### 初始化环境

```bash
# 初始化环境并安装最新版本的 elan
leanup init

# 强制重新初始化
leanup init --force

# 初始化但不修改 shell 配置文件
leanup init --no-modify-path
```

### 管理 Lean 工具链

初始化环境后，您可以使用 `leanup elan` 命令来管理 Lean 工具链：

```bash
# 列出所有可用的工具链
leanup elan toolchain list

# 安装稳定版工具链
leanup elan toolchain install stable

# 安装夜间构建版本
leanup elan toolchain install leanprover/lean4:nightly

# 设置默认工具链
leanup elan default stable

# 更新所有工具链
leanup elan update

# 查看当前活动的工具链
leanup elan show
```

### 项目管理

```bash
# 为项目设置特定的工具链
cd your-lean-project
leanup elan override set stable

# 移除项目的工具链覆盖
leanup elan override unset
```

## 🛠️ 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp

# 安装开发依赖
pip install -r requirements_dev.txt

# 安装项目（可编辑模式）
pip install -e .
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
coverage run -m pytest tests/
coverage report -m
```

### 代码质量检查

```bash
# 代码风格检查
ruff check .

# 类型检查
mypy .
```

## 🌍 跨平台支持

LeanUp 在以下平台上经过测试：

- **Linux**: Ubuntu 20.04+, CentOS 7+, Debian 10+
- **macOS**: macOS 10.15+（Intel 和 Apple Silicon）
- **Windows**: Windows 10+

## 📊 项目状态

| 功能 | 状态 | 说明 |
|------|------|------|
| elan 安装 | ✅ | 支持自动检测平台和版本 |
| 命令代理 | ✅ | 透明传递所有 elan 命令 |
| 跨平台支持 | ✅ | Linux/macOS/Windows |
| 单元测试 | ✅ | 覆盖率 > 85% |
| CI/CD | ✅ | GitHub Actions 多平台测试 |

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详细信息。

## 📝 许可证

本项目采用 MIT 许可证。详细信息请查看 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [Lean 官方网站](https://leanprover.github.io/)
- [Lean 社区文档](https://leanprover-community.github.io/)
- [elan 工具链管理器](https://github.com/leanprover/elan)