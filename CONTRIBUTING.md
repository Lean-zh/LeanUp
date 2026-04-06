# 贡献指南

感谢您对 LeanUp 项目的关注！欢迎各种形式的贡献。

## 🚀 快速开始

### 环境准备

1. Fork 并克隆仓库：
```bash
git clone https://github.com/yourusername/LeanUp.git
cd LeanUp
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -e .
pip install -r requirements_dev.txt
```

## 🧪 测试

运行测试确保一切正常：

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
coverage run -m pytest tests/
coverage report -m

# 代码风格检查
ruff check .

# 类型检查
mypy .
```

## 📝 代码规范

- 使用 Python 3.9+
- 遵循 PEP 8 代码风格
- 添加适当的类型注解
- 为新功能编写测试
- 保持代码覆盖率 > 85%
- 具体开发约束以 `AGENTS.md` 和 `DEVELOP.md` 为准

## 🔄 提交流程

1. 创建功能分支：
```bash
git checkout -b feature/your-feature-name
```

2. 进行更改并提交：
```bash
git add .
git commit -m "描述你的更改 / Describe your changes"
```

3. 推送到你的 fork：
```bash
git push origin feature/your-feature-name
```

4. 创建 Pull Request

## 📋 提交信息格式

```
类型(scope): 简短描述

详细描述（可选）

类型：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式化
- refactor: 代码重构
- test: 测试相关
- chore: 构建/工具相关
```

## 🐛 报告问题

报告 bug 或提出功能请求时，请提供：

- 操作系统和版本
- Python 版本
- LeanUp 版本
- 重现步骤
- 期望行为
- 实际行为

## 💡 功能请求

欢迎新功能建议，请尽量确保：

- 功能与项目目标一致
- 提供清晰的用例
- 考虑向后兼容性

## 📞 联系方式

- 通过 GitHub Issues 讨论
- 邮箱：leanprover@outlook.com

感谢您的贡献！
