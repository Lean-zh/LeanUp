# LeanUp 现阶段已经做成了什么

`LeanUp` 现在还不是一个“大而全”的 Lean 工作流平台，但它已经不只是一个概念原型。更准确地说，它已经具备了一个早期可用 CLI 工具应有的骨架：能安装基础环境、能管理 Lean toolchain、能代理原生 `elan`、能拉取 Lean 仓库，也能把部分 `lake` 操作收口到 Python API 里。

这篇文章的目标不是讲愿景，而是回答一个更具体的问题：`LeanUp` 今天到底已经能做什么。

## 1. 它已经是一个可安装的 CLI 工具

`LeanUp` 通过 `setup.cfg` 暴露 `console_scripts` 入口，安装后可以直接使用 `leanup` 命令。

当前顶层 CLI 已经包含这些命令：

- `leanup init`
- `leanup install`
- `leanup status`
- `leanup elan`
- `leanup repo`

这意味着它不是只给 Python 调用的内部库，而是明确朝命令行工具方向在演进。

## 2. 它已经能管理 elan 和 Lean toolchain

Lean 开发环境里，`elan` 是一个非常核心的基础设施。`LeanUp` 现阶段最成熟的一块，就是围绕 `elan` 和 Lean toolchain 做了一层更统一的封装。

当前已经具备的能力包括：

- 检测本机是否已安装 `elan`
- 在 Linux、macOS、Windows 上安装 `elan`
- 读取 `elan` 版本信息
- 列出已安装的 toolchain
- 安装指定或默认版本的 Lean toolchain
- 直接代理执行任意 `elan` 命令

如果只从“先把 Lean 环境跑起来”这个目标看，`LeanUp` 已经解决了相当大一块重复劳动。

## 3. 它已经能安装和管理 Lean 仓库

除了 Lean 自身版本，实际工作里另一个高频动作是拉仓库、切分支、更新依赖、跑构建。`LeanUp` 现在已经对这部分提供了一个可用的命令层。

例如当前支持：

- `leanup repo install leanprover-community/mathlib4`
- 指定分支或 tag
- 指定目标目录
- 指定目标名
- 覆盖已有目录
- 克隆后执行 `lake update`
- 克隆后执行 `lake build`
- 指定构建包
- 列出缓存目录或指定目录下的仓库

这部分已经不只是“git clone 的别名”，而是开始带有 Lean 场景语义了。

## 4. 它已经有初步交互能力，但还比较浅

`LeanUp` 当前已经支持 `repo install -i` 这种交互式安装。

不过它的交互方式还比较原始，主要是逐项 `prompt` 和 `confirm`：

- 问仓库名
- 问 source
- 问 branch
- 问目标目录
- 问目标名
- 问是否执行 `lake update`
- 问是否执行 `lake build`

它已经证明了一点：`LeanUp` 并不是完全排斥交互式 CLI 的工具。

但同时也说明，它还没有形成统一的 CLI 交互范式。现阶段更像“参数补全式提示”，而不是完成度更高的项目创建体验。

## 5. 它已经有一层可编程 API

如果只把 `LeanUp` 看成 CLI，其实低估了它。它现在已经有了几层可直接在 Python 代码中使用的抽象：

### `InstallConfig`

负责安装配置的组织，包括：

- URL 拼接
- 目标路径推导
- 参数复制与更新

### `RepoManager`

负责通用目录和 Git 相关能力，包括：

- 克隆仓库
- 读写文件
- 编辑文件
- 执行命令
- 列出文件和目录
- 查看 git 状态

### `LeanRepo`

在 `RepoManager` 之上继续封装 Lean/Lake 相关能力，包括：

- 读取 `lean-toolchain`
- 定位 `lake` 可执行文件
- `lake init`
- `lake update`
- `lake build`
- `lake env lean`
- `lake clean`
- `lake test`
- 汇总项目结构信息

从这个角度看，`LeanUp` 已经不是单纯“把一堆 shell 命令封成 click 命令”，而是在逐步形成 Lean 项目管理的程序化接口。

## 6. 它已经具备项目工程化骨架

虽然产品能力还在演进，但工程基础并不空：

- 有中英文 README
- 有快速开始文档
- 有 MkDocs 站点配置
- 有 GitHub Actions CI
- 有 `pytest` 测试

测试覆盖面目前主要包括：

- CLI 命令
- `ElanManager`
- `InstallConfig`
- `RepoManager`
- `LeanRepo`
- 基础工具函数

这说明它已经具备了“持续迭代而不是一次性脚本”的基础条件。

## 7. 现阶段最大的不足，不在基础能力，而在高层工作流

如果把今天的 `LeanUp` 总结成一句话，我会说：

它已经有“环境管理”和“仓库管理”的骨架，但还没有把这些能力组织成更高层、更顺手的用户工作流。

最明显的几个不足是：

### 配置系统还不统一

- README 写的是 `config.toml`
- 代码里实际用的是 `config.yaml`
- CLI 主流程也还没有真正把配置系统接进去

### 交互方式还没有统一范式

- 现在已经有交互，但风格比较散
- 缺少统一的 `-i/-I`、缺参补全、默认值展示规则

### 还没有“创建新项目”这种高层命令

- 现在更偏底层环境工具
- 还没有把“新建一个指定 Lean/mathlib 版本的项目”做成一条顺滑路径

## 8. 下一阶段应该怎么走

`LeanUp` 的下一阶段重点，不应该再是“继续补更多底层命令”，而应该开始把已有能力组织成更高层的工作流。

最自然的一步就是：

- 设计并实现 `leanup create`
- 明确统一的 CLI 交互范式
- 给交互式 CLI 建立更清晰的测试和文档规则

也就是说，接下来的重点不是从零开始，而是把已经存在的能力收拢成一个更像产品的入口。

## 结语

`LeanUp` 现在已经具备一个早期可用 CLI 工具的基本形态：它能装 `elan`、装 Lean toolchain、代理 `elan`、拉 Lean 仓库，并对 `lake` 操作做了一层程序化封装。

它还远没有结束，但也已经过了“什么都没有”的阶段。接下来真正值得投入的，不是重复堆更多零散命令，而是把这些基础能力组织成更顺手、更一致的 Lean 项目工作流。
