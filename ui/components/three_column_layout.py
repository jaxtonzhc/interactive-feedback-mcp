# -*- coding: utf-8 -*-
# Three Column Layout Component for Interactive Feedback MCP
# 三栏式布局组件

import os
import sys
import subprocess
import time
from datetime import datetime
from typing import Optional, List, TypedDict
import re

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTextBrowser, QFrame,
    QScrollArea, QApplication, QTextEdit, QSplitter, QGridLayout
)
from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QIcon, QShortcut, QKeySequence, QFont, QPixmap

from ..widgets.feedback_text_edit import FeedbackTextEdit
from ..styles.glassmorphism import GlassmorphismStyles
from ..styles.modern_glassmorphism import ModernGlassmorphismTheme
from ..styles.enhanced_glassmorphism import EnhancedGlassmorphismTheme
from ..components.text_processing import TextProcessor
from ..components.enhanced_markdown_renderer import EnhancedTextBrowser
# 集成配置管理和数据可视化
from ..utils.config_manager import global_config_manager, ThemeManager, ThemeType
from ..components.data_visualization import DataVisualizationWidget, FeedbackData
from ..utils.performance import global_performance_monitor, global_response_tracker
from ..utils.responsive import ScreenSizeManager, responsive_manager
from ..resources.icon_manager import icon_manager

class FeedbackResult(TypedDict):
    interactive_feedback: str
    images: List[str]

class ThreeColumnFeedbackUI(QMainWindow):
    """三栏式交互反馈主窗口"""
    
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None, task_title: Optional[str] = None):
        super().__init__()
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.task_title = self._build_task_title(task_title or prompt)
        self.feedback_result = None
        
        # 初始化文本处理器
        self.text_processor = TextProcessor()
        
        # Git和项目信息
        self.project_info = self._get_project_info()
        self.git_info = self._get_git_info()
        
        # 集成配置管理和数据可视化
        self.config_manager = global_config_manager
        self.data_visualization = None  # 按需创建
        
        # 性能监控
        global_performance_monitor.start_monitoring()
        start_time = time.time()
        
        self._setup_window()
        self._load_settings()
        self._create_ui()
        self._setup_shortcuts()
        self._setup_config_integration()
        self._apply_saved_config()
        
        # 检查启动性能 (PRD要求: <2s)
        startup_time = time.time() - start_time
        if startup_time > 2.0:
            print(f"⚠️ 启动时间超标: {startup_time:.2f}s (目标: <2s)")
        else:
            print(f"✅ 启动性能达标: {startup_time:.2f}s")

    def _setup_window(self):
        """设置窗口基本属性"""
        # 跟随系统主题同步当前配色模式
        self._sync_system_theme()
        
        caller_project_name = self._get_caller_project_name()
        ts = datetime.now().strftime("%H:%M:%S")
        self.setWindowTitle(f"[{ts}] {self.task_title} · {caller_project_name}")
        
        # 设置应用图标
        if icon_manager.is_available():
            app_icon = icon_manager.get_app_icon()
            self.setWindowIcon(app_icon)
            print("✅ 应用图标已加载")
        else:
            print("⚠️ 应用图标不可用，使用默认图标")
        
        # 使用更克制的常规窗口效果，避免过强玻璃感
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowOpacity(1.0)
        
        # 应用自适应主题样式
        self.setStyleSheet(EnhancedGlassmorphismTheme.get_main_window_style())
        
    def _sync_system_theme(self):
        """同步系统主题并应用到当前样式系统"""
        try:
            requested_mode = os.environ.get('MCP_FEEDBACK_THEME', 'system')
            mode = EnhancedGlassmorphismTheme.set_theme_mode(requested_mode)
            print(f"🎨 UI主题已同步系统配色: {mode}")
        except Exception as e:
            print(f"⚠️ UI主题同步异常: {e}")

    def _load_settings(self):
        """加载设置"""
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        self.line_height = self._load_line_height()
        
        screen = QApplication.primaryScreen().geometry()
        window_height = min(920, int(screen.height() * 0.78))
        window_width = min(1320, int(screen.width() * 0.78))
        
        self.resize(window_width, window_height)
        self.setMinimumSize(980, 680)
        
        # 窗口居中
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        self.move(x, y)

    def _create_ui(self):
        """创建 Summary / Reply 主区 + 右侧 Git/Actions 列的界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        outer_layout = QHBoxLayout(central_widget)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.setSpacing(10)

        main_panel = QFrame()
        main_panel.setStyleSheet(EnhancedGlassmorphismTheme.get_panel_style())
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        main_layout.addWidget(self._create_task_header(), 0)
        main_layout.addWidget(self._create_left_panel(), 6)
        main_layout.addWidget(self._create_composer_panel(), 4)

        side_panel = self._create_right_panel()

        outer_layout.addWidget(main_panel, 6)
        outer_layout.addWidget(side_panel, 2)

    def _build_task_title(self, title: str) -> str:
        """为窗口顶部生成适合展示的任务标题"""
        normalized = re.sub(r'\s+', ' ', (title or '').strip())
        if not normalized:
            return 'Interactive task'
        normalized = normalized.strip('：:.- ')
        if len(normalized) > 48:
            normalized = normalized[:47].rstrip() + '…'
        return normalized

    def _create_task_header(self):
        """顶部任务标题区，方便区分多个并行反馈窗口"""
        panel = QFrame()
        panel.setStyleSheet(EnhancedGlassmorphismTheme.get_info_section_style())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        kicker = QLabel(f'ACTIVE TASK  ·  {ts}')
        kicker.setStyleSheet(EnhancedGlassmorphismTheme.get_task_kicker_style())

        title = QLabel(self.task_title)
        title.setStyleSheet(EnhancedGlassmorphismTheme.get_task_title_style())
        title.setWordWrap(True)

        project_name = self._get_caller_project_name()
        subtitle = QLabel(f'Project: {project_name}')
        subtitle.setStyleSheet(EnhancedGlassmorphismTheme.get_task_subtitle_style())

        layout.addWidget(kicker)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return panel

    def _create_left_panel(self):
        """顶部总结内容面板"""
        panel = QFrame()
        panel.setStyleSheet(EnhancedGlassmorphismTheme.get_section_shell_style())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        title = QLabel("Summary")
        title.setStyleSheet(EnhancedGlassmorphismTheme.get_title_style())
        layout.addWidget(title)

        self.description_text = EnhancedTextBrowser()
        self.description_text.setStyleSheet(EnhancedGlassmorphismTheme.get_text_browser_style())
        summary_font = self.description_text.font()
        summary_font.setPointSize(max(summary_font.pointSize(), 15))
        self.description_text.setFont(summary_font)
        self._update_description_text()
        layout.addWidget(self.description_text, 1)

        return panel

    def _create_center_panel(self):
        """中部选项面板"""
        panel = QFrame()
        panel.setStyleSheet(EnhancedGlassmorphismTheme.get_info_section_style())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        title = QLabel("Actions")
        title.setStyleSheet(EnhancedGlassmorphismTheme.get_title_style())
        layout.addWidget(title)
        
        # 创建选项列表 - 使用增强版样式
        self.option_checkboxes = []
        if self.predefined_options:
            for i, option in enumerate(self.predefined_options, 1):
                checkbox_frame = QFrame()
                checkbox_frame.setStyleSheet(EnhancedGlassmorphismTheme.get_checkbox_frame_style())
                
                checkbox_layout = QHBoxLayout(checkbox_frame)
                checkbox_layout.setContentsMargins(10, 6, 10, 6)
                
                # 序号标签
                number_label = QLabel(f"{i}.")
                number_label.setStyleSheet(EnhancedGlassmorphismTheme.get_label_style(size='small'))
                number_label.setFixedWidth(25)
                
                # 复选框 - 使用增强版样式
                checkbox = QCheckBox(option)
                checkbox.setStyleSheet(EnhancedGlassmorphismTheme.get_checkbox_style())
                checkbox.setMinimumHeight(28)
                
                checkbox_layout.addWidget(number_label)
                checkbox_layout.addWidget(checkbox)
                
                self.option_checkboxes.append(checkbox)
                layout.addWidget(checkbox_frame)
        
        # 移除重复的默认结束选项，让用户专注于具体的操作选项
        
        hint_label = QLabel("可以多选，提交时会和下方输入内容一起发送。")
        hint_label.setStyleSheet(EnhancedGlassmorphismTheme.get_hint_label_style())
        layout.addWidget(hint_label)
        
        layout.addStretch()
        return panel

    def _create_right_panel(self):
        """右侧信息列，上半部分 Git，下半部分 Actions"""
        panel = QFrame()
        panel.setStyleSheet(EnhancedGlassmorphismTheme.get_panel_style())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        git_title = QLabel("Git")
        git_title.setStyleSheet(EnhancedGlassmorphismTheme.get_title_style())
        layout.addWidget(git_title)
        self._add_git_info_section(layout)

        actions_panel = self._create_center_panel()
        layout.addWidget(actions_panel, 1)

        return panel

    def _create_composer_panel(self):
        """底部输入区"""
        panel = QFrame()
        panel.setStyleSheet(EnhancedGlassmorphismTheme.get_section_shell_style())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        header_layout = QHBoxLayout()
        title = QLabel("Reply")
        title.setStyleSheet(EnhancedGlassmorphismTheme.get_title_style())
        helper = QLabel("Enter 发送，Shift+Enter 换行")
        helper.setStyleSheet(EnhancedGlassmorphismTheme.get_hint_label_style())
        header_layout.addWidget(title, 1)
        header_layout.addWidget(helper, 0, Qt.AlignRight | Qt.AlignVCenter)
        layout.addLayout(header_layout)

        self.custom_input = FeedbackTextEdit()
        self.custom_input.setStyleSheet(EnhancedGlassmorphismTheme.get_text_edit_style())
        font = self.custom_input.font()
        font.setPointSize(max(font.pointSize(), 16))
        self.custom_input.setFont(font)
        self.custom_input.setMinimumHeight(145)
        self.custom_input.setMaximumHeight(220)
        self.custom_input.setPlaceholderText("继续补充、确认，或者告诉模型下一步要做什么…")
        self.custom_input.image_pasted.connect(self._on_image_pasted)
        self.custom_input.ime_position_adjusted.connect(self._on_ime_position_adjusted)

        try:
            self.custom_input.submit_requested.connect(self._submit_feedback)
            print("🔗 信号连接完成: FeedbackTextEdit.submit_requested -> ThreeColumnFeedbackUI._submit_feedback")
            print("✅ 信号连接验证: submit_requested 信号已连接")
            if hasattr(self.custom_input.submit_requested, 'emit'):
                print("📡 信号发射器可用")
            else:
                print("❌ 信号发射器不可用")
        except Exception as e:
            print(f"❌ 信号连接失败: {e}")
            import traceback
            traceback.print_exc()

        layout.addWidget(self.custom_input)
        self._add_image_preview_section(layout)

        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        footer_note = QLabel("勾选项会自动附加到本次反馈中")
        footer_note.setStyleSheet(EnhancedGlassmorphismTheme.get_hint_label_style())

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        cancel_btn = QPushButton("Close")
        cancel_btn.setStyleSheet(EnhancedGlassmorphismTheme.get_button_style('error'))
        cancel_btn.clicked.connect(self.close)

        submit_btn = QPushButton("Submit")
        submit_btn.setStyleSheet(EnhancedGlassmorphismTheme.get_button_style('primary'))
        submit_btn.clicked.connect(self._submit_feedback)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(submit_btn)

        footer_layout.addWidget(footer_note, 1)
        footer_layout.addLayout(button_layout)
        layout.addLayout(footer_layout)

        return panel

    def _add_image_preview_section(self, layout):
        """添加统一图片预览区域"""
        # 图片预览容器 - 与智能推荐选项保持一致的样式
        self.images_container = QFrame()
        self.images_container.setStyleSheet(EnhancedGlassmorphismTheme.get_attachment_container_style())
        self.images_container.setFixedHeight(150)
        self.images_container.setVisible(False)  # 默认隐藏
        
        # 图片预览标题
        preview_title = QLabel("Attachments")
        preview_title.setStyleSheet(EnhancedGlassmorphismTheme.get_attachment_title_style())
        
        # 创建滚动区域用于图片预览
        self.images_scroll_area = QScrollArea()
        self.images_scroll_area.setStyleSheet(EnhancedGlassmorphismTheme.get_attachment_scroll_style())
        self.images_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.images_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.images_scroll_area.setWidgetResizable(True)
        self.images_scroll_area.setFixedHeight(112)
        
        # 图片容器widget
        images_widget = QWidget()
        self.images_layout = QHBoxLayout(images_widget)
        self.images_layout.setSpacing(8)  # 增加图片间距
        self.images_layout.setContentsMargins(8, 10, 8, 10)  # 增加内边距
        self.images_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 左对齐，垂直居中
        
        # 添加弹性空间，确保图片靠左对齐
        self.images_layout.addStretch(1)
        
        self.images_scroll_area.setWidget(images_widget)
        
        # 将组件添加到容器
        container_layout = QVBoxLayout(self.images_container)
        container_layout.setContentsMargins(10, 8, 10, 8)  # 增加内边距
        container_layout.setSpacing(5)  # 增加间距
        container_layout.addWidget(preview_title)
        container_layout.addWidget(self.images_scroll_area)
        
        # 添加到主布局
        layout.addWidget(self.images_container)

    def _on_image_pasted(self, pixmap):
        """处理粘贴的图片，显示在中间栏预览区域"""
        # 确保图片容器可见
        if not self.images_container.isVisible():
            self.images_container.setVisible(True)
        
        # 获取原始图片尺寸
        original_width = pixmap.width()
        original_height = pixmap.height()
        
        # 固定高度，保持宽高比
        target_height = 64
        scaled_width = int(original_width * (target_height / original_height))
        
        # 创建图片容器帧
        image_frame = QFrame()
        image_frame.setMinimumWidth(scaled_width)
        image_frame.setStyleSheet(EnhancedGlassmorphismTheme.get_attachment_frame_style())
        
        # 使用QGridLayout放置图片和删除按钮
        frame_layout = QGridLayout(image_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        
        # 创建图片标签
        image_label = QLabel()
        image_label.setStyleSheet("border: none; background: transparent;")
        image_label.setScaledContents(False)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(scaled_width, target_height)
        image_label.setMaximumSize(scaled_width, target_height)
        
        # 缩放图片，保持宽高比
        scaled_pixmap = pixmap.scaled(
            scaled_width,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # 支持高DPI屏幕
        device_pixel_ratio = QApplication.primaryScreen().devicePixelRatio()
        if device_pixel_ratio > 1.0:
            hires_scaled_width = int(scaled_width * device_pixel_ratio)
            hires_target_height = int(target_height * device_pixel_ratio)
            
            hires_pixmap = pixmap.scaled(
                hires_scaled_width,
                hires_target_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            hires_pixmap.setDevicePixelRatio(device_pixel_ratio)
            image_label.setPixmap(hires_pixmap)
        else:
            image_label.setPixmap(scaled_pixmap)
        
        # 删除按钮
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.setCursor(Qt.PointingHandCursor)
        delete_button.setStyleSheet(EnhancedGlassmorphismTheme.get_icon_button_style())
        
        # 删除图片的功能
        def delete_image():
            # 获取图片索引
            index = self.images_layout.indexOf(image_frame)
            if index >= 0:
                # 从布局中移除
                widget = self.images_layout.itemAt(index).widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
                    
                    # 从图片数据列表中删除
                    if hasattr(self, 'custom_input') and hasattr(self.custom_input, '_image_data'):
                        if index < len(self.custom_input._image_data):
                            del self.custom_input._image_data[index]
                    if hasattr(self, 'custom_input') and hasattr(self.custom_input, '_images_list'):
                        if index < len(self.custom_input._images_list):
                            del self.custom_input._images_list[index]
                    
                    # 检查是否还有图片
                    has_images = False
                    for i in range(self.images_layout.count()):
                        item = self.images_layout.itemAt(i)
                        if item and not item.spacerItem() and item.widget():
                            has_images = True
                            break
                    
                    # 如果没有图片了，隐藏容器
                    if not has_images:
                        self.images_container.setVisible(False)
        
        delete_button.clicked.connect(delete_image)
        
        # 将图片和删除按钮添加到布局
        frame_layout.addWidget(image_label, 0, 0)
        frame_layout.addWidget(delete_button, 0, 0, Qt.AlignTop | Qt.AlignRight)
        
        # 添加到图片布局，确保在弹性空间之前插入
        if self.images_layout.count() > 0:
            # 找到弹性空间的索引
            stretch_index = -1
            for i in range(self.images_layout.count()):
                if self.images_layout.itemAt(i).spacerItem():
                    stretch_index = i
                    break
            
            if stretch_index >= 0:
                # 在弹性空间之前插入图片
                self.images_layout.insertWidget(stretch_index, image_frame)
            else:
                # 如果没有找到弹性空间，直接添加到末尾
                self.images_layout.addWidget(image_frame)
        else:
            # 第一张图片，直接添加
            self.images_layout.addWidget(image_frame)

    # 🎯 输入法位置调整处理方法
    def _on_ime_position_adjusted(self, adjusted_rect):
        """处理输入法位置调整信号"""
        try:
            print(f"🎯 输入法位置已调整: 显示位置({adjusted_rect.x()}, {adjusted_rect.y()})")
            print("✅ 候选词框已智能下移，避免遮挡正在编辑的文本")
        except Exception as e:
            print(f"❌ 处理输入法位置调整错误: {e}")

    def _add_project_info_section(self, layout):
        """添加项目基础信息部分 - 增强版样式，使用实际项目数据"""
        # 根据是否为调用方项目显示不同的标题
        project_data = self.project_info
        is_caller = project_data.get('is_caller_project', False)
        
        if is_caller:
            info_label = QLabel("Active project")
            info_label.setStyleSheet(EnhancedGlassmorphismTheme.get_label_style(size='large'))
        else:
            info_label = QLabel("Current project (MCP server)")
            info_label.setStyleSheet(EnhancedGlassmorphismTheme.get_label_style(size='large'))
        
        layout.addWidget(info_label)
        
        info_frame = QFrame()
        info_frame.setStyleSheet(EnhancedGlassmorphismTheme.get_info_section_style())
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(5)
        
        # 获取实际项目信息
        project_data = self.project_info
        
        # 获取项目路径
        project_path = project_data.get("path", ".")
        
        # 检测项目类型（在正确的项目路径下）
        project_type = "未知项目"
        try:
            if os.path.exists(os.path.join(project_path, "pyproject.toml")):
                project_type = "Python Package (pyproject.toml)"
            elif os.path.exists(os.path.join(project_path, "requirements.txt")):
                project_type = "Python Project"
            elif os.path.exists(os.path.join(project_path, "package.json")):
                project_type = "Node.js Project"
            elif os.path.exists(os.path.join(project_path, "Cargo.toml")):
                project_type = "Rust Project"
            elif os.path.exists(os.path.join(project_path, "go.mod")):
                project_type = "Go Project"
            elif os.path.exists(os.path.join(project_path, "pom.xml")):
                project_type = "Java Project (Maven)"
            elif os.path.exists(os.path.join(project_path, "build.gradle")):
                project_type = "Java Project (Gradle)"
            elif os.path.exists(os.path.join(project_path, ".cursorrules")):
                project_type = "Cursor项目"
            else:
                # 检查是否为Git仓库
                if os.path.exists(os.path.join(project_path, ".git")):
                    project_type = "Git仓库"
                else:
                    project_type = "普通文件夹"
        except:
            project_type = "检测失败"
        
        # 计算项目大小（跨平台兼容）
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(project_path):
                # 跳过 .git 目录
                if '.git' in dirnames:
                    dirnames.remove('.git')
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
            # 格式化大小
            if total_size < 1024:
                project_size = f"{total_size}B"
            elif total_size < 1024 * 1024:
                project_size = f"{total_size / 1024:.1f}K"
            elif total_size < 1024 * 1024 * 1024:
                project_size = f"{total_size / (1024 * 1024):.1f}M"
            else:
                project_size = f"{total_size / (1024 * 1024 * 1024):.1f}G"
        except:
            project_size = "未知"
        
        # 实际项目信息
        project_info = [
            ("名称:", project_data.get("name", "未知")),
            ("类型:", project_type),
            ("文件数:", str(project_data.get("files", 0))),
            ("大小:", project_size),
            ("路径:", os.path.basename(project_data.get("path", "未知")))
        ]
        
        for label, value in project_info:
            row = QHBoxLayout()
            
            # 🎨 增强label样式 - 更明显的视觉区分
            label_widget = QLabel(label)
            label_widget.setStyleSheet(EnhancedGlassmorphismTheme.get_meta_label_style())
            label_widget.setFixedWidth(50)
            label_widget.setAlignment(Qt.AlignCenter)
            
            # 🎯 增强value样式 - 清晰的内容显示
            value_widget = QLabel(value)
            value_widget.setStyleSheet(EnhancedGlassmorphismTheme.get_meta_value_style())
            value_widget.setWordWrap(True)
            
            row.addWidget(label_widget)
            row.addWidget(value_widget)
            row.addStretch()
            info_layout.addLayout(row)
        
        layout.addWidget(info_frame)

    def _add_git_info_section(self, layout):
        """添加Git状态信息部分，使用实际Git数据"""
        # 根据是否为调用方项目显示不同的Git标题
        git_data = self.git_info
        is_caller = git_data.get('is_caller_project', False)
        
        if is_caller:
            git_label = QLabel("Status")
            git_label.setStyleSheet(EnhancedGlassmorphismTheme.get_section_caption_style())
        else:
            git_label = QLabel("Status (MCP server)")
            git_label.setStyleSheet(EnhancedGlassmorphismTheme.get_section_caption_style())
        
        layout.addWidget(git_label)
        
        git_frame = QFrame()
        git_frame.setStyleSheet(EnhancedGlassmorphismTheme.get_info_section_style())
        
        git_layout = QVBoxLayout(git_frame)
        git_layout.setSpacing(5)
        
        # 获取实际Git信息
        git_data = self.git_info
        
        # 获取额外Git信息（在正确的项目路径下）
        project_dir = git_data.get("project_dir", ".")
        data_source = git_data.get("data_source", "local_query")
        
        try:
            if data_source == "mcp_server":
                # 如果是从MCP服务器获取的数据，尝试补充本地查询
                untracked_result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                                                cwd=project_dir, capture_output=True, text=True, timeout=5)
                untracked_count = len(untracked_result.stdout.strip().split('\n')) if untracked_result.stdout.strip() else 0
                
                author_result = subprocess.run(['git', 'log', '-1', '--pretty=format:%an'], 
                                             cwd=project_dir, capture_output=True, text=True, timeout=5)
                author = author_result.stdout.strip() if author_result.returncode == 0 else "MCP数据"
                
                time_result = subprocess.run(['git', 'log', '-1', '--pretty=format:%ar'], 
                                           cwd=project_dir, capture_output=True, text=True, timeout=5)
                commit_time = time_result.stdout.strip() if time_result.returncode == 0 else "MCP数据"
            else:
                # 本地查询
                untracked_result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                                                cwd=project_dir, capture_output=True, text=True, timeout=5)
                untracked_count = len(untracked_result.stdout.strip().split('\n')) if untracked_result.stdout.strip() else 0
                
                author_result = subprocess.run(['git', 'log', '-1', '--pretty=format:%an'], 
                                             cwd=project_dir, capture_output=True, text=True, timeout=5)
                author = author_result.stdout.strip() if author_result.returncode == 0 else "未知"
                
                time_result = subprocess.run(['git', 'log', '-1', '--pretty=format:%ar'], 
                                           cwd=project_dir, capture_output=True, text=True, timeout=5)
                commit_time = time_result.stdout.strip() if time_result.returncode == 0 else "未知"
        except:
            untracked_count = 0
            author = "查询失败"
            commit_time = "查询失败"
        
        # 实际Git信息
        git_info = [
            ("分支:", git_data.get("branch", "未知")),
            ("修改文件:", f"{git_data.get('modified_files', 0)}个"),
            ("未跟踪:", f"{untracked_count}个"),
            ("最后提交:", git_data.get("last_commit", "无提交")[:50] + "..." if len(git_data.get("last_commit", "")) > 50 else git_data.get("last_commit", "无提交")),
            ("作者:", author),
            ("时间:", commit_time)
        ]
        
        for label, value in git_info:
            row_layout = QVBoxLayout() if label == "最后提交:" else QHBoxLayout()
            
            label_widget = QLabel(label)
            label_widget.setStyleSheet(EnhancedGlassmorphismTheme.get_meta_label_style())
            if isinstance(row_layout, QHBoxLayout):
                label_widget.setFixedWidth(50)
                label_widget.setAlignment(Qt.AlignCenter)
            
            value_widget = QLabel(value)
            value_widget.setStyleSheet(EnhancedGlassmorphismTheme.get_meta_value_style(EnhancedGlassmorphismTheme._colors()['accent_secondary']))
            if label == "最后提交:":
                value_widget.setWordWrap(True)
                value_widget.setMaximumHeight(40)
            
            if isinstance(row_layout, QHBoxLayout):
                row_layout.addWidget(label_widget)
                row_layout.addWidget(value_widget)
                row_layout.addStretch()
                git_layout.addLayout(row_layout)
            else:
                git_layout.addWidget(label_widget)
                git_layout.addWidget(value_widget)
        
        layout.addWidget(git_frame)


    def _add_project_activity_section(self, layout):
        """添加项目活动信息部分，使用实际项目数据"""
        activity_label = QLabel("Project activity")
        activity_label.setStyleSheet(EnhancedGlassmorphismTheme.get_section_caption_style())
        layout.addWidget(activity_label)
        
        activity_frame = QFrame()
        activity_frame.setStyleSheet(ModernGlassmorphismTheme.get_info_section_style())
        
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setSpacing(5)
        
        # 获取实际项目活动信息
        try:
            # 统计文件类型
            file_types = {}
            large_files = 0
            for root, dirs, files in os.walk('.'):
                # 跳过隐藏目录和常见的非重要目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.venv']]
                for file in files:
                    if not file.startswith('.'):
                        ext = os.path.splitext(file)[1].lower() or 'no_ext'
                        file_types[ext] = file_types.get(ext, 0) + 1
                        
                        # 检查文件大小
                        try:
                            file_path = os.path.join(root, file)
                            if os.path.getsize(file_path) > 100 * 1024:  # >100KB
                                large_files += 1
                        except:
                            pass
            
            # 获取主要文件类型
            top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
            file_types_str = ", ".join([f"{ext}({count})" for ext, count in top_types])
            
            # 获取最近修改的文件（跨平台兼容）
            try:
                import time
                one_day_ago = time.time() - 86400  # 24小时前
                recent_files = 0
                for dirpath, dirnames, filenames in os.walk(project_path):
                    # 跳过 .git 目录
                    if '.git' in dirnames:
                        dirnames.remove('.git')
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        try:
                            if os.path.getmtime(fp) > one_day_ago:
                                recent_files += 1
                        except OSError:
                            pass
            except:
                recent_files = 0
            
            # 检测主要语言
            python_files = file_types.get('.py', 0)
            js_files = file_types.get('.js', 0)
            ts_files = file_types.get('.ts', 0)
            
            if python_files > 0:
                main_language = "Python"
            elif js_files > 0 or ts_files > 0:
                main_language = "JavaScript/TypeScript" 
            else:
                main_language = "多语言"
                
        except Exception as e:
            file_types_str = "未知"
            large_files = 0
            recent_files = 0
            main_language = "未知"
            print(f"项目活动信息收集错误: {e}")
        
        # 实际活动信息
        activity_info = [
            ("最近修改:", f"{recent_files}个文件 (24小时内)"),
            ("大文件:", f"{large_files}个 (>100KB)"),
            ("主要语言:", main_language),
            ("文件类型:", file_types_str),
            ("总文件数:", str(self.project_info.get("files", 0)))
        ]
        
        for label, value in activity_info:
            row = QHBoxLayout()
            
            # 🎨 增强label样式 - 活动信息专用配色
            label_widget = QLabel(label)
            label_widget.setStyleSheet(EnhancedGlassmorphismTheme.get_meta_label_style())
            label_widget.setFixedWidth(60)
            label_widget.setAlignment(Qt.AlignCenter)
            
            # 🎯 增强value样式 - 活动信息专用样式
            value_widget = QLabel(value)
            value_widget.setStyleSheet(EnhancedGlassmorphismTheme.get_meta_value_style())
            value_widget.setWordWrap(True)
            
            row.addWidget(label_widget)
            row.addWidget(value_widget)
            activity_layout.addLayout(row)
        
        layout.addWidget(activity_frame)



    def _get_layout_improvements(self):
        """获取布局改进建议"""
        return """
        <div style="color: #ccc; font-size: 12px; line-height: 1.4;">
        <p><strong style="color: #4CAF50;">✅ CSS Grid布局优化:</strong></p>
        <ul style="margin: 5px 0; padding-left: 15px;">
        <li>网格布局定义: repeat(auto-fit, minmax(100px, 1fr)) → repeat(auto-fill, 100px)</li>
        <li>新增网格对齐: justify-content: start</li>
        <li>最小网格定义尺寸: width: 100px</li>
        <li>文字居中对齐: text-align: center</li>
        </ul>
        
        <p><strong style="color: #4CAF50;">🎨 布局行为改进:</strong></p>
        <ul style="margin: 5px 0; padding-left: 15px;">
        <li>按钮样式优化和响应性提升</li>
        <li>固定100px宽度，排列整齐</li>
        <li>保持12x间距，美观排版</li>
        <li>自动换行时的间距对齐</li>
        </ul>
        </div>
        """



    def _get_project_info(self):
        """获取项目基础信息 - 优先获取调用方项目信息"""
        try:
            # 从环境变量获取调用方项目信息（由MCP服务器传递）
            caller_cwd = os.environ.get('MCP_CALLER_CWD')
            caller_name = os.environ.get('MCP_CALLER_PROJECT_NAME', 'unknown')
            is_detected = os.environ.get('MCP_CALLER_IS_DETECTED', 'false').lower() == 'true'
            
            # 清理从环境变量获取的项目名称
            caller_name = self._clean_project_name(caller_name)
            
            if caller_cwd and os.path.exists(caller_cwd):
                # 使用调用方项目信息
                file_count = 0
                try:
                    file_count = len([f for f in os.listdir(caller_cwd) 
                                    if os.path.isfile(os.path.join(caller_cwd, f))])
                except:
                    file_count = 0
                
                return {
                    "name": caller_name,
                    "path": caller_cwd,
                    "files": file_count,
                    "is_caller_project": True,
                    "is_detected": is_detected
                }
            else:
                # 回退到本地检测方法
                cwd = self._detect_caller_project_dir()
                if not cwd:
                    cwd = os.getcwd()
                
                # 也清理本地项目名称
                local_name = self._clean_project_name(os.path.basename(cwd))
                
                return {
                    "name": local_name,
                    "path": cwd,
                    "files": len([f for f in os.listdir(cwd) if os.path.isfile(f)]) if os.path.exists(cwd) else 0,
                    "is_caller_project": cwd != os.getcwd(),
                    "is_detected": False
                }
        except:
            return {
                "name": "unknown", 
                "path": "unknown", 
                "files": 0, 
                "is_caller_project": False,
                "is_detected": False
            }

    def _detect_caller_project_dir(self):
        """检测调用方项目目录"""
        try:
            import psutil
            current_process = psutil.Process()
            parent_process = current_process.parent()
            
            # 获取父进程的工作目录
            if parent_process and hasattr(parent_process, 'cwd'):
                parent_cwd = parent_process.cwd()
                # 检查是否为有效的项目目录（包含常见项目文件）
                if self._is_project_directory(parent_cwd):
                    return parent_cwd
            
            # 如果父进程方法失败，尝试从命令行参数推断
            import sys
            for arg in sys.argv:
                if arg.startswith('--project-dir='):
                    project_dir = arg.split('=', 1)[1]
                    if os.path.exists(project_dir):
                        return project_dir
            
            return None
        except:
            return None
    
    def _is_project_directory(self, path):
        """判断是否为项目目录"""
        if not os.path.exists(path):
            return False
        
        # 检查常见的项目标识文件
        project_indicators = [
            '.git', 'package.json', 'requirements.txt', 'pyproject.toml',
            'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
            '.gitignore', 'README.md', 'README.rst'
        ]
        
        for indicator in project_indicators:
            if os.path.exists(os.path.join(path, indicator)):
                return True
        
        return False

    def _get_caller_project_name(self):
        """获取调用方项目名称用于窗口标题"""
        project_info = self._get_project_info()
        project_name = project_info.get('name', 'unknown')
        is_caller = project_info.get('is_caller_project', False)
        
        # 清理项目名称中的特殊字符，避免乱码问题
        cleaned_name = self._clean_project_name(project_name)
        
        if is_caller:
            return cleaned_name
        else:
            # 如果没有检测到调用方项目，显示MCP服务器项目名
            return f"{cleaned_name} (MCP Server)"
    
    def _clean_project_name(self, name: str) -> str:
        """清理项目名称中的特殊字符和乱码"""
        try:
            if not name:
                return 'unknown'
            
            # 如果是None或其他类型，先转换为字符串
            if name is None:
                return 'unknown'
            
            if not isinstance(name, str):
                name = str(name)
            
            # 简化UTF-8处理 - 避免重复编码
            if isinstance(name, bytes):
                try:
                    name = name.decode('utf-8')
                except UnicodeDecodeError:
                    # 使用更安全的错误处理
                    name = name.decode('utf-8', errors='ignore')
            
            # 移除控制字符和乱码符号
            name = re.sub(r'[\x00-\x1f\x7f-\x9f\ufffd◇◆]', '', name)
            
            # 移除多余的空格
            name = re.sub(r'\s+', ' ', name).strip()
            
            # 如果清理后为空，返回默认值
            if not name:
                return 'unknown'
                
            return name
            
        except Exception as e:
            print(f"⚠️ 项目名称清理失败: {e}")
            return 'unknown'

    def _get_git_info(self):
        """获取Git状态信息 - 优先获取调用方项目的Git状态"""
        try:
            # 首先尝试从环境变量获取调用方Git信息（由MCP服务器传递）
            caller_branch = os.environ.get('MCP_CALLER_GIT_BRANCH')
            caller_modified = os.environ.get('MCP_CALLER_GIT_MODIFIED_FILES')
            caller_commit = os.environ.get('MCP_CALLER_GIT_LAST_COMMIT')
            caller_is_git = os.environ.get('MCP_CALLER_IS_GIT_REPO', 'false').lower() == 'true'
            
            # 获取项目信息
            project_info = self._get_project_info()
            project_dir = project_info.get('path', os.getcwd())
            is_caller_project = project_info.get('is_caller_project', False)
            
            if caller_branch and is_caller_project:
                # 使用MCP服务器传递的Git信息
                return {
                    "branch": caller_branch if caller_branch != 'unknown' else 'unknown',
                    "modified_files": int(caller_modified) if caller_modified and caller_modified.isdigit() else 0,
                    "last_commit": caller_commit if caller_commit != 'unknown' else 'No commits',
                    "project_dir": project_dir,
                    "is_caller_project": is_caller_project,
                    "is_git_repo": caller_is_git,
                    "data_source": "mcp_server"
                }
            else:
                # 回退到本地Git命令查询
                git_commands = [
                    (['git', 'branch', '--show-current'], 'branch'),
                    (['git', 'status', '--porcelain'], 'status'),
                    (['git', 'log', '-1', '--pretty=format:%s'], 'log')
                ]
                
                results = {}
                for cmd, key in git_commands:
                    try:
                        result = subprocess.run(cmd, cwd=project_dir,
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            results[key] = result.stdout.strip()
                        else:
                            results[key] = ""
                    except:
                        results[key] = ""
                
                # 处理结果
                branch = results.get('branch', 'unknown') or 'unknown'
                status_output = results.get('status', '')
                modified_files = len(status_output.split('\n')) if status_output.strip() else 0
                last_commit = results.get('log', 'No commits') or 'No commits'
                
                return {
                    "branch": branch,
                    "modified_files": modified_files,
                    "last_commit": last_commit,
                    "project_dir": project_dir,
                    "is_caller_project": is_caller_project,
                    "is_git_repo": branch != 'unknown',
                    "data_source": "local_query"
                }
        except:
            return {
                "branch": "unknown", 
                "modified_files": 0, 
                "last_commit": "unknown", 
                "project_dir": "unknown", 
                "is_caller_project": False,
                "is_git_repo": False,
                "data_source": "error"
            }

    def _setup_shortcuts(self):
        """设置快捷键 - 根据PRD文档增强"""
        # 字体缩放快捷键
        zoom_in = QShortcut(QKeySequence("Ctrl+="), self)
        zoom_in.activated.connect(lambda: self.adjust_font_size(1.1))

        zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out.activated.connect(lambda: self.adjust_font_size(0.9))

        reset_font = QShortcut(QKeySequence("Ctrl+0"), self)
        reset_font.activated.connect(self.reset_font_size)
        
        # PRD文档中定义的快捷键
        # Enter: 由文本框处理，不设置全局快捷键
        # Esc: 取消/关闭
        cancel_shortcut = QShortcut(QKeySequence("Escape"), self)
        cancel_shortcut.activated.connect(self.close)
        
        # Ctrl+1-9: 快速选择选项
        for i in range(1, min(10, len(self.option_checkboxes) + 1)):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda checked, idx=i-1: self._toggle_option(idx))
        
        # Ctrl+/: 显示帮助（暂时显示快捷键信息）
        help_shortcut = QShortcut(QKeySequence("Ctrl+/"), self)
        help_shortcut.activated.connect(self._show_help)
    
    def _setup_config_integration(self):
        """设置配置管理集成"""
        # 连接配置变更信号
        self.config_manager.theme_changed.connect(self._on_theme_changed)
        self.config_manager.config_changed.connect(self._on_config_changed)
        
        # 添加配置相关的快捷键
        config_shortcuts = [
            ("Ctrl+T", "切换主题", self._toggle_theme),
            ("Ctrl+D", "显示数据分析", self._show_data_visualization),
            ("Ctrl+E", "导出配置", self._export_config),
            ("Ctrl+I", "导入配置", self._import_config),
            ("Ctrl+R", "重置配置", self._reset_config)
        ]
        
        for shortcut, description, callback in config_shortcuts:
            shortcut_obj = QShortcut(QKeySequence(shortcut), self)
            shortcut_obj.activated.connect(callback)
            print(f"🔧 已注册快捷键: {shortcut} - {description}")
    
    def _apply_saved_config(self):
        """应用保存的配置"""
        config = self.config_manager.config
        
        # 应用窗口尺寸
        self.resize(config.ui.window_width, config.ui.window_height)
        
        # 应用主题
        theme_type = ThemeType(config.ui.theme)
        ThemeManager.apply_theme(self, theme_type)
        
        # 应用字体设置
        if hasattr(QApplication.instance(), 'setFont'):
            font = QApplication.instance().font()
            font.setPointSize(config.ui.font_size)
            font.setFamily(config.ui.font_family)
            QApplication.instance().setFont(font)
        
        print(f"✅ 已应用配置: 主题={config.ui.theme}, 字体={config.ui.font_size}px")
    
    def _on_theme_changed(self, theme_name: str):
        """主题变更处理"""
        theme_type = ThemeType(theme_name)
        ThemeManager.apply_theme(self, theme_type)
        print(f"🎨 主题已切换: {theme_name}")
    
    def _on_config_changed(self, config_type: str, value):
        """配置变更处理"""
        if config_type == "window_size":
            width, height = value
            self.resize(width, height)
        elif config_type == "font_size":
            # 字体大小已在config_manager中处理
            pass
        elif config_type == "panel_ratios":
            # 重新调整面板比例
            self._adjust_panel_ratios(value)
        
        print(f"⚙️ 配置已更新: {config_type} = {value}")
    
    def _adjust_panel_ratios(self, ratios: List[int]):
        """调整面板比例"""
        if hasattr(self, 'splitter') and len(ratios) == 3:
            total_width = self.width()
            sizes = [int(total_width * ratio / 100) for ratio in ratios]
            self.splitter.setSizes(sizes)
    
    def _toggle_theme(self):
        """切换主题 - 强制深色模式"""
        current_theme = self.config_manager.config.ui.theme
        available_themes = [
            ThemeType.ENHANCED_GLASSMORPHISM,
            ThemeType.MODERN_GLASSMORPHISM,
            ThemeType.GLASSMORPHISM,
            ThemeType.DARK,
            ThemeType.HIGH_CONTRAST
        ]
        
        # 找到当前主题的索引
        current_index = 0
        for i, theme in enumerate(available_themes):
            if theme.value == current_theme:
                current_index = i
                break
        
        # 切换到下一个主题
        next_index = (current_index + 1) % len(available_themes)
        next_theme = available_themes[next_index]
        
        self.config_manager.set_theme(next_theme)
    
    def _show_data_visualization(self):
        """显示数据可视化"""
        if self.data_visualization is None:
            self.data_visualization = DataVisualizationWidget()
            self.data_visualization.setWindowTitle("📊 Interactive Feedback MCP - 数据分析")
            
            # 添加当前反馈数据
            if hasattr(self, 'feedback_result') and self.feedback_result:
                feedback_data = self._create_feedback_data_from_result()
                self.data_visualization.add_feedback_data(feedback_data)
        
        self.data_visualization.show()
        print("📊 数据可视化窗口已打开")
    
    def _create_feedback_data_from_result(self) -> FeedbackData:
        """从反馈结果创建数据对象"""
        from datetime import datetime
        
        selected_options = []
        if hasattr(self, 'feedback_result') and self.feedback_result:
            if 'interactive_feedback' in self.feedback_result:
                feedback_text = self.feedback_result['interactive_feedback']
                # 简单解析选中的选项
                if hasattr(self, 'predefined_options'):
                    for option in self.predefined_options:
                        if option in feedback_text:
                            selected_options.append(option)
        
        return FeedbackData(
            timestamp=datetime.now(),
            user_id="current_user",
            message=getattr(self, 'prompt', ''),
            selected_options=selected_options,
            custom_input=self.custom_input.toPlainText() if hasattr(self, 'custom_input') else '',
            response_time=getattr(self, 'last_response_time', 0.0),
            satisfaction_score=4,  # 默认满意度
            category="interactive"
        )
    
    def _export_config(self):
        """导出配置"""
        from datetime import datetime
        filename = f"interactive_feedback_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        success = self.config_manager.export_config(filename)
        
        if success:
            # 在描述区域显示成功消息
            self.description_text.append(f"\n✅ 配置已导出到: {filename}")
        else:
            self.description_text.append(f"\n❌ 配置导出失败")
    
    def _import_config(self):
        """导入配置（简化版，实际应用中可以添加文件选择对话框）"""
        self.description_text.append(f"\n💡 配置导入功能：请使用 config_manager.import_config(file_path) 方法")
    
    def _reset_config(self):
        """重置配置"""
        self.config_manager.reset_to_default()
        self.description_text.append(f"\n🔄 配置已重置为默认值")
    
    def _record_feedback_data(self):
        """记录反馈数据用于分析"""
        if hasattr(self, 'feedback_result') and self.feedback_result:
            feedback_data = self._create_feedback_data_from_result()
            
            # 如果数据可视化窗口已打开，添加数据
            if self.data_visualization is not None:
                self.data_visualization.add_feedback_data(feedback_data)
            
            print(f"📝 已记录反馈数据: {len(feedback_data.selected_options)} 个选项")
    
    def _save_window_state(self):
        """保存窗口状态到配置"""
        self.config_manager.set_window_size(self.width(), self.height())
        
        # 保存面板比例
        if hasattr(self, 'splitter'):
            sizes = self.splitter.sizes()
            total = sum(sizes)
            if total > 0:
                ratios = [int(size * 100 / total) for size in sizes]
                # 确保总和为100
                if sum(ratios) != 100:
                    ratios[-1] = 100 - sum(ratios[:-1])
                self.config_manager.set_panel_ratios(ratios)
    
    def _toggle_option(self, index):
        """切换选项状态"""
        if 0 <= index < len(self.option_checkboxes):
            checkbox = self.option_checkboxes[index]
            checkbox.setChecked(not checkbox.isChecked())
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
        <div style="color: #fff; font-size: 13px; line-height: 1.6; padding: 10px;">
        <h3 style="color: #2196F3;">🎯 快捷键帮助</h3>
        <p><strong>Enter:</strong> 提交反馈</p>
        <p><strong>Shift+Enter:</strong> 在输入框中换行</p>
        <p><strong>Ctrl+1-9:</strong> 快速选择/取消选项</p>
        <p><strong>Ctrl+/:</strong> 显示此帮助</p>
        <p><strong>Esc:</strong> 取消/关闭窗口</p>
        <p><strong>Ctrl +/-:</strong> 缩放字体</p>
        <p><strong>Ctrl+0:</strong> 重置字体大小</p>
        </div>
        """
        # 临时在描述区域显示帮助
        original_html = self.description_text.toHtml()
        self.description_text.setHtml(help_text)
        
        # 3秒后恢复原内容
        QTimer.singleShot(3000, lambda: self.description_text.setHtml(original_html))

    def _update_description_text(self):
        """更新描述文本内容"""
        # 使用增强markdown渲染器处理内容
        self.description_text.set_markdown_content(self.prompt)

    def adjust_font_size(self, factor: float):
        """调整字体大小"""
        app = QApplication.instance()
        current_font = app.font()
        new_size = max(8, int(current_font.pointSize() * factor))
        current_font.setPointSize(new_size)
        app.setFont(current_font)

    def reset_font_size(self):
        """重置字体大小"""
        app = QApplication.instance()
        default_font = app.font()
        default_font.setPointSize(15)
        app.setFont(default_font)

    def _load_line_height(self) -> float:
        """加载行高设置"""
        self.settings.beginGroup("AppearanceSettings")
        line_height = self.settings.value("lineHeight", 1.3, type=float)
        self.settings.endGroup()
        return line_height

    def _submit_feedback(self):
        """提交反馈"""
        print("🎯 _submit_feedback() 方法被调用！！！")
        print(f"🕐 调用时间: {time.time()}")
        print(f"📍 调用源: 通过信号槽机制触发")
        
        start_time = global_response_tracker.start_timing()
        
        feedback_text = self.custom_input.toPlainText().strip()
        print(f"📝 输入框内容: '{feedback_text}'")
        selected_options = []

        # 获取选中的预定义选项
        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    selected_options.append(self.predefined_options[i])

        # 获取图片数据
        image_data = self.custom_input.get_image_data()
        images = [img['base64'] for img in image_data] if image_data else []

        # 组合反馈内容
        combined_feedback = []
        if selected_options:
            combined_feedback.append("选择的选项:")
            for option in selected_options:
                combined_feedback.append(f"- {option}")
        
        if feedback_text:
            if combined_feedback:
                combined_feedback.append("\n自定义反馈:")
            combined_feedback.append(feedback_text)

        final_feedback = "\n".join(combined_feedback) if combined_feedback else "无反馈内容"

        self.feedback_result = FeedbackResult(
            interactive_feedback=final_feedback,
            images=images
        )
        
        # 记录响应时间
        response_time = global_response_tracker.end_timing(start_time, "submit_feedback")
        self.last_response_time = response_time
        
        # 记录反馈数据用于分析（需要先设置feedback_result）
        try:
            self._record_feedback_data()
        except Exception as e:
            print(f"⚠️ 记录反馈数据失败: {e}")
        
        # 保存窗口状态到配置
        self._save_window_state()
        
        print(f"✅ 反馈已提交 (响应时间: {response_time:.0f}ms)")
        print(f"📝 选中选项: {selected_options}")
        if feedback_text:
            print(f"💬 自定义输入: {feedback_text}")
        
        self.close()

    def closeEvent(self, event):
        """关闭事件处理"""
        event.accept()

    def run(self) -> FeedbackResult:
        """运行UI并返回结果"""
        self.show()
        return self.feedback_result 