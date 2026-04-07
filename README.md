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

</div>

## 🎯 功能特性

- **📦 仓库管理**: 安装和管理 Lean 仓库，支持命令优先、交互兜底的配置流程
- **⚡ 项目初始化**: 快速创建固定 Lean 版本的项目，并复用同版本 mathlib 缓存
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

# 快速初始化一个 Lean + mathlib 项目
leanup setup ./Demo --lean-version v4.27.0

# 如需手动透传 elan，也可以继续使用
leanup elan toolchain list
```

## 📖 详细使用指南

### 仓库管理

```bash
# 安装 Mathlib
leanup repo install leanprover-community/mathlib4

# 安装特定分支或标签
leanup repo install leanprover-community/mathlib4 -b v4.14.0

# 安装到自定义目录
leanup repo install Lean-zh/leanup -d /path/to/custom/dir

# 控制构建选项
leanup repo install leanprover-community/mathlib4 --lake-build

# 交互式补参
leanup repo install leanprover-community/mathlib4 -i

# 禁止交互，参数不足时直接报错
leanup repo install -I leanprover-community/mathlib4

# 指定要构建的包
leanup repo install Lean-zh/repl --build-packages "REPL,REPL.Main"

# 列出已安装的仓库
leanup repo list

# 在指定目录中搜索仓库
leanup repo list --search-dir /path/to/repos

# 按名称过滤仓库
leanup repo list -n mathlib
```

### 快速初始化项目

`leanup setup` 用于快速创建一个固定 Lean 版本的项目，并按需要为 `mathlib` 依赖准备共享缓存。

```bash
# 创建一个带 mathlib 的项目，默认有缓存就复用，没有缓存就构建
leanup setup ./Demo --lean-version v4.27.0

# 首次为某个版本准备依赖缓存时，从头构建一次
leanup setup ./DemoBuild --lean-version v4.27.0 --dependency-mode build

# 后续同版本项目可直接软链接复用缓存
leanup setup ./DemoFast --lean-version v4.27.0 --dependency-mode symlink

# 创建不带 mathlib 的纯 Lean 项目
leanup setup ./PlainDemo --lean-version v4.27.0 --no-mathlib

# 指定 Lake 项目名，并覆盖已存在目录
leanup setup ./Demo --lean-version v4.27.0 --name MyDemo --force
```

规则说明：

- `--dependency-mode symlink` 只在启用 `mathlib` 时可用
- 默认缓存目录为 `LEANUP_CACHE_DIR/setup/mathlib/<version>/packages`
- 在当前 workspace 中，默认也会尝试从 `reference/Projects/cache/<version>/packages.tar.gz` 自动导入缓存
- 默认行为是：有缓存就复用，没有缓存就自动构建并刷新缓存
- 显式指定 `--dependency-mode symlink` 时，如果当前版本还没有缓存，会直接报错
- `setup` 会确保对应 Lean toolchain 已通过 `elan` 安装

### 管理 mathlib 缓存

```bash
# 查看 LeanUp 已有缓存，以及 reference 中可导入的缓存
leanup mathlib cache list

# 只看本地已导入缓存
leanup mathlib cache list --local-only

# 只看可从 reference 导入的缓存
leanup mathlib cache list --importable-only

# 导入某个版本的 reference cache 到 LeanUp 默认缓存目录
leanup mathlib cache import v4.22.0

# 一次性导入全部 reference cache
leanup mathlib cache import --all
```

如果需要覆盖 reference cache 来源目录，可以设置环境变量 `LEANUP_MATHLIB_CACHE_SOURCE`，或者在命令里传 `--source-dir`。

### 交互式安装

使用 `leanup repo install -i` 时，您可以配置：

- 仓库名称（必需）
- 仓库源的基础 URL
- 分支或标签
- 存储仓库的目标目录
- 自定义目标名称
- 是否在克隆后运行 `lake update`
- 是否在克隆后运行 `lake build`
- 要编译的特定构建包
- 是否覆盖现有目录

默认规则：

- 命令优先，交互兜底
- 缺必要参数时自动进入交互
- `-i` 强制交互
- `-I` 禁止交互，参数不足时直接报错

### 编程接口

#### 使用 InstallConfig

```python
from leanup.repo.manager import InstallConfig

# 创建安装配置
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

# 执行安装
config.install()
```

#### 使用 RepoManager

```python
from leanup.repo.manager import RepoManager

# 创建仓库管理器
repo = RepoManager("/path/to/directory")

# 克隆仓库
repo.clone_from("https://github.com/owner/repo.git", branch="main")

# 文件操作
repo.write_file("test.txt", "Hello world")
content = repo.read_file("test.txt")
repo.edit_file("test.txt", "world", "universe")

# 列出文件和目录
files = repo.list_files("*.lean")
dirs = repo.list_dirs()
```

#### 使用 LeanRepo

```python
from leanup.repo.manager import LeanRepo

# 创建 Lean 仓库管理器
lean_repo = LeanRepo("/path/to/lean/project")

# 获取项目信息
info = lean_repo.get_project_info()
print(f"Lean 版本: {info['lean_version']}")
print(f"有 lakefile: {info['has_lakefile_toml']}")

# Lake 操作
stdout, stderr, returncode = lean_repo.lake_init("my_project", "std")
stdout, stderr, returncode = lean_repo.lake_update()
stdout, stderr, returncode = lean_repo.lake_build()
stdout, stderr, returncode = lean_repo.lake_env_lean("Main.lean")
```

## 🛠️ 开发

仓库级开发规范见：

- `AGENTS.md`
- `DEVELOP.md`

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

LeanUp 使用位于 `~/.leanup/config.yaml` 的配置文件。您可以自定义：

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
