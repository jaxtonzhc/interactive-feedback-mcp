#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Feedback UI for Interactive Feedback MCP
增强版交互反馈UI - MCP服务器专用入口

根据PRD文档实现的增强版毛玻璃效果三栏布局UI
支持命令行参数和JSON结果输出
"""

import sys
import os
import json
import argparse

# 强制设置UTF-8编码
import locale
import codecs

# 导入日志系统
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.utils.logging_system import init_logging, get_logger, log_project_context, log_performance

# 设置默认编码
if sys.platform.startswith('win'):
    # Windows系统特殊处理
    try:
        # 使用 reconfigure 代替 detach，避免破坏 pytest 等工具的 capture 机制
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        elif hasattr(sys.stdout, 'detach'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())  # type: ignore
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        elif hasattr(sys.stderr, 'detach'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())  # type: ignore
    except (AttributeError, OSError, TypeError):
        # 如果reconfigure/detach不可用或失败，跳过编码设置
        pass

# 设置locale - 跨平台兼容
if sys.platform.startswith('win'):
    # Windows locale 格式
    _locale_candidates = ['zh_CN.UTF-8', 'Chinese (Simplified)_China.UTF-8', 'en_US.UTF-8', 'English_United States.UTF-8']
else:
    # macOS / Linux locale 格式
    _locale_candidates = ['zh_CN.UTF-8', 'en_US.UTF-8']

for _loc in _locale_candidates:
    try:
        locale.setlocale(locale.LC_ALL, _loc)
        break
    except (locale.Error, ValueError):
        continue

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.components.three_column_layout import ThreeColumnFeedbackUI
from ui.styles.enhanced_glassmorphism import EnhancedGlassmorphismTheme

def main():
    """主函数 - 处理命令行参数并运行增强版UI"""
    
    # 初始化日志系统
    init_logging({
        'level': 'INFO',
        'console_enabled': True,
        'console_level': 'WARNING',  # UI只在控制台显示警告和错误
        'performance_enabled': True,
        'project_context_enabled': True
    })
    
    logger = get_logger('enhanced_ui')
    logger.info("增强版反馈UI启动")
    
    with log_performance("enhanced_ui_main", "ui_startup"):
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='Enhanced Interactive Feedback UI')
        parser.add_argument('--prompt', required=True, help='The prompt message to display')
        parser.add_argument('--output-file', required=True, help='Output file for the result')
        parser.add_argument('--predefined-options', default='', help='Predefined options separated by |||')
        parser.add_argument('--task-title', default='', help='Large task title shown at the top of the window')
        parser.add_argument('--theme', choices=['system', 'light', 'dark'], default=os.environ.get('MCP_FEEDBACK_THEME', 'system'), help='Theme mode: follow system, force light, or force dark')
        
        args = parser.parse_args()
        logger.info(f"命令行参数解析完成: prompt长度={len(args.prompt)}")
        
        # 如果没有从server.py传递的环境变量，则自行检测调用方项目
        if not os.environ.get('MCP_CALLER_CWD'):
            logger.info("未检测到MCP服务器传递的调用方信息，直接检测调用方项目")
            try:
                # 导入server.py中的检测函数
                from server import _detect_caller_project_context, _get_caller_git_info
                
                # 检测调用方项目上下文
                caller_context = _detect_caller_project_context()
                caller_git_info = _get_caller_git_info(caller_context['cwd'])
                
                # 设置环境变量，以便UI组件能够正确读取
                os.environ['MCP_CALLER_CWD'] = caller_context['cwd']
                os.environ['MCP_CALLER_PROJECT_NAME'] = caller_context['name']
                os.environ['MCP_CALLER_IS_DETECTED'] = str(caller_context['is_detected'])
                os.environ['MCP_CALLER_GIT_BRANCH'] = caller_git_info['branch']
                os.environ['MCP_CALLER_GIT_MODIFIED_FILES'] = str(caller_git_info['modified_files'])
                os.environ['MCP_CALLER_GIT_LAST_COMMIT'] = caller_git_info['last_commit']
                os.environ['MCP_CALLER_IS_GIT_REPO'] = str(caller_git_info['is_git_repo'])
                
                logger.info(f"已检测到调用方项目: {caller_context['name']} ({caller_context['cwd']})")
                
                # 记录项目上下文
                log_project_context("ui_startup_project_detection", {
                    'project': caller_context,
                    'git': caller_git_info
                })
                
            except Exception as e:
                logger.error(f"调用方项目检测失败: {e}")
                logger.info("将使用当前工作目录作为项目信息")
        else:
            project_name = os.environ.get('MCP_CALLER_PROJECT_NAME')
            logger.info(f"使用MCP服务器传递的调用方信息: {project_name}")
            
            # 记录从服务器传递的项目上下文
            log_project_context("ui_startup_server_context", {
                'project_name': project_name,
                'project_cwd': os.environ.get('MCP_CALLER_CWD'),
                'git_branch': os.environ.get('MCP_CALLER_GIT_BRANCH'),
                'priority': os.environ.get('MCP_FEEDBACK_PRIORITY'),
                'category': os.environ.get('MCP_FEEDBACK_CATEGORY')
            })
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    # 强制设置Qt应用程序编码（PySide6中QTextCodec已弃用）
    try:
        # PySide6中不再需要QTextCodec，默认就是UTF-8
        pass
    except:
        pass
    
    # 先设置临时应用程序名称，稍后会更新
    app.setApplicationName("Interactive Feedback MCP")
    app.setApplicationVersion("2.0.0")
    
    # 设置应用程序图标（用于Dock显示）
    from PySide6.QtGui import QIcon
    icon_path = os.path.join(os.path.dirname(__file__), "ui", "resources", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"✅ 应用程序图标已设置: {icon_path}")
    else:
        print(f"⚠️ 应用程序图标文件不存在: {icon_path}")
    
    # 设置应用程序属性
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # type: ignore
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # type: ignore

    # 跟随系统或按参数切换主题，不再强制深色
    try:
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
        os.environ['QT_SCALE_FACTOR'] = '1'
    except Exception as e:
        print(f"⚠️ 设置缩放参数失败: {e}")

    os.environ['MCP_FEEDBACK_THEME'] = args.theme
    resolved_theme = EnhancedGlassmorphismTheme.set_theme_mode(args.theme)
    print(f"🎨 当前UI主题模式: {resolved_theme} (requested={args.theme})")
    
    # 设置中文字体支持
    from PySide6.QtGui import QFont
    default_font = QFont()
    chinese_fonts = ['PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', 'STHeiti']
    for font_name in chinese_fonts:
        test_font = QFont(font_name)
        default_font.setFamily(font_name)
        if test_font.exactMatch():
            break
    else:
        default_font = app.font()
    
    default_font.setPointSize(14)
    app.setFont(default_font)
    
    # 处理预定义选项
    predefined_options = []
    if args.predefined_options:
        predefined_options = args.predefined_options.split('|||')
        predefined_options = [opt.strip() for opt in predefined_options if opt.strip()]
    
    # 创建并显示UI
    ui = ThreeColumnFeedbackUI(args.prompt, predefined_options, task_title=args.task_title)
    
    # 获取调用方项目名称作为标题的一部分
    caller_project_name = ui._get_caller_project_name()
    app_title = f"Interactive Feedback MCP - {caller_project_name}"
    
    # 更新应用程序名称
    app.setApplicationName(app_title)
    # 窗口标题已在ThreeColumnFeedbackUI的_setup_window中设置
    
    # 运行UI并获取结果
    ui.show()
    app.exec()
    
    # 获取反馈结果
    result = ui.feedback_result
    
    # 如果没有结果，创建默认结果
    if result is None:
        result = {
            'interactive_feedback': '',
            'images': []
        }
    
    # 将结果写入输出文件
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return 0
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 