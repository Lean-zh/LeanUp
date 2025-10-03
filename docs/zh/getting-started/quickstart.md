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
# 安装 Mathlib
leanup repo install leanprover-community/mathlib4

# 安装特定分支或标签
leanup repo install leanprover-community/mathlib4 -b v4.14.0

# 安装到自定义目录
leanup repo install Lean-zh/leanup -d /path/to/custom/dir

# 控制构建选项
leanup repo install leanprover-community/mathlib4 --lake-build

# 交互式
leanup repo install leanprover-community/mathlib4 -i

# 指定要构建的包
leanup repo install Lean-zh/repl --build-packages "REPL,REPL.Main"

# 列出已安装的仓库
leanup repo list

# 在指定目录中搜索仓库
leanup repo list --search-dir /path/to/repos

# 按名称过滤仓库
leanup repo list -n mathlib
```

## 使用 InstallConfig

`InstallConfig` 类提供了编程方式配置仓库安装：

```python
from pathlib import Path
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

# 检查配置是否有效
if config.is_valid:
    print(f"将安装到: {config.dest_path}")
    
# 执行安装
config.install()

# 更新配置
new_config = config.update(branch="v4.3.0", override=True)
```

## 使用 RepoManager

`RepoManager` 类提供了管理目录和 git 仓库的功能：

```python
from leanup.repo.manager import RepoManager

# 创建仓库管理器
repo = RepoManager("/path/to/your/directory")

# 检查是否为 git 仓库
if repo.is_gitrepo:
    print("这是一个 git 仓库")
    status = repo.git_status()
    print(f"当前分支: {status['branch']}")
    print(f"是否有修改: {status['is_dirty']}")

# 克隆仓库
success = repo.clone_from(
    "https://github.com/owner/repo.git", 
    branch="main", 
    depth=1
)

# 文件操作
repo.write_file("test.txt", "Hello world")
content = repo.read_file("test.txt")
repo.edit_file("test.txt", "world", "universe", use_regex=False)

# 列出文件和目录
files = repo.list_files("*.lean")
dirs = repo.list_dirs()

# 执行命令
stdout, stderr, returncode = repo.execute_command(["ls", "-la"])
```

## 使用 LeanRepo 管理 Lean 项目

```python
from leanup.repo.manager import LeanRepo

# 创建 Lean 仓库管理器
lean_repo = LeanRepo("/path/to/lean/project")

# 获取项目信息
info = lean_repo.get_project_info()
print(f"Lean 版本: {info['lean_version']}")
print(f"有 lakefile.toml: {info['has_lakefile_toml']}")
print(f"有 lakefile.lean: {info['has_lakefile_lean']}")
print(f"有 lake-manifest.json: {info['has_lake_manifest']}")
print(f"构建目录存在: {info['build_dir_exists']}")

# Lake 操作
lean_repo.lake_init("my_project", "std", "lean")
lean_repo.lake_update()
lean_repo.lake_build("MyTarget")
lean_repo.lake_env_lean("Main.lean", json=True)
lean_repo.lake_clean()
lean_repo.lake_test()

# 使用配置安装
config = InstallConfig(
    suffix="leanprover-community/mathlib4",
    lake_update=True,
    lake_build=False
)
lean_repo.install(config)
```