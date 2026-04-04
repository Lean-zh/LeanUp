# Create Command Design

## Goal

`leanup create` 的目标不是安装一个现成仓库，而是创建一个新的 Lean 项目目录，并把 Lean 版本、mathlib 依赖与初始构建流程组织成一条可复用的 CLI 工作流。

第一阶段的设计基线来自 `/home/zhihong/Playground/Projects/create_project.sh`，但命令语义与交互方式要对齐 `LeanUp` 未来的 CLI 规范。

## Command Shape

建议命令形态：

```bash
leanup create [version]
```

建议首批参数：

```bash
leanup create [version] \
  --project-name lean4web \
  --dest-dir . \
  --dest-name <default-to-version> \
  --force \
  -i \
  -I
```

## Why Top-Level

`create` 应作为顶层命令存在，而不是继续放在 `repo` 下面。

原因有三点：

1. `repo install` 的语义是“获取已有仓库”
2. `create` 的语义是“生成新的项目工作目录”
3. 后续如果支持模板、预设或更高层工作流，顶层命令更容易扩展

## Required Input

### `version`

- 必填
- 接受 `4.x.x` 或 `v4.x.x`
- 进入执行前统一规范化为 `v4.x.x`

## Optional Inputs

### `project_name`

- 默认值：`lean4web`
- 影响 `lake new <project_name> math.lean`
- 影响 package 名与模块名

### `dest_dir`

- 默认值：当前目录 `.`

### `dest_name`

- 默认值：规范化后的 Lean 版本，例如 `v4.14.0`
- 保持与 `create_project.sh` 一致，方便按版本生成多个实验目录

### `force`

- 默认关闭
- 仅在目标目录已存在时使用

## Interaction Rules

### Default

1. 必要参数已齐全时，直接执行
2. 必要参数缺失时，如果允许交互，则补问缺失参数
3. 必要参数缺失且 `-I` 生效时，立即报错

### `-i`

- 强制进入交互模式
- 即使已有参数，也允许逐项确认与覆盖

### `-I`

- 禁止任何交互
- 缺少必要参数时报错
- 目标目录已存在且未传 `--force` 时也直接报错

## Prompt Style

交互方式应是“参数补全”，而不是冗长 wizard。

约束如下：

1. 只询问当前缺失或需要确认的关键参数
2. 已有值展示为默认值
3. 用户回车即可保留默认值
4. 默认值必须与最终执行值一致

## Execution Phases

参考 `create_project.sh`，第一版 `create` 的执行阶段应至少包含：

1. 校验 Lean 版本
2. 处理目标目录
3. 在临时目录运行 `lake new <project_name> math.lean`
4. 写入 `lean-toolchain`
5. 写入 `lakefile.lean`
6. 执行 `lake update`
7. 执行 `lake exe cache get`
8. 执行 `lake build`
9. 成功后移动到目标目录

## Error Semantics

建议统一为以下风格：

- `Error: Lean version is required`
- `Error: Invalid version format. Must be v4.x.x or 4.x.x`
- `Error: Directory <path> already exists. Use --force to replace it.`
- `Error: lake update failed`
- `Error: cache download failed`
- `Error: build failed`

## Implementation Guidance

第一版实现约束：

1. 忠实复用 `create_project.sh` 的核心创建流程
2. CLI 层只负责参数解析、交互补全和输出
3. 创建逻辑下沉到 `LeanRepo` 或相关模块
4. 文档、测试与实现同步推进

## Next Step

下一阶段 `05-create-command-implementation` 按本设计直接落代码，并补齐对应测试。
