# Adaptive sci-fi IDE theme for Interactive Feedback MCP

from __future__ import annotations

from typing import Dict


class EnhancedGlassmorphismTheme:
    """Adaptive sci-fi theme with system/light/dark support."""

    _active_mode = "dark"

    THEMES: Dict[str, Dict[str, str]] = {
        "dark": {
            "bg_app": "#070b16",
            "bg_gradient_top": "#0b1224",
            "bg_gradient_bottom": "#070b16",
            "bg_panel": "#0d1428",
            "bg_panel_alt": "#101a31",
            "bg_elevated": "#142240",
            "bg_input": "#0b1327",
            "bg_hover": "#17284b",
            "bg_soft": "rgba(102, 227, 255, 0.07)",
            "border": "#243a63",
            "border_soft": "rgba(120, 155, 220, 0.22)",
            "border_strong": "#33558d",
            "accent": "#66e3ff",
            "accent_hover": "#8aeeff",
            "accent_soft": "rgba(102, 227, 255, 0.16)",
            "accent_secondary": "#9b8cff",
            "success": "#78f0c9",
            "warning": "#ffd166",
            "danger": "#ff7aa2",
            "danger_hover": "rgba(255, 122, 162, 0.12)",
            "text_primary": "#d8e7ff",
            "text_secondary": "#a9bddf",
            "text_muted": "#7f96bf",
            "text_title": "#f2f7ff",
            "text_inverse": "#05101b",
            "surface_line": "rgba(102, 227, 255, 0.18)",
            "selection": "rgba(102, 227, 255, 0.18)",
            "button_primary": "#66e3ff",
            "button_primary_hover": "#7be8ff",
            "button_secondary": "#132241",
            "button_secondary_hover": "#192d54",
        },
        "light": {
            "bg_app": "#e7eef6",
            "bg_gradient_top": "#edf4fa",
            "bg_gradient_bottom": "#dde8f2",
            "bg_panel": "#eef4fb",
            "bg_panel_alt": "#f5f9fd",
            "bg_elevated": "#e6eef8",
            "bg_input": "#eff6fb",
            "bg_hover": "#e1edf9",
            "bg_soft": "rgba(31, 91, 191, 0.06)",
            "border": "#c8d8ea",
            "border_soft": "rgba(96, 130, 182, 0.26)",
            "border_strong": "#aabed7",
            "accent": "#1f5bbf",
            "accent_hover": "#184fa8",
            "accent_soft": "rgba(31, 91, 191, 0.10)",
            "accent_secondary": "#6d4aff",
            "success": "#14866d",
            "warning": "#d08a0f",
            "danger": "#c73c68",
            "danger_hover": "rgba(199, 60, 104, 0.08)",
            "text_primary": "#15314f",
            "text_secondary": "#35506e",
            "text_muted": "#6b819b",
            "text_title": "#0a2038",
            "text_inverse": "#ffffff",
            "surface_line": "rgba(109, 74, 255, 0.12)",
            "selection": "rgba(31, 91, 191, 0.12)",
            "button_primary": "#1f5bbf",
            "button_primary_hover": "#184fa8",
            "button_secondary": "#e8eff7",
            "button_secondary_hover": "#dce7f4",
        },
    }

    @classmethod
    def _colors(cls) -> Dict[str, str]:
        return cls.THEMES.get(cls._active_mode, cls.THEMES["dark"])

    @classmethod
    def set_theme_mode(cls, mode: str | None = None):
        mode = (mode or "system").lower()
        if mode == "system":
            mode = cls.detect_system_theme()
        cls._active_mode = "light" if mode == "light" else "dark"
        return cls._active_mode

    @classmethod
    def current_mode(cls) -> str:
        return cls._active_mode

    @classmethod
    def detect_system_theme(cls) -> str:
        try:
            from PySide6.QtGui import QGuiApplication, QPalette
            from PySide6.QtCore import Qt

            app = QGuiApplication.instance()
            if app and hasattr(app, "styleHints"):
                hints = app.styleHints()
                color_scheme = hints.colorScheme()
                if color_scheme == Qt.ColorScheme.Light:
                    return "light"
                if color_scheme == Qt.ColorScheme.Dark:
                    return "dark"
            if app:
                window_color = app.palette().color(QPalette.Window)
                return "dark" if window_color.lightness() < 140 else "light"
        except Exception:
            pass
        return "dark"

    @classmethod
    def get_main_window_style(cls):
        c = cls._colors()
        return f"""
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {c['bg_gradient_top']},
                stop:0.55 {c['bg_app']},
                stop:1 {c['bg_gradient_bottom']});
            border: 1px solid {c['border_soft']};
            border-radius: 20px;
            color: {c['text_primary']};
        }}
        QWidget {{
            background: transparent;
            color: {c['text_primary']};
            font-family: 'SF Pro Text', 'Inter', 'Segoe UI', 'PingFang SC', sans-serif;
        }}
        """

    @classmethod
    def get_panel_style(cls):
        c = cls._colors()
        return f"""
        QFrame {{
            background: {c['bg_panel']};
            border: 1px solid {c['border_soft']};
            border-radius: 18px;
        }}
        """

    @classmethod
    def get_section_shell_style(cls):
        return "QFrame { background: transparent; border: none; }"

    @classmethod
    def get_title_style(cls, color=None):
        c = cls._colors()
        color = color or c['text_title']
        return f"""
        QLabel {{
            color: {color};
            font-size: 15px;
            font-weight: 700;
            padding: 0 0 2px 0;
            border: none;
        }}
        """

    @classmethod
    def get_task_kicker_style(cls):
        c = cls._colors()
        return f"""
        QLabel {{
            color: {c['accent']};
            font-size: 15px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 0;
            border: none;
        }}
        """

    @classmethod
    def get_task_title_style(cls):
        c = cls._colors()
        return f"""
        QLabel {{
            color: {c['text_title']};
            font-size: 20px;
            font-weight: 800;
            padding: 0;
            border: none;
        }}
        """

    @classmethod
    def get_task_subtitle_style(cls):
        c = cls._colors()
        return f"""
        QLabel {{
            color: {c['text_secondary']};
            font-size: 12px;
            font-weight: 500;
            padding: 0;
            border: none;
        }}
        """

    @classmethod
    def get_text_browser_style(cls):
        c = cls._colors()
        return f"""
        QTextBrowser {{
            background: {c['bg_panel_alt']};
            color: {c['text_title']};
            border: 1px solid {c['border_soft']};
            border-top: 1px solid {c['surface_line']};
            border-radius: 14px;
            padding: 12px 14px;
            font-size: 14px;
            line-height: 1.7;
            selection-background-color: {c['selection']};
        }}
        QTextBrowser:focus {{
            border: 1px solid {c['accent_soft']};
        }}
        {cls._scrollbar_css()}
        """

    @classmethod
    def get_text_edit_style(cls):
        c = cls._colors()
        return f"""
        QTextEdit {{
            background: {c['bg_input']};
            color: {c['text_title']};
            border: 1px solid {c['border_soft']};
            border-top: 1px solid {c['surface_line']};
            border-radius: 14px;
            padding: 10px 12px;
            font-size: 15px;
            line-height: 1.65;
            selection-background-color: {c['selection']};
        }}
        QTextEdit:focus {{
            border: 1px solid {c['accent']};
            background: {c['bg_panel_alt']};
        }}
        {cls._scrollbar_css()}
        """

    @classmethod
    def get_checkbox_style(cls):
        c = cls._colors()
        return f"""
        QCheckBox {{
            color: {c['text_primary']};
            font-size: 12px;
            font-weight: 500;
            spacing: 8px;
            padding: 5px 0;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 5px;
            border: 1px solid {c['border_strong']};
            background: {c['bg_input']};
        }}
        QCheckBox::indicator:checked {{
            background: {c['accent']};
            border-color: {c['accent']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {c['accent']};
        }}
        """

    @classmethod
    def get_checkbox_frame_style(cls):
        c = cls._colors()
        return f"""
        QFrame {{
            background: {c['bg_elevated']};
            border: 1px solid {c['border_soft']};
            border-radius: 12px;
            padding: 0;
        }}
        QFrame:hover {{
            background: {c['bg_hover']};
            border: 1px solid {c['border']};
        }}
        """

    @classmethod
    def get_button_style(cls, button_type='primary'):
        c = cls._colors()
        if button_type == 'primary':
            bg = c['button_primary']
            fg = c['text_inverse']
            border = c['button_primary']
            hover = c['button_primary_hover']
        elif button_type == 'error':
            bg = c['button_secondary']
            fg = c['text_secondary']
            border = c['border']
            hover = c['button_secondary_hover']
        else:
            bg = c['bg_elevated']
            fg = c['text_primary']
            border = c['border']
            hover = c['bg_hover']
        return f"""
        QPushButton {{
            background: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 12px;
            padding: 9px 14px;
            font-size: 12px;
            font-weight: 700;
            min-width: 88px;
        }}
        QPushButton:hover {{
            background: {hover};
        }}
        """

    @classmethod
    def get_info_section_style(cls):
        c = cls._colors()
        return f"""
        QFrame {{
            background: {c['bg_panel_alt']};
            border: 1px solid {c['border_soft']};
            border-top: 1px solid {c['surface_line']};
            border-radius: 14px;
            padding: 8px;
        }}
        """

    @classmethod
    def get_label_style(cls, color=None, size='normal'):
        c = cls._colors()
        label_color = color or c['text_secondary']
        size_map = {'small': '10px', 'normal': '11px', 'large': '12px', 'title': '14px'}
        return f"QLabel {{ color: {label_color}; font-size: {size_map.get(size, '12px')}; font-weight: 500; padding: 0; }}"

    @classmethod
    def get_hint_label_style(cls):
        c = cls._colors()
        return f"color: {c['text_muted']}; font-size: 11px;"

    @classmethod
    def get_section_caption_style(cls):
        c = cls._colors()
        return f"color: {c['text_title']}; font-weight: 700; font-size: 12px;"

    @classmethod
    def get_meta_label_style(cls):
        c = cls._colors()
        return f"""
        color: {c['accent_secondary']};
        font-size: 10px;
        font-weight: 700;
        background-color: {c['accent_soft']};
        padding: 3px 6px;
        border-radius: 6px;
        min-width: 48px;
        max-width: 72px;
        """

    @classmethod
    def get_meta_value_style(cls, accent: str | None = None):
        c = cls._colors()
        accent = accent or c['accent']
        return f"""
        color: {c['text_primary']};
        font-size: 11px;
        font-weight: 500;
        background-color: {c['bg_elevated']};
        padding: 4px 8px;
        border-radius: 8px;
        border-left: 2px solid {accent};
        """

    @classmethod
    def get_attachment_container_style(cls):
        c = cls._colors()
        return f"QFrame {{ background: {c['bg_panel_alt']}; border: 1px solid {c['border_soft']}; border-radius: 12px; padding: 4px; }}"

    @classmethod
    def get_attachment_title_style(cls):
        c = cls._colors()
        return f"color: {c['text_secondary']}; font-weight: 600; font-size: 11px;"

    @classmethod
    def get_attachment_scroll_style(cls):
        c = cls._colors()
        return f"""
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:horizontal {{ height: 8px; background: {c['bg_soft']}; border-radius: 4px; }}
        QScrollBar::handle:horizontal {{ background: {c['border_strong']}; border-radius: 4px; min-width: 18px; }}
        QScrollBar::handle:horizontal:hover {{ background: {c['accent']}; }}
        """

    @classmethod
    def get_attachment_frame_style(cls):
        c = cls._colors()
        return f"QFrame {{ background: transparent; border: 1px solid {c['border']}; border-radius: 8px; padding: 1px; }} QFrame:hover {{ border: 1px solid {c['accent']}; }}"

    @classmethod
    def get_icon_button_style(cls):
        c = cls._colors()
        return f"""
        QPushButton {{
            background-color: {c['bg_panel_alt']};
            color: {c['text_primary']};
            border-radius: 10px;
            font-weight: bold;
            font-size: 12px;
            border: 1px solid {c['border']};
        }}
        QPushButton:hover {{
            background-color: {c['danger_hover']};
            border: 1px solid {c['danger']};
            color: {c['danger']};
        }}
        """

    @classmethod
    def _scrollbar_css(cls):
        c = cls._colors()
        return f"""
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
        QScrollBar::handle:vertical {{ background: {c['border_strong']}; border-radius: 5px; min-height: 26px; }}
        QScrollBar::handle:vertical:hover {{ background: {c['accent']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; height: 0; }}
        """
