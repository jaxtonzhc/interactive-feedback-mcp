"""验证所有模块可正常导入，不会因缺失依赖而崩溃。"""

import pytest


def test_import_server():
    import server
    assert hasattr(server, "mcp")
    assert hasattr(server, "interactive_feedback")


def test_import_enhanced_feedback_ui():
    import enhanced_feedback_ui
    assert hasattr(enhanced_feedback_ui, "main")


def test_import_ui_components():
    from ui.components.text_processing import TextProcessor
    from ui.components.enhanced_markdown_renderer import EnhancedTextBrowser
    from ui.components.three_column_layout import ThreeColumnFeedbackUI
    from ui.components.data_visualization import DataVisualizationWidget


def test_import_ui_styles():
    from ui.styles.glassmorphism import GlassmorphismStyles
    from ui.styles.enhanced_glassmorphism import EnhancedGlassmorphismTheme
    from ui.styles.modern_glassmorphism import ModernGlassmorphismTheme


def test_import_ui_utils():
    from ui.utils.logging_system import init_logging, get_logger
    from ui.utils.performance import global_performance_monitor
    from ui.utils.config_manager import global_config_manager
    from ui.utils.responsive import responsive_manager


def test_import_ui_widgets():
    from ui.widgets.feedback_text_edit import FeedbackTextEdit


def test_import_ui_resources():
    from ui.resources.icon_manager import icon_manager
