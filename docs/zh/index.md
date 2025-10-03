# LeanUp

一个用于管理 Lean 数学证明语言环境的 Python 工具。

## 功能特性

- **🔧 elan 管理**: 安装和管理 Lean 工具链管理器 elan
- **📦 仓库管理**: 安装和管理 Lean 仓库，支持高级配置选项
- **🌍 跨平台支持**: 支持 Linux、macOS 和 Windows
- **📦 简单易用**: 通过 `pip install leanup` 快速安装

## 快速开始

查看[快速开始](getting-started/quickstart.md)指南，开始使用 LeanUp。

## 命令行界面

LeanUp 提供了完整的 CLI，包含以下命令：

### 主要命令

- `leanup init` - 初始化 elan 安装
- `leanup install [version]` - 安装 Lean 工具链版本（通过 elan）
- `leanup status` - 显示当前状态和已安装工具链
- `leanup elan <args>` - 代理 elan 命令

### 仓库管理

- `leanup repo install <repository>` - 安装 Lean 仓库，支持灵活配置
- `leanup repo list` - 列出已安装的仓库，支持过滤选项

#### 仓库安装选项

- `--source` - 仓库源 URL（默认：https://github.com）
- `--branch` - 要克隆的分支或标签
- `--force` - 替换现有目录
- `--dest-dir` - 目标目录
- `--dest-name` - 自定义目标名称
- `--interactive` - 交互式配置模式
- `--lake-update` - 克隆后运行 lake update（默认：true）
- `--lake-build` - 克隆后运行 lake build（默认：true）
- `--build-packages` - 要构建的特定包

## 模块

### CLI 模块

`leanup.cli` 模块提供了命令行界面：

- **主 CLI**: elan 管理和状态监控的核心命令
- **仓库 CLI**: 管理 Lean 仓库的命令，支持高级选项

### Utils 模块

`leanup.utils` 模块提供了包的实用函数：

- `execute_command`: 执行 shell 命令，具有适当的错误处理和跨平台支持
- `setup_logger`: 配置日志记录器，支持自定义输出格式和颜色

### Repo 模块

`leanup.repo` 模块提供了仓库管理功能：

- `InstallConfig`: 仓库安装的配置类，支持验证
- `RepoManager`: 目录和 git 操作的基础类
- `LeanRepo`: 专门用于 Lean 项目管理的类，支持 lake 操作
- `ElanManager`: 管理 elan 安装和工具链操作