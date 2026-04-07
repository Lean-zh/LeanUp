# LeanUp

一个用于管理 Lean 数学证明语言环境的 Python 工具。

## 功能特性

- `leanup setup`：快速创建固定 Lean 版本项目，支持 mathlib 共享缓存
- `leanup mathlib cache ...`：查看和导入 mathlib 共享缓存
- `leanup repo install`：安装 Lean 仓库，支持命令优先、交互补参
- `leanup repo list`：查看已安装仓库

## 快速开始

查看[快速开始](getting-started/quickstart.md)开始使用 LeanUp。

## 开发说明

- 仓库级开发规范见 `AGENTS.md` 与 `DEVELOP.md`
- 当前以中文主文档为准，不继续维护英文平行版本
- `repo install` 当前遵循：缺必要参数自动进入交互，`-i` 强制交互，`-I` 禁止交互
