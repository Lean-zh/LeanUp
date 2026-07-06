# LeanUp

一个用于管理 Lean 数学证明语言环境的 Python 工具。

## 功能特性

- `leanup init`：初始化 LeanUp home、`.env`、cache、tmp、logs 等基础目录
- `leanup elan`：安装、打包、下载、解包和检查基础 elan runtime
- `leanup lean`：安装、打包、下载、解包和检查 `ELAN_HOME/toolchains` 下的 Lean toolchain
- `leanup mathlib setup`：快速创建固定 Lean 版本项目，支持 mathlib 共享缓存
- `leanup mathlib check <version>`：检查指定 Mathlib 环境是否能 `import Mathlib`
- `leanup mathlib pack <version>`：优先把已验证 workspace 的 `.lake/` 打包为共享缓存归档
- `leanup mathlib unpack <version>`：优先从本地 `.lake` archive 解压回 LeanUp mathlib cache
- `leanup mathlib list/get/create`：查看、下载或创建 mathlib 共享缓存
- `leanup serve`：提供 `.ltar` 兼容路由和 LeanUp 归档下载服务
- `leanup toolchains`：兼容旧入口，管理 `.elan` 基础包和 Lean toolchain 归档
- `leanup repo install`：安装 Lean 仓库，支持命令优先、交互补参
- `leanup repo list`：查看已安装仓库

## 快速开始

查看[快速开始](getting-started/quickstart.md)开始使用 LeanUp。

## 开发说明

- 仓库级开发规范见 `AGENTS.md` 与 `DEVELOP.md`
- 当前以中文主文档为准，不继续维护英文平行版本
- `repo install` 当前遵循：缺必要参数自动进入交互，`-i` 强制交互，`-I` 禁止交互
