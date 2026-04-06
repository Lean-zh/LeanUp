# LeanUp

一个用于管理 Lean 数学证明语言环境的 Python 工具。

## 功能特性

- `leanup init`：安装并初始化 elan
- `leanup install [version]`：通过 elan 安装 Lean 工具链
- `leanup status`：查看当前 elan / toolchain 状态
- `leanup elan <args>`：透明代理 elan 命令
- `leanup repo install`：安装 Lean 仓库，支持命令优先、交互补参
- `leanup repo list`：查看已安装仓库

## 快速开始

查看[快速开始](getting-started/quickstart.md)开始使用 LeanUp。

## 开发说明

- 仓库级开发规范见 `AGENTS.md` 与 `DEVELOP.md`
- 当前以中文主文档为准，不继续维护英文平行版本
- `repo install` 当前遵循：缺必要参数自动进入交互，`-i` 强制交互，`-I` 禁止交互
