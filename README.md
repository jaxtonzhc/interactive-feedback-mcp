# Interactive Feedback MCP

**让 AI Agent 在执行任务时暂停并弹窗询问你，而不是猜测着往下做。**

工具调用不消耗 API 额度，你可以在单次请求内与 AI 多轮交互，直到满意为止。

## 快速安装

### 前置条件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 包管理器

```bash
# 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 一步到位

```bash
git clone https://github.com/jaxtonzhc/interactive-feedback-mcp.git ~/.interactive-feedback-mcp
cd ~/.interactive-feedback-mcp && uv sync
```

## 配置

### 1. MCP 配置

在 `~/.cursor/mcp.json`（全局）或项目的 `.cursor/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/.interactive-feedback-mcp",
        "run",
        "server.py"
      ],
      "timeout": 600,
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

> 把 `/absolute/path/to/.interactive-feedback-mcp` 替换为你实际的安装路径。

### 2. AI Rule 配置

在 Cursor Settings > Rules for AI 中添加以下规则：

```
完成任务后，必须调用 interactive_feedback 工具向用户确认结果并询问后续需求。
禁止在未调用 interactive_feedback 的情况下结束回复。
调用时提供 predefined_options 预定义选项供用户快速选择。
仅当用户明确选择"结束"选项时才可停止调用。
```

## 粘贴给 Agent 一键安装

把下面这段话直接发给你的 AI Agent，它会帮你完成所有配置：

> 帮我安装 interactive-feedback-mcp。步骤：
> 1. 执行 `git clone https://github.com/jaxtonzhc/interactive-feedback-mcp.git ~/.interactive-feedback-mcp && cd ~/.interactive-feedback-mcp && uv sync`
> 2. 在 `~/.cursor/mcp.json` 中添加配置（command 为 uv，args 为 `["--directory", "~/.interactive-feedback-mcp 的绝对路径", "run", "server.py"]`，timeout 600，autoApprove `["interactive_feedback"]`）
> 3. 在 Cursor Settings > Rules for AI 中添加规则：完成任务后必须调用 interactive_feedback 向用户确认并询问后续需求，提供预定义选项，仅用户选择结束时才停止调用。

## 工作原理

```
你发出任务 → Agent 执行 → 弹窗等待反馈 → 你追加指令 → Agent 继续 → ... → 输入 Done 结束
```

Agent 调用 `interactive_feedback` 工具 → `server.py` 启动 PySide6 GUI 子进程 → 弹出交互窗口 → 用户输入反馈 → 写入临时 JSON → 返回给 Agent 继续执行。

内置心跳机制防止 Cursor 超时断连，防重复弹窗逻辑避免多个窗口同时弹出。

## 项目结构

```
server.py                  # MCP 服务器入口（FastMCP + 心跳 + 防重复弹窗）
enhanced_feedback_ui.py    # GUI 入口（PySide6 三栏布局窗口）
pyproject.toml             # 依赖：fastmcp, pyside6, psutil, markdown, pygments
ui/
├── components/            # 三栏布局、Markdown 渲染、数据可视化
├── styles/                # 毛玻璃主题、增强主题
├── utils/                 # 日志、性能监控、配置管理、响应式
├── widgets/               # 自定义文本编辑框（支持图片粘贴）
└── resources/             # 图标管理
```

## 许可证

[MIT License](LICENSE)
