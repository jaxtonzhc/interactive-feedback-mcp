# Interactive Feedback MCP - 代码地图

## 项目概述

基于 FastMCP 的交互式反馈 MCP 服务器，为 Cursor/Augment/Claude 等 AI Agent 提供弹窗式用户反馈收集。使用 PySide6 (Qt) 构建 GUI，通过子进程方式启动，支持心跳防超时和防重复弹窗。

## 核心文件

| 文件 | 职责 |
|------|------|
| `server.py` | **MCP 服务器主入口**。注册 `interactive_feedback` 工具，实现心跳防超时、防重复弹窗、子进程管理、项目/Git 探测、结果格式化 |
| `enhanced_feedback_ui.py` | **GUI 子进程入口**。解析 CLI 参数、初始化 QApplication、主题、字体，启动 `ThreeColumnFeedbackUI`，退出后将 `feedback_result` 写入临时 JSON |

## UI 组件层 (`ui/components/`)

| 文件 | 职责 |
|------|------|
| `three_column_layout.py` | **当前主窗口** `ThreeColumnFeedbackUI(QMainWindow)`。三栏布局：左区 Summary(Markdown)、底部 Reply(文字+图片)、右区 Actions(Git+预定义选项) |
| `enhanced_markdown_renderer.py` | `EnhancedTextBrowser` — 基于 python-markdown + Pygments 的 Markdown 渲染器，支持代码高亮、外链打开、锚点跳转 |
| `text_processing.py` | `TextProcessor` — 文本预处理，Markdown 检测与 HTML 转换（旧版窗口使用） |
| `main_window.py` | 旧版单栏 `FeedbackUI` — 当前未被主流程引用，保留兼容 |
| `data_visualization.py` | 数据分析子窗口 — QtCharts 饼图/柱状图，`Ctrl+D` 快捷键打开 |
| `visual_config_manager.py` | 独立可视化设置面板 — 未挂到主流程 |

## UI 控件层 (`ui/widgets/`)

| 文件 | 职责 |
|------|------|
| `feedback_text_edit.py` | `FeedbackTextEdit` — 纯文本编辑器，支持粘贴图片(base64)、IME 候选框、`submit_requested`/`image_pasted` 信号 |

## 样式层 (`ui/styles/`)

| 文件 | 职责 |
|------|------|
| `enhanced_glassmorphism.py` | **当前主主题** — 亮/暗/跟随系统 token，三栏窗口大量使用 |
| `glassmorphism.py` | 经典毛玻璃 QSS — 基于系统调色板的深浅判断 |
| `modern_glassmorphism.py` | 深色渐变风格 QSS — 部分区块引用 |
| `dark_theme.py` | `DarkThemeStyles` — 构造深色 QPalette |
| `enhanced_theme_manager.py` | 多主题管理 `ThemeConfig`/`ThemeType` |

## 工具层 (`ui/utils/`)

| 文件 | 职责 |
|------|------|
| `logging_system.py` | 多文件日志系统 — `server.py` 和 `enhanced_feedback_ui.py` 共用 |
| `config_manager.py` | `ConfigManager` + `ThemeManager` — 读写 `~/.interactive_feedback_mcp/config.json` |
| `performance.py` | `PerformanceMonitor` — 内存/CPU 采样、提交耗时统计 |
| `responsive.py` | `ScreenSizeManager` — 按屏幕档位建议窗口与比例 |
| `animations.py` | QPropertyAnimation 封装（未在主流程中强依赖） |
| `advanced_interactions.py` | 手势/智能快捷键增强框架（未在主流程中强依赖） |

## 资源层 (`ui/resources/`)

| 文件 | 职责 |
|------|------|
| `icon_manager.py` | 从 `icons/` 加载多尺寸 QIcon/QPixmap |
| `icon_generator.py` | 程序化绘制图标 |

## 会话分析（可选，与主流程解耦）

| 文件 | 职责 |
|------|------|
| `session_metrics_collector.py` | 会话指标数据结构与事件记录 |
| `session_integration.py` | 集成 Tracker，`server.py` 主路径未使用 |
| `session_analysis_tool.py` | 会话分析 CLI — 报表、对比 |
| `manage_logs.py` | 日志运维 CLI — 摘要、清理、搜索 |

## 数据流

```
Agent 调用 → interactive_feedback() → 参数归一化
  → 检查 _active_process（有活跃进程则复用，无则启动新子进程）
  → 等待 _WAIT_SECONDS（默认10min）
    → 用户回复 → 读取临时 JSON → _format_feedback_result() → 返回 Agent
    → 超时 → 返回心跳消息 → Agent 重新调用 → 复用现有进程继续等待
    → 被取消 → 保留 UI 进程 → 下次调用复用
```

## 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_FEEDBACK_WAIT_SECONDS` | `600` | 心跳间隔（秒），超过后返回心跳消息 |
| `MCP_FEEDBACK_CALLER_SOURCE` | `cursor` | 调用来源标识 |
| `MCP_FEEDBACK_UI_TIMEOUT_SECONDS` | 无限 | 旧版 UI 超时（仅旧版函数使用） |
| `MCP_FEEDBACK_DEBUG` | - | 启用调试模式 |
| `MCP_FEEDBACK_LOG_LEVEL` | `INFO` | 日志级别 |

## 模块依赖关系

```
server.py
  ├── fastmcp, pydantic
  ├── ui.utils.logging_system
  └── (subprocess) → enhanced_feedback_ui.py
                        ├── ui.components.three_column_layout.ThreeColumnFeedbackUI
                        │     ├── ui.widgets.feedback_text_edit.FeedbackTextEdit
                        │     ├── ui.components.enhanced_markdown_renderer.EnhancedTextBrowser
                        │     ├── ui.components.text_processing.TextProcessor
                        │     ├── ui.components.data_visualization (可选)
                        │     ├── ui.styles.enhanced_glassmorphism (主主题)
                        │     ├── ui.styles.glassmorphism
                        │     ├── ui.styles.modern_glassmorphism
                        │     ├── ui.utils.config_manager
                        │     ├── ui.utils.performance
                        │     ├── ui.utils.responsive
                        │     └── ui.resources.icon_manager
                        └── ui.utils.logging_system
```
