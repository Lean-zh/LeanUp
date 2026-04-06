# LeanUp Agent Notes

## 项目信息

- 主语言：Python
- CLI 入口：`leanup`
- 代码路径：`leanup/`
- 文档：`README.md`、`docs/`

## 目录边界

```text
leanup/
├── cli/      # CLI 入口与编排
├── repo/     # Lean / elan / repo 相关核心逻辑
├── utils/    # 通用工具与配置能力
└── const.py  # 常量定义
```

## 开发规范

### CLI

- 命令优先，交互兜底。
- 缺必要参数时自动进入 interactive；`-i` 强制交互，`-I` 禁止交互。
- interactive 展示的默认值必须和最终实际执行一致。
- 新交互统一收敛到共享 interaction 层，不在命令文件里重复写 `click.prompt` / `click.confirm` 流程。
- CLI 文件只做接入、参数编排和输出组织，不承载主要业务实现。

### 代码结构

- `cli/` 负责入口编排。
- `repo/` 负责 Lean / elan / 仓库相关核心逻辑。
- `utils/` 只放真正通用的工具能力，不把业务逻辑塞进去。
- 相同行为优先复用，不重复实现。

### 文档

- 当前以中文主文档为准，不继续维护英文平行文档。
- 功能变更同步更新 `README.md` 和 `docs/`。

### 测试

- 先保证最小可运行测试覆盖。
- 与 CLI 行为强相关的改动，测试要同步更新。
- 新测试优先保持意图清晰、边界明确，不继续扩散历史风格。
