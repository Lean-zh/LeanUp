# CLI And Development Conventions

本文档收敛 `LeanUp` 当前采用的 CLI、测试和开发约定。它参考了 `ChatTool` 中较成熟的工程实践，但只保留适合 `LeanUp` 当前阶段的部分。

## 1. CLI Conventions

### 1.1 New interactive commands must support `-i` and `-I`

- `-i`: 强制进入交互模式
- `-I`: 禁止交互，缺少必要参数时立即失败

这个约定应优先适用于新命令，例如 `leanup create`，并逐步推广到其他需要交互补全的命令。

### 1.2 Missing required arguments should trigger parameter completion

- 必要参数已经齐全时，直接执行
- 必要参数缺失时，在默认模式下进入交互补全
- 交互目标是补齐参数，不是进入冗长 wizard

### 1.3 Prompt defaults must match actual execution values

- prompt 中展示的默认值必须与最终真正使用的值一致
- 用户按回车保留默认值时，不允许出现“显示一个值、实际执行另一个值”的情况

### 1.4 CLI layer should stay thin

- `leanup/cli/` 负责参数解析、交互补全、阶段输出和错误呈现
- 业务逻辑应下沉到对应模块，例如 `leanup.repo.manager`

### 1.5 Stage output should be explicit

涉及多阶段执行的命令，应输出关键阶段信息，至少让用户知道当前在哪一步失败。

适合输出阶段日志的典型场景：

- 环境初始化
- 项目创建
- 仓库安装
- 依赖更新和构建

## 2. Testing Conventions

### 2.1 Use doc-first for new interactive CLI work

交互式 CLI 的新能力，优先先写测试设计文档，再补测试实现。

推荐结构：

- 初始环境准备
- 预期过程和结果
- 关键断言点
- 边界与失败分支

### 2.2 Distinguish orchestration tests from real-chain tests

`LeanUp` 当前不强制完全复制 `ChatTool` 的目录结构，但测试思路上要区分：

- CLI 编排测试：关注参数、prompt、输出、错误语义
- 真实链路测试：关注真实 `lake`、真实环境、真实依赖是否跑通

### 2.3 Priority assertions for interactive CLI

交互式 CLI 应优先覆盖这些断言：

- 缺参时是否触发交互
- `-I` 时是否按预期失败
- 默认值是否正确
- 参数规范化是否正确
- 目录冲突与覆盖逻辑是否正确
- 关键阶段输出是否存在

## 3. Development Conventions

### 3.1 Code, docs, and tests move together

每个阶段都必须同时补：

- 代码
- 文档
- 测试

不允许只改代码不补文档，或只写设计不补测试边界。

### 3.2 Each stage ends with a commit

当前 `LeanUp` 重构阶段采用阶段化推进方式：

- 每个阶段结束时更新对应报告
- 同步更新任务集级进度
- 为该阶段单独创建一次 commit
- 然后自动进入下一个阶段

### 3.3 Temporary exploration should not pollute the repository

- 草稿、实验和中间材料优先放到外层 workspace 的 `reports/`、`playgrounds/`、`knowledge/`
- `LeanUp` 仓库内只保留真正需要长期维护的实现、测试和文档

### 3.4 CLI behavior changes must update docs

新增命令、交互变化、错误语义变化时，至少同步更新：

- `README.md`
- `docs/`
- 对应测试或测试设计文档

## 4. Current Priority

当前这些约定首先服务于 `leanup create` 的落地，后续再逐步推广到其他 CLI 命令。
