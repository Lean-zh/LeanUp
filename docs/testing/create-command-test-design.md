# Create Command Test Design

## Goal

为 `leanup create` 建立一份 doc-first 测试设计，确保后续实现时，交互行为、非交互行为和目录处理规则都有稳定的验证边界。

## Scope

- 聚焦 CLI 编排层
- 不验证真实 `lake`/网络链路
- 重点验证参数、交互、错误语义与阶段输出

## Cases

### Case 1: explicit version should execute directly

#### Initial State

- 提供 `version`
- 不传 `-i`
- 目标目录不存在

#### Expected Result

- 不触发 prompt
- 版本规范化为 `v4.x.x`
- 直接进入创建执行链路

### Case 2: missing version should prompt in default mode

#### Initial State

- 不提供 `version`
- 未传 `-I`

#### Expected Result

- 触发版本输入 prompt
- 输入值被规范化
- 继续执行创建链路

### Case 3: missing version should fail under `-I`

#### Initial State

- 不提供 `version`
- 显式传 `-I`

#### Expected Result

- 不触发 prompt
- 直接输出 `Error: Lean version is required`

### Case 4: existing directory should require `--force` under `-I`

#### Initial State

- 目标目录已存在
- 传 `-I`
- 未传 `--force`

#### Expected Result

- 不触发确认
- 直接失败
- 输出提示使用 `--force`

### Case 5: interactive mode should allow confirming target details

#### Initial State

- 传 `-i`
- 已提供部分参数

#### Expected Result

- 按顺序询问缺失值或允许确认已有值
- prompt 默认值与最终实际执行值一致

### Case 6: output should include key execution stages

#### Initial State

- 正常执行创建流程

#### Expected Result

- 输出包含关键阶段信息，如版本校验、目标目录处理、`lake new`、`lake update`、`lake build`

## Notes

- 真实 `lake`、cache 下载和构建链路可在后续更高层测试中补充
- 当前这份文档主要服务 `05-create-command-implementation`
