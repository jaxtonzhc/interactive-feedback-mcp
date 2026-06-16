# 🗣️ Interactive Feedback MCP - 专业版

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.8.2+-green.svg)](https://pypi.org/project/PySide6/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.5.1+-orange.svg)](https://pypi.org/project/fastmcp/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)

**专为AI辅助开发设计的智能交互反馈系统**

Interactive Feedback MCP 是一个高性能的 MCP Server，专为 **Cursor**、**Claude Desktop** 和 **Windsurf** 等AI开发工具设计。采用现代化三栏布局和毛玻璃效果UI，支持实时交互反馈、多媒体处理和智能项目分析。

## ✨ 核心特性

### 🎯 智能交互系统
- **🔄 实时双向对话** - AI助手可暂停并请求用户澄清，避免猜测性开发
- **🎯 预定义选项** - 快速选择常用操作，提升开发效率
- **📊 智能分析** - 自动分析用户意图、紧急程度和项目上下文
- **⚡ 性能优化** - 启动时间<2秒，UI响应<100ms，内存占用<100MB

### 🎨 现代化UI界面
- **🖼️ 三栏布局** - 消息内容(40%) + 智能推荐(40%) + 项目信息(20%)
- **✨ 毛玻璃效果** - 深色主题，强制模式，不受系统主题影响
- **🌏 中文优化** - 完美支持中文字体和UTF-8编码
- **📱 响应式设计** - 适配不同屏幕尺寸和DPI设置

### 🔧 技术架构
- **🏗️ MCP协议** - 基于FastMCP框架的标准化工具调用
- **🎯 PySide6 UI** - 现代化Qt界面框架
- **⚡ 性能监控** - 内置性能跟踪和优化系统
- **⚙️ 配置管理** - 统一配置系统，支持主题切换和个性化设置

## 💡 解决的问题

### AI开发工具的痛点
在 **Cursor** 等环境中：
- 每次提示消耗API额度，成本高昂
- 基于猜测的开发导致错误代码
- 单向交互，无法及时澄清需求
- 迭代效率低，调试时间长

### 我们的解决方案
**Interactive Feedback MCP** 通过**工具调用暂停机制**：
- 🔄 AI可在单次请求内多轮交互
- 💰 工具调用不计入API使用量
- ✅ 确认后再执行，减少错误
- 🚀 效率提升5倍以上

## 🚀 快速开始

### 系统要求
- **Python**: 3.10+
- **系统**: Windows 10+, macOS 12+, Ubuntu 20.04+
- **内存**: 建议4GB+
- **存储**: 500MB可用空间

### 安装步骤

#### 1. 安装 uv 包管理器
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或者使用 pip
pip install uv
```

#### 2. 克隆项目
```bash
git clone https://github.com/jaxtonzhc/interactive-feedback-mcp.git
cd interactive-feedback-mcp
```

#### 3. 验证安装
```bash
# 测试MCP服务器
uv run server.py

# 测试UI界面
uv run enhanced_feedback_ui.py --prompt "测试消息" --output-file test.json
```

## ⚙️ 配置指南

### MCP客户端配置

#### Cursor 配置
在项目根目录或全局配置中创建 `mcp.json`：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uv",
      "args": [
        "--directory", 
        "/absolute/path/to/interactive-feedback-mcp", 
        "run", 
        "server.py"
      ],
      "timeout": 600,
      "autoApprove": ["interactive_feedback"]
    }
  }
}
```

#### Claude Desktop 配置
编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uv",
      "args": [
        "--directory", 
        "/absolute/path/to/interactive-feedback-mcp", 
        "run", 
        "server.py"
      ],
      "timeout": 600
    }
  }
}
```

**⚠️ 重要提醒**：
- 使用绝对路径确保正确找到项目
- Windows用户请使用正斜杠 `/` 或双反斜杠 `\\`
- 配置后需要重启AI客户端

### AI助手规则配置

在 **Cursor Settings > Rules for AI** 中添加：

```markdown
# Interactive Feedback MCP 使用规则

## 强制交互协议
- 收到用户消息后，必须先调用 `interactive_feedback` 工具进行智能分析
- 提供预定义选项供用户快速选择
- 执行操作前必须获得用户确认
- 完成任务后询问是否需要进一步操作

## 使用场景
- 需求不明确时：询问澄清
- 有多种实现方案时：提供选项
- 重要操作前：请求确认
- 任务完成后：询问后续需求

## 格式示例
```
请使用 interactive_feedback 工具询问用户具体需求
```
```

### 性能配置

创建 `~/.interactive_feedback_mcp/config.json`：

```json
{
  "ui": {
    "theme": "enhanced_glassmorphism",
    "language": "zh_CN",
    "font_family": "PingFang SC",
    "font_size": 14,
    "window_width": 1400,
    "window_height": 1200,
    "panel_ratios": [40, 40, 20]
  },
  "performance": {
    "max_startup_time": 2.0,
    "max_response_time": 100.0,
    "max_memory_usage": 100.0,
    "enable_monitoring": true
  }
}
```

## 📄 日志系统

### 🔍 日志功能
本项目现已集成完整的日志系统，支持：

- **📊 多级别日志记录** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **🔄 文件轮转和大小控制** (默认10MB轮转，保留5个备份)
- **⚡ 性能监控** (记录操作耗时，识别慢操作)
- **📋 项目上下文记录** (自动记录项目信息和Git状态)
- **🐛 错误详情追踪** (包含堆栈信息和上下文)
- **👁️ 实时日志监控**

### 📁 日志文件位置
```
logs/
├── interactive_feedback_mcp.log    # 主日志文件
├── errors.log                      # 错误日志
├── performance.log                  # 性能日志  
└── project_context.log             # 项目上下文日志
```

### 🛠️ 日志管理工具

使用 `manage_logs.py` 脚本管理日志：

```bash
# 查看日志摘要
python manage_logs.py summary

# 查看最近50行主日志
python manage_logs.py view --type main --lines 50

# 查看错误日志
python manage_logs.py view --type error

# 搜索日志内容
python manage_logs.py search "错误关键词" --type all

# 分析错误统计
python manage_logs.py analyze

# 实时监控日志
python manage_logs.py monitor

# 清理30天前的日志
python manage_logs.py cleanup --days 30

# 导出日志文件
python manage_logs.py export --output logs_backup.zip

# 配置日志级别
python manage_logs.py config --level DEBUG
```

### ⚙️ 日志配置
日志配置文件 `logging_config.json` 允许自定义：
- 📝 日志级别和格式
- 📦 文件大小和轮转设置
- 🖥️ 控制台输出控制
- ⏱️ 性能监控阈值
- 🧹 自动清理策略

### 🚨 排查问题
使用日志系统排查问题：

1. **查看错误日志**
   ```bash
   python manage_logs.py view --type error
   ```

2. **分析性能问题**
   ```bash
   python manage_logs.py view --type performance
   ```

3. **检查项目上下文**
   ```bash
   python manage_logs.py view --type context
   ```

4. **搜索特定错误**
   ```bash
   python manage_logs.py search "UI启动失败" --type all
   ```

## 📖 使用指南

### 基础用法

#### 1. 智能交互反馈
```
请使用 interactive_feedback 询问我想要什么类型的API设计
```

#### 2. 项目分析和建议
```
分析当前项目状态并提供改进建议
```

#### 3. 代码审查和优化
```
请审查这段代码并提供优化建议：[代码内容]
```

### 高级功能

#### 1. 文件引用系统
```
请分析 @server.py 文件的架构设计
```

#### 2. 批量操作
```
请批量处理以下文件的格式化：@ui/components/*.py
```

#### 3. 性能监控
```
检查当前应用的性能指标并提供优化建议
```

### UI界面说明

#### 三栏布局
- **左栏(40%)**：消息内容和用户输入
- **中栏(40%)**：AI智能推荐和选项
- **右栏(20%)**：项目信息和Git状态

#### 快捷键
- `Ctrl+Enter`：提交反馈
- `Escape`：取消操作
- `Ctrl+1-5`：快速选择预定义选项
- `Ctrl+/`：显示帮助信息

## 🛠️ 开发指南

### 项目结构
```
interactive-feedback-mcp/
├── server.py                          # MCP服务器入口
├── enhanced_feedback_ui.py            # UI主程序
├── pyproject.toml                    # 项目配置
├── ui/                               # UI组件模块
│   ├── components/                   # 核心组件
│   │   ├── three_column_layout.py   # 三栏布局
│   │   ├── enhanced_markdown_renderer.py  # 渲染引擎
│   │   └── main_window.py           # 主窗口
│   ├── styles/                      # 样式主题
│   │   └── enhanced_glassmorphism.py # 毛玻璃主题
│   ├── utils/                       # 工具模块
│   │   ├── performance.py           # 性能监控
│   │   └── config_manager.py        # 配置管理
│   └── widgets/                     # 自定义控件
└── tests/                           # 测试文件
```

### 开发环境设置
```bash
# 安装开发依赖
uv sync --dev

# 运行测试
uv run python -m pytest tests/

# 代码格式化
uv run python -m black .

# 类型检查
uv run python -m mypy .
```

### 性能要求
- **启动时间**: < 2秒
- **UI响应**: < 100毫秒
- **内存使用**: < 100MB (空闲状态)
- **CPU占用**: < 5% (空闲状态)

## 🔧 故障排除

### 常见问题

#### 1. 中文显示乱码
```bash
# 检查编码设置
python -c "import locale; print(locale.getpreferredencoding())"

# 强制UTF-8
export PYTHONIOENCODING=utf-8
```

#### 2. UI界面异常
```bash
# 重置配置
rm ~/.interactive_feedback_mcp/config.json

# 重新启动应用
uv run enhanced_feedback_ui.py --prompt "测试" --output-file test.json
```

#### 3. 性能问题
```bash
# 检查性能指标
uv run python -c "
from ui.utils.performance import global_performance_monitor
monitor = global_performance_monitor
monitor.start_monitoring()
print(monitor.get_current_metrics())
"
```

#### 4. MCP连接失败
- 检查路径配置是否正确
- 确认uv命令可用
- 查看客户端日志错误信息
- 验证server.py可正常运行

## 📈 路线图

### 当前版本 (v2.0)
- ✅ 三栏布局UI
- ✅ 毛玻璃主题
- ✅ 性能监控
- ✅ 配置管理

### 下一版本 (v2.1)
- 🔄 视频内容分析
- 🔄 图片OCR识别  
- 🔄 多语言支持
- 🔄 插件系统

### 未来计划 (v3.0)
- 🔮 AI代理集成
- 🔮 云端同步
- 🔮 团队协作
- 🔮 API扩展

## 🤝 贡献指南

### 开发流程
1. Fork 项目
2. 创建功能分支：`git checkout -b feature/new-feature`
3. 编写测试用例
4. 提交PR

### 代码规范
- 使用Black进行代码格式化
- 保持测试覆盖率 > 80%
- 编写清晰的提交消息

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP框架支持
- [PySide6](https://pypi.org/project/PySide6/) - UI框架
- [Cursor](https://cursor.sh/) - AI开发工具
- [Claude](https://claude.ai/) - AI助手
- [interactive-mcp](https://github.com/ttommyth/interactive-mcp) - 项目灵感来源

---

**📞 联系方式**
- 问题反馈：[GitHub Issues](https://github.com/jaxtonzhc/interactive-feedback-mcp/issues)
- 功能建议：[GitHub Discussions](https://github.com/jaxtonzhc/interactive-feedback-mcp/discussions)

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**
