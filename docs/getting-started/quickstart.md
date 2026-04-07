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

### 查看帮助

```bash
leanup --help
```

### 快速创建项目

```bash
# 创建一个带 mathlib 的 Lean 项目，默认有缓存就复用，没有缓存就构建
leanup setup ./Demo --lean-version v4.27.0

# 首次为某个版本准备缓存时，从头构建依赖
leanup setup ./DemoBuild --lean-version v4.27.0 --dependency-mode build

# 后续项目直接复用共享依赖缓存
leanup setup ./DemoFast --lean-version v4.27.0 --dependency-mode symlink

# 创建不依赖 mathlib 的纯 Lean 项目
leanup setup ./PlainDemo --lean-version v4.27.0 --no-mathlib
```

说明：

- 共享缓存默认放在 `LEANUP_CACHE_DIR/setup/mathlib/<version>/packages`
- Linux 默认通常对应 `~/.cache/leanup/setup/mathlib/<version>/packages`
- `symlink` 模式只对 `mathlib` 项目开放
- 默认行为偏向缓存复用：如果已有 `packages` 缓存就直接链接，否则执行 `lake update`、`lake exe cache get`，再把 `.lake/packages` 写回缓存
- `setup` 会自动确保 `elan` 和目标 Lean toolchain 已安装
- 如果你需要直接透传给 `elan`，仍然可以使用 `leanup elan ...`

### 管理 mathlib 缓存

```bash
# 查看 LeanUp 已有缓存版本
leanup mathlib cache list

# 进入当前仓库后，打包本仓库的 .lake/packages 到指定目录
cd /path/to/repo
leanup mathlib cache pack --lean-version v4.22.0 --output-dir /path/to/cache

# 如果本机安装了 pigz，也可以显式启用并发压缩
leanup mathlib cache pack --lean-version v4.22.0 --output-dir /path/to/cache --pigz
```

- `--pigz` 会在本机存在 `pigz` 时启用并发压缩
- 如果系统里没有 `pigz`，命令会自动回退到普通 gzip 打包

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
