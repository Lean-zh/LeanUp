---
name: leanup-environment-pack-serve-restore
description: Pack a Lean/Mathlib environment on one machine, serve the Lean assets from cache/serve, and restore them on another machine without public-network access for Lean-related actions.
version: 0.1.0
updated: 2026-07-07
---

# LeanUp 环境打包、Serve 与恢复

用于一台 provider 机器已经有可用 Lean/Mathlib 环境，需要把同一版本提供给另一台 consumer 机器恢复的场景。

这个 skill 的边界是 Lean 环境资产，不是 Python 工具安装：

- LeanUp 自身是普通 Python CLI，作为前置条件安装或升级，可以使用常规 Python/package 网络环境。
- 从 `leanup init --server ...` 之后的 Lean 相关动作应能只依赖 provider 的 `cache/serve`，不访问 GitHub、Elan 官方源、Mathlib 远端仓库或其它公网 Lean 资源。

## 默认目录契约

默认不要另起奇怪的 serve 目录。LeanUp 的默认路径必须和 `init`、`get`、`unpack`、`install`、`setup` 的客户端行为保持一致：

```text
$HOME/.leanup/cache/serve/      # leanup serve 的默认源目录
$HOME/.leanup/cache/local/      # consumer 本地可复用 cache
$HOME/.leanup/cache/downloads/  # 下载/校验 staging
```

`cache/serve` 的 HTTP 布局固定为：

```text
/elan/base/elan-base.tar.gz
/lean/<version>/toolchain.tar.gz
/mathlib/<version>/mathlib-lake.tar.gz
```

不要把这些内容放进 `cache/serve`：

```text
scripts/
project-files/
Python wheel/package artifacts
*-pack-source/
```

如果确实需要非默认目录，优先显式设置 `LEANUP_HOME` 或 `LEANUP_CACHE_DIR`，让 provider 和 consumer 都从同一套 LeanUp cache 规则推导路径；调试和标准流程应优先使用默认 `~/.leanup/cache/serve`。

## 随附脚本

脚本位于本目录的 `scripts/` 下：

```text
provider-pack-version.sh     # provider: 打包 Elan、Lean toolchain、Mathlib .lake
provider-serve-assets.sh     # provider: 从 ~/.leanup/cache/serve 启动静态文件服务
provider-verify-assets.sh    # provider: 校验本地文件和 HTTP 可访问性
consumer-restore-version.sh  # consumer: 使用已安装 LeanUp 从 provider 恢复 Lean 环境
consumer-verify-version.sh   # consumer: 校验恢复结果
```

## Provider: 打包资产

前置条件：

- provider 已安装 LeanUp。
- provider 的 `ELAN_HOME` 中已有目标 Lean 版本。
- provider 能准备一个可用的 Mathlib workspace。
- 大归档建议安装 `pigz`。

示例：

```bash
export VERSION=v4.30.0
export LEANUP=leanup
export ELAN_HOME=$HOME/.elan
export PROJECT_ROOT=$HOME/leanup-provider-projects
# Optional when using a non-default LeanUp home/cache:
# export LEANUP_HOME=$HOME/.leanup
# export LEANUP_CACHE_DIR=$LEANUP_HOME/cache

./scripts/provider-pack-version.sh "$VERSION"
```

脚本会在默认位置生成：

```text
~/.leanup/cache/serve/elan/base/elan-base.tar.gz
~/.leanup/cache/serve/lean/v4.30.0/toolchain.tar.gz
~/.leanup/cache/serve/mathlib/v4.30.0/mathlib-lake.tar.gz
```

Mathlib portable archive 必须来自 copy-mode 的 `.lake` source。不要把绝对 symlink workspace 直接打包，也不要把 `*-pack-source` 常驻留在项目目录里。脚本会使用临时 copy-mode workspace，完成后自动清理。

## Provider: 启动 serve

默认 serve root 是 `~/.leanup/cache/serve`：

```bash
export HOST=0.0.0.0
export PORT=8765
./scripts/provider-serve-assets.sh
```

如果机器 IP 是 `PROVIDER_HOST`，consumer 使用：

```text
http://PROVIDER_HOST:8765
```

校验 provider：

```bash
export SERVER=http://127.0.0.1:8765
./scripts/provider-verify-assets.sh v4.30.0
```

## Consumer: 恢复 Lean 环境

前置条件：consumer 已安装 LeanUp。

```bash
export VERSION=v4.30.0
export SERVER=http://PROVIDER_HOST:8765
export LEANUP=leanup
export ELAN_HOME=$HOME/.elan
# Optional when using a non-default LeanUp home/cache:
# export LEANUP_HOME=$HOME/.leanup
# export LEANUP_CACHE_DIR=$LEANUP_HOME/cache

./scripts/consumer-restore-version.sh "$VERSION"
```

脚本会：

1. 检查 LeanUp 已存在。
2. 设置 provider host 到 `no_proxy`。
3. 把公共代理指向不可用地址，证明 Lean 相关动作不需要公网。
4. 从 provider 获取 Elan base 和 Lean toolchain。
5. 从 provider 获取 Mathlib `.lake` archive。
6. 执行 `mathlib unpack/setup/check`。

期望输出包含：

```text
elan <version>
Lean (version 4.30.0, ...)
import Mathlib ok
lean-related offline restore ok for <version> via <server>
```

## 校验边界

为了确认没有使用公网 Lean 资源，consumer 恢复时可设置：

```bash
export no_proxy="PROVIDER_HOST,127.0.0.1,localhost,${no_proxy:-}"
export NO_PROXY="$no_proxy"
export http_proxy=http://127.0.0.1:9
export https_proxy=http://127.0.0.1:9
export all_proxy=http://127.0.0.1:9
```

这样 provider 的 `cache/serve` 仍可访问，而任何意外公网访问都会失败。

## 安全规则

- 不要在 skill、脚本或日志里写入 token、password、proxy auth、API key。
- 不要把带认证的 proxy 环境输出打印进日志。
- 不要把机器私有路径作为默认值写死；使用 `$HOME`、`ELAN_HOME`、`SERVER`、`PROJECT_ROOT` 等变量。
- 不要把 LeanUp wheel 放进 `cache/serve` 作为标准资产；LeanUp 自身是普通 Python 前置条件。
- 不要依赖持久 `~/.leanup/tmp`；临时工作区应由命令或脚本自己清理。
- 目录级原子替换的 staging 应和目标目录在同一 filesystem。

## 已验证边界

这套流程已用一个 provider 和一个 consumer 验证过：

- provider 从默认 `~/.leanup/cache/serve` 提供三类 Lean 资产。
- consumer 使用预装 LeanUp。
- consumer 从 `leanup init --server ...` 开始设置死代理，仅 provider host 走 `no_proxy`。
- Elan、Lean toolchain、Mathlib `.lake` 恢复和 `import Mathlib` 校验通过。
