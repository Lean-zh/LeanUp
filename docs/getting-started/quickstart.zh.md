# 快速开始

## 安装

```bash
# 从 PyPI 安装
pip install leanup

# 或者克隆仓库后安装
git clone https://github.com/Lean-zh/LeanUp.git
cd LeanUp
pip install -e .
```

## 基础使用

### 初始化 elan

```bash
# 查看帮助
leanup --help

# 安装 elan
leanup init

# 查看当前状态
leanup status
```

### 安装 Lean 工具链

```bash
# 安装最新稳定版 Lean 工具链
leanup install

# 安装特定版本的 Lean 工具链
leanup install v4.14.0

# 强制重新安装
leanup install --force
```

### 管理工具链

```bash
# 代理执行 elan 命令
leanup elan --help
leanup elan toolchain list
leanup elan toolchain install stable
leanup elan default stable
```

### 仓库管理

```bash
# 安装仓库（格式：owner/repo）
leanup repo install leanprover-community/mathlib4

# 使用特定选项安装
leanup repo install leanprover-community/mathlib4 --branch main --force

# 安装到指定目录
leanup repo install leanprover-community/mathlib4 --dest-dir ./my-mathlib

# 列出已安装的仓库
leanup repo list

# 使用过滤器列出仓库
leanup repo list --name mathlib

# 交互式安装
leanup repo install -i
```

## 使用 RepoManager

`RepoManager` 类提供了管理目录和 git 仓库的功能：

```python
from leanup.repo import RepoManager

# 创建仓库管理器
repo = RepoManager("/path/to/your/directory")

# 检查是否为 git 仓库
if repo.is_gitrepo:
    print("这是一个 git 仓库")
    status = repo.git_status()
    print(f"当前分支: {status['branch']}")

# 文件操作
repo.write_file("test.txt", "Hello world")
content = repo.read_file("test.txt")
repo.edit_file("test.txt", "world", "universe")

# 列出文件和目录
files = repo.list_files("*.lean")
dirs = repo.list_dirs()
```

## 使用 LeanRepo 管理 Lean 项目

```python
from leanup.repo import LeanRepo

# 创建 Lean 仓库管理器
lean_repo = LeanRepo("/path/to/lean/project")

# 获取项目信息
info = lean_repo.get_project_info()
print(f"Lean 版本: {info['lean_version']}")
print(f"有 lakefile: {info['has_lakefile_toml']}")

# Lake 操作（直接执行命令）
stdout, stderr, returncode = lean_repo.lake(["build"])
stdout, stderr, returncode = lean_repo.lake_update()
stdout, stderr, returncode = lean_repo.lake_build()
```