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

- **📦 仓库管理**: 安装和管理 Lean 仓库，支持交互式配置
- **🌍 跨平台支持**: 支持 Linux、macOS 和 Windows
- **📦 简单易用**: 通过 `pip install leanup` 快速安装
- **🔄 命令代理**: 透明代理所有 elan 命令，无缝体验

## 🚀 快速开始

### 安装

```bash
# 从 PyPI 安装
pip install leanup 

# 或者克隆仓库后安装
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp
pip install -e .
```

### 基础使用

```bash
# 查看帮助
leanup --help

# 安装 elan 并初始化配置
leanup init

# 安装 
leanup install # stable

# 查看状态
leanup status

# 代理执行 elan 命令
leanup elan --help
leanup elan toolchain list
leanup elan toolchain install stable
leanup elan default stable
```

## 📖 详细使用指南

### 管理 Lean 工具链

安装 elan 后，您可以使用 `leanup elan` 命令来管理 Lean 工具链：

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

### 仓库管理

```bash
# 从默认源安装仓库
leanup repo install mathlib4

# 使用交互式配置安装
leanup repo install mathlib4 --interactive

# 从指定源安装
leanup repo install mathlib4 --source github

# 从完整 URL 安装
leanup repo install --url https://github.com/leanprover-community/mathlib4.git

# 安装特定分支或标签
leanup repo install mathlib4 --branch v4.3.0

# 强制替换现有目录
leanup repo install mathlib4 --force

# 安装到自定义目录
leanup repo install mathlib4 --dest-dir /path/to/custom/dir

# 列出已安装的仓库
leanup repo list
```

### 交互式安装

使用 `leanup repo install` 的 `--interactive` 标志时，您可以配置：

- 仓库前缀（如 `leanprover-community/`）
- 仓库源的基础 URL
- 存储仓库的缓存目录
- 是否在克隆后运行 `lake update`
- 是否在克隆后运行 `lake build`
- 要编译的特定构建包


## 🛠️ 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp

# 安装开发依赖
pip install -e ".[dev]"

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

## ⚙️ 配置

LeanUp 使用位于 `~/.leanup/config.toml` 的配置文件。您可以自定义：

- 默认仓库源
- 仓库缓存目录
- elan 自动安装设置
- 仓库前缀和基础 URL

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
| 仓库管理 | ✅ | 安装和管理 Lean 仓库 |
| 交互式配置 | ✅ | 用户友好的设置过程 |
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