# Glassmorphism Styles for Interactive Feedback MCP
# 毛玻璃样式定义

def _is_dark_mode() -> bool:
    """检测系统是否处于暗色模式"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette
        app = QApplication.instance()
        if app:
            palette = app.palette()
            bg = palette.color(QPalette.ColorRole.Window)
            return bg.lightness() < 128
    except Exception:
        pass
    return True


class GlassmorphismStyles:
    """毛玻璃效果样式类"""
    
    @staticmethod
    def is_dark():
        return _is_dark_mode()

    @staticmethod
    def main_window():
        """主窗口毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(45, 45, 60, 0.90),
                        stop:0.5 rgba(55, 55, 70, 0.85),
                        stop:1 rgba(40, 40, 55, 0.90));
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
            """
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(240, 240, 245, 0.95),
                    stop:0.5 rgba(245, 245, 250, 0.92),
                    stop:1 rgba(235, 235, 240, 0.95));
                border-radius: 15px;
                border: 1px solid rgba(0, 0, 0, 0.12);
            }
        """
    
    @staticmethod
    def central_widget():
        """中央widget毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QWidget {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                }
            """
        return """
            QWidget {
                background: rgba(0, 0, 0, 0.03);
                border-radius: 12px;
            }
        """
    
    @staticmethod
    def text_browser():
        """文本浏览器毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QTextBrowser {
                    background: rgba(255, 255, 255, 0.12);
                    border: 1px solid rgba(255, 255, 255, 0.20);
                    border-radius: 12px;
                    padding: 15px;
                    margin-bottom: 8px;
                    color: #f0f0f0;
                    selection-background-color: rgba(33, 150, 243, 0.6);
                }
                QTextBrowser:focus {
                    border: 2px solid rgba(33, 150, 243, 0.8);
                    background: rgba(255, 255, 255, 0.16);
                }
            """ + GlassmorphismStyles._scrollbar_vertical()
        return """
            QTextBrowser {
                background: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 8px;
                color: #1a1a1a;
                selection-background-color: rgba(33, 150, 243, 0.3);
            }
            QTextBrowser:focus {
                border: 2px solid rgba(33, 150, 243, 0.6);
                background: rgba(255, 255, 255, 0.92);
            }
        """ + GlassmorphismStyles._scrollbar_vertical_light()
    
    @staticmethod
    def text_edit():
        """文本编辑器毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QTextEdit {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 12px;
                    padding: 12px;
                    margin: 5px 0px 15px 0px;
                    color: #e0e0e0;
                    selection-background-color: rgba(33, 150, 243, 0.6);
                }
                QTextEdit:focus {
                    border: 2px solid rgba(33, 150, 243, 0.8);
                    background: rgba(255, 255, 255, 0.12);
                }
            """ + GlassmorphismStyles._scrollbar_vertical()
        return """
            QTextEdit {
                background: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 12px;
                padding: 12px;
                margin: 5px 0px 15px 0px;
                color: #1a1a1a;
                selection-background-color: rgba(33, 150, 243, 0.3);
            }
            QTextEdit:focus {
                border: 2px solid rgba(33, 150, 243, 0.6);
                background: rgba(255, 255, 255, 0.92);
            }
        """ + GlassmorphismStyles._scrollbar_vertical_light()
    
    @staticmethod
    def options_frame():
        """选项框架毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QFrame {
                    background: rgba(255, 255, 255, 0.10);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 10px;
                    padding: 10px;
                    margin: 5px 0px;
                }
            """
        return """
            QFrame {
                background: rgba(0, 0, 0, 0.04);
                border: 1px solid rgba(0, 0, 0, 0.10);
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0px;
            }
        """
    
    @staticmethod
    def checkbox():
        """复选框毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QCheckBox {
                    color: #e0e0e0;
                    spacing: 8px;
                    padding: 5px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    background: rgba(255, 255, 255, 0.1);
                }
                QCheckBox::indicator:hover {
                    border: 2px solid rgba(33, 150, 243, 0.6);
                    background: rgba(33, 150, 243, 0.2);
                }
                QCheckBox::indicator:checked {
                    background: rgba(33, 150, 243, 0.8);
                    border: 2px solid rgba(33, 150, 243, 1.0);
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
                }
                QCheckBox:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 6px;
                }
            """
        return """
            QCheckBox {
                color: #1a1a1a;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid rgba(0, 0, 0, 0.25);
                background: rgba(255, 255, 255, 0.8);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(33, 150, 243, 0.6);
                background: rgba(33, 150, 243, 0.1);
            }
            QCheckBox::indicator:checked {
                background: rgba(33, 150, 243, 0.8);
                border: 2px solid rgba(33, 150, 243, 1.0);
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            QCheckBox:hover {
                background: rgba(0, 0, 0, 0.03);
                border-radius: 6px;
            }
        """
    
    @staticmethod
    def images_container():
        """图片容器毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QFrame {
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 8px;
                    padding: 5px;
                    margin: 2px 0px;
                }
            """
        return """
            QFrame {
                background: rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
                padding: 5px;
                margin: 2px 0px;
            }
        """
    
    @staticmethod
    def submit_button():
        """提交按钮毛玻璃样式"""
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(33, 150, 243, 0.9),
                    stop:1 rgba(21, 101, 192, 0.9));
                color: white;
                border: 1px solid rgba(33, 150, 243, 0.6);
                border-radius: 8px;
                padding: 12px 24px;
                margin-left: 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(33, 150, 243, 1.0),
                    stop:1 rgba(21, 101, 192, 1.0));
                border: 1px solid rgba(33, 150, 243, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(21, 101, 192, 1.0),
                    stop:1 rgba(13, 71, 161, 1.0));
            }
        """
    
    @staticmethod
    def cancel_button():
        """取消按钮毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(158, 158, 158, 0.6),
                        stop:1 rgba(117, 117, 117, 0.6));
                    color: white;
                    border: 1px solid rgba(158, 158, 158, 0.4);
                    border-radius: 8px;
                    padding: 12px 24px;
                    margin-right: 20px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(158, 158, 158, 0.7),
                        stop:1 rgba(117, 117, 117, 0.7));
                    border: 1px solid rgba(158, 158, 158, 0.6);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(117, 117, 117, 0.8),
                        stop:1 rgba(97, 97, 97, 0.8));
                }
            """
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(200, 200, 200, 0.8),
                    stop:1 rgba(180, 180, 180, 0.8));
                color: #333333;
                border: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 8px;
                padding: 12px 24px;
                margin-right: 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(190, 190, 190, 0.9),
                    stop:1 rgba(170, 170, 170, 0.9));
                border: 1px solid rgba(0, 0, 0, 0.18);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(170, 170, 170, 0.9),
                    stop:1 rgba(150, 150, 150, 0.9));
            }
        """
    
    @staticmethod
    def info_label():
        """信息标签毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QLabel {
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 10pt;
                    font-family: "PingFang SC", "Hiragino Sans GB", sans-serif;
                    background: rgba(255, 255, 255, 0.03);
                    border-radius: 6px;
                    padding: 5px 10px;
                    margin: 5px 0px;
                }
            """
        return """
            QLabel {
                color: rgba(0, 0, 0, 0.5);
                font-size: 10pt;
                font-family: "PingFang SC", "Hiragino Sans GB", sans-serif;
                background: rgba(0, 0, 0, 0.03);
                border-radius: 6px;
                padding: 5px 10px;
                margin: 5px 0px;
            }
        """
    
    @staticmethod
    def scroll_area():
        """滚动区域毛玻璃样式"""
        if GlassmorphismStyles.is_dark():
            return """
                QScrollArea {
                    background: transparent;
                    border: none;
                    margin: 0px;
                    padding: 0px;
                }
            """ + GlassmorphismStyles._scrollbar_horizontal()
        return """
            QScrollArea {
                background: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """ + GlassmorphismStyles._scrollbar_horizontal_light()
    
    @staticmethod
    def _scrollbar_vertical():
        """垂直滚动条样式"""
        return """
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
    
    @staticmethod
    def _scrollbar_horizontal():
        """水平滚动条样式"""
        return """
            QScrollBar:horizontal {
                height: 8px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """

    @staticmethod
    def _scrollbar_vertical_light():
        """亮色模式垂直滚动条样式"""
        return """
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.05);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 0, 0, 0.35);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    @staticmethod
    def _scrollbar_horizontal_light():
        """亮色模式水平滚动条样式"""
        return """
            QScrollBar:horizontal {
                height: 8px;
                background: rgba(0, 0, 0, 0.05);
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 0, 0, 0.35);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """