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
# 创建一个带 mathlib 的 Lean 项目，默认有缓存就复用，没有缓存就自动准备缓存
leanup setup ./Demo --lean-version v4.27.0

# 使用 copy 模式，把共享缓存复制到项目里
leanup setup ./DemoCopy --lean-version v4.27.0 --dependency-mode copy

# 后续项目直接复用共享依赖缓存
leanup setup ./DemoFast --lean-version v4.27.0 --dependency-mode symlink

# 创建不依赖 mathlib 的纯 Lean 项目
leanup setup ./PlainDemo --lean-version v4.27.0 --no-mathlib
```

说明：

- 共享缓存默认放在 `LEANUP_CACHE_DIR/mathlib/packages/<version>/packages`
- 归档缓存默认放在 `LEANUP_CACHE_DIR/mathlib/archives/<version>/packages.tar.gz`
- Linux 默认通常对应 `~/.cache/leanup/mathlib/packages/<version>/packages`
- `--dependency-mode` 支持 `symlink` 和 `copy`
- 如果已有 `packages` 缓存，则按 `symlink` 或 `copy` 的方式放进项目
- 如果缓存不存在，则会自动执行 `lake update`、`lake exe cache get`，再把 `.lake/packages` 写回缓存
- `setup` 会自动确保 `elan` 和目标 Lean toolchain 已安装

### 管理 mathlib 缓存

```bash
# 查看 LeanUp 已有缓存版本
leanup cache list

# 查看远端服务已有缓存版本和下载 URL
leanup cache list --base-url http://127.0.0.1:8000

# 在 tempfile 临时工作目录中创建某个 Lean 版本的共享 mathlib packages 缓存
leanup cache create v4.22.0

# 将本地缓存里的 packages/<version>/packages 打包成 archives/<version>/packages.tar.gz
leanup cache pack v4.22.0

# 或者使用指定缓存根
leanup cache pack v4.22.0 --output-dir /path/to/cache

# 启动缓存服务：/f/... 给 lake exe cache get，/packages/... 给 leanup cache get
leanup cache serve

# 让 mathlib 官方 cache client 改走 LeanUp 服务
export MATHLIB_CACHE_GET_URL=http://127.0.0.1:8000
lake exe cache get

# 从 LeanUp cache 服务下载 packages.tar.gz，并解压到本地缓存根
leanup cache get v4.22.0 --base-url http://127.0.0.1:8000

# 如需关闭并发压缩，可以显式禁用 pigz
leanup cache pack v4.22.0 --output-dir /path/to/cache --no-pigz
```

- 默认会在本机存在 `pigz` 时启用并发压缩
- 如果系统里没有 `pigz`，命令会自动回退到普通 gzip 打包
- `--no-pigz` 可显式关闭并发压缩
- `leanup cache create` 会在临时目录中执行 `lake update` 和 `lake exe cache get`，再把 `.lake/packages` 回填到 `mathlib/packages/<version>/packages` 并生成 `mathlib/archives/<version>/packages.tar.gz`
- `leanup cache serve` 的 `.ltar` 路由只做 mathlib 兼容分发；`packages.tar.gz` 是 LeanUp 自定义缓存格式
- `leanup cache serve` 使用 FastAPI/uvicorn，并提供 `/packages/mathlib/index.json` 供其他机器列出远端可用版本
- `leanup cache pack` 从 `mathlib/packages/<version>/packages` 生成 `mathlib/archives/<version>/packages.tar.gz`
- `leanup cache get` 从远端下载 `packages.tar.gz` 到 `mathlib/archives/<version>/packages.tar.gz`，并解压到 `mathlib/packages/<version>/packages`
- `leanup cache pack` 和 `leanup cache get` 都先写临时文件 / 临时目录，成功后再原子替换正式路径，避免中断损坏缓存

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
