#!/usr/bin/env python3
"""
Enhanced Markdown Renderer for Interactive Feedback MCP
增强的Markdown渲染器 - 方案A实现
"""

import re
import hashlib
from typing import Dict, Optional
from urllib.parse import urlparse

try:
    import markdown
    from markdown.extensions import codehilite, fenced_code, tables, toc
    from pygments.formatters import HtmlFormatter
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.util import ClassNotFound
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("⚠️ python-markdown 或 pygments 未安装，使用基础渲染")

from PySide6.QtWidgets import QTextBrowser, QApplication
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

class EnhancedMarkdownRenderer:
    """增强的Markdown渲染器"""
    
    def __init__(self):
        self.cache = {}
        self.max_cache_size = 100
        
        if MARKDOWN_AVAILABLE:
            self._setup_markdown()
        else:
            self.md = None
    
    def _setup_markdown(self):
        """设置markdown渲染器"""
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',      # 代码高亮
                'fenced_code',     # 围栏代码块
                'tables',          # 表格支持
                'toc',             # 目录生成
                'admonition',      # 警告框
                'attr_list',       # 属性列表
                'def_list',        # 定义列表
                'footnotes',       # 脚注
                'nl2br',           # 换行转换
                'sane_lists',      # 智能列表
                'smarty',          # 智能标点
                'abbr',            # 缩写
                'meta',            # 元数据
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True,
                    'pygments_style': 'monokai',
                    'linenums': False,
                    'guess_lang': True
                },
                'toc': {
                    'permalink': True,
                    'permalink_title': '链接到此标题'
                }
            }
        )
        
        # 获取Pygments CSS样式
        self.pygments_css = HtmlFormatter(style='monokai').get_style_defs('.highlight')
    
    def render(self, text: str) -> str:
        """渲染markdown文本为HTML"""
        if not text:
            return ""
        
        # 检查缓存
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]
        
        if MARKDOWN_AVAILABLE and self.md:
            html = self._render_with_markdown(text)
        else:
            html = self._render_basic(text)
        
        # 添加到缓存
        if len(self.cache) >= self.max_cache_size:
            # 移除最旧的缓存项
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[text_hash] = html
        return html
    
    def _render_with_markdown(self, text: str) -> str:
        """使用python-markdown渲染"""
        try:
            # 🔧 增强emoji编码处理
            if isinstance(text, bytes):
                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError:
                    text = text.decode('utf-8', errors='ignore')
            elif not isinstance(text, str):
                text = str(text)
            
            # 清理乱码字符（但严格保留emoji）
            text = self._clean_garbled_text(text)
            
            # 清理标题中的非常规字符
            text = self._clean_title_characters(text)
            
            # 重置markdown实例
            self.md.reset()
            
            # 渲染markdown
            html_content = self.md.convert(text)
            
            # 🎯 确保HTML编码正确处理emoji
            if isinstance(html_content, bytes):
                try:
                    html_content = html_content.decode('utf-8')
                except UnicodeDecodeError:
                    html_content = html_content.decode('utf-8', errors='ignore')
            
            # 包装在完整的HTML中 - 增强emoji支持
            full_html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    {self._get_custom_css()}
                    {self.pygments_css}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            return full_html
            
        except Exception as e:
            print(f"⚠️ Markdown渲染失败: {e}")
            return self._render_basic(text)
    
    def _render_basic(self, text: str) -> str:
        """基础渲染（回退方案）"""
        # 简化编码处理 - 避免重复编码
        if isinstance(text, bytes):
            try:
                text = text.decode('utf-8')
            except UnicodeDecodeError:
                text = text.decode('utf-8', errors='ignore')
        elif not isinstance(text, str):
            text = str(text)
        
        # 清理乱码字符
        text = self._clean_garbled_text(text)
            
        # 简单的文本到HTML转换
        html = text.replace('\n', '<br>')
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        html = html.replace('*', '<em>').replace('*', '</em>')
        html = html.replace('`', '<code>').replace('`', '</code>')
        
        return f"""
        <html>
        <head>
            <meta charset="utf-8">
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <style>{self._get_custom_css()}</style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
    
    def _is_light_mode(self) -> bool:
        """检测当前是否为浅色模式"""
        try:
            from ..styles.enhanced_glassmorphism import EnhancedGlassmorphismTheme
            return EnhancedGlassmorphismTheme.current_mode() == "light"
        except Exception:
            return False

    def _get_custom_css(self) -> str:
        """获取自定义CSS样式 - 自适应亮/暗模式"""
        if self._is_light_mode():
            return self._get_light_css()
        return self._get_dark_css()

    def _get_light_css(self) -> str:
        """浅色模式 CSS"""
        return """
        body {
            font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
            background: transparent;
            color: #1a2a3a;
            line-height: 1.6;
            margin: 0;
            padding: 16px;
            font-size: 14px;
            font-variant-emoji: normal;
            text-rendering: optimizeLegibility;
            -webkit-font-feature-settings: "liga", "kern";
            font-feature-settings: "liga", "kern";
        }

        h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 700;
            position: relative;
            padding: 12px 20px;
            border-radius: 8px;
            border-left: 4px solid #1565C0;
            background: linear-gradient(135deg, rgba(21, 101, 192, 0.08), rgba(21, 101, 192, 0.03));
            color: #0d47a1;
        }

        h1 {
            font-size: 22px;
            background: linear-gradient(135deg, rgba(46, 125, 50, 0.10), rgba(46, 125, 50, 0.04));
            border-left: 4px solid #2E7D32;
            color: #1b5e20;
        }
        h2 {
            font-size: 19px;
            background: linear-gradient(135deg, rgba(21, 101, 192, 0.10), rgba(21, 101, 192, 0.04));
            border-left: 4px solid #1565C0;
            color: #0d47a1;
        }
        h3 {
            font-size: 17px;
            background: linear-gradient(135deg, rgba(230, 81, 0, 0.08), rgba(230, 81, 0, 0.03));
            border-left: 4px solid #E65100;
            color: #bf360c;
        }
        h4 {
            font-size: 15px;
            background: linear-gradient(135deg, rgba(106, 27, 154, 0.08), rgba(106, 27, 154, 0.03));
            border-left: 4px solid #6A1B9A;
            color: #4a148c;
        }
        h5 { font-size: 14px; padding: 8px 16px; }
        h6 { font-size: 13px; padding: 6px 12px; }

        p {
            margin: 12px 0;
            text-align: justify;
        }

        strong, b {
            color: #b45309;
            font-weight: 700;
            background: linear-gradient(135deg, rgba(180, 83, 9, 0.10), rgba(180, 83, 9, 0.04));
            padding: 2px 6px;
            border-radius: 4px;
        }

        em, i {
            color: #2E7D32;
            font-style: italic;
            background: linear-gradient(135deg, rgba(46, 125, 50, 0.08), rgba(46, 125, 50, 0.03));
            padding: 1px 4px;
            border-radius: 3px;
        }

        .highlight {
            background: #f5f5f5;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            border-left: 6px solid #1565C0;
            border: 1px solid #e0e0e0;
            overflow-x: auto;
            position: relative;
        }

        .highlight pre {
            margin: 0;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #263238;
        }

        code {
            background: rgba(211, 47, 47, 0.08);
            padding: 3px 8px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            color: #c62828;
            border: 1px solid rgba(211, 47, 47, 0.15);
            font-weight: 500;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #e0e0e0;
        }

        th, td {
            padding: 16px 20px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        th {
            background: linear-gradient(135deg, rgba(21, 101, 192, 0.12), rgba(21, 101, 192, 0.06));
            font-weight: 700;
            color: #0d47a1;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid rgba(21, 101, 192, 0.25);
        }

        tr:hover {
            background: rgba(21, 101, 192, 0.04);
        }

        tr:nth-child(even) {
            background: rgba(0, 0, 0, 0.02);
        }

        blockquote {
            margin: 20px 0;
            padding: 20px 24px;
            background: linear-gradient(135deg, rgba(106, 27, 154, 0.06), rgba(106, 27, 154, 0.02));
            border-left: 6px solid #7B1FA2;
            border-radius: 0 12px 12px 0;
            position: relative;
            font-style: italic;
        }

        blockquote p {
            margin: 0;
            color: #4a148c;
            font-weight: 500;
        }

        ul, ol {
            margin: 16px 0;
            padding-left: 28px;
        }

        li {
            margin: 8px 0;
            padding-left: 8px;
            position: relative;
        }

        ul li::before {
            content: "▸";
            color: #1565C0;
            font-weight: bold;
            position: absolute;
            left: -16px;
            font-size: 16px;
        }

        a {
            color: #1565C0;
            text-decoration: none;
            border-bottom: 2px solid rgba(21, 101, 192, 0.3);
            padding: 2px 4px;
            border-radius: 4px;
            background: linear-gradient(135deg, rgba(21, 101, 192, 0.06), rgba(21, 101, 192, 0.02));
        }

        a:hover {
            color: #0d47a1;
            border-bottom-color: #0d47a1;
            background: linear-gradient(135deg, rgba(21, 101, 192, 0.12), rgba(21, 101, 192, 0.06));
        }

        .admonition {
            margin: 20px 0;
            padding: 20px;
            border-radius: 12px;
            position: relative;
            border-top: 3px solid;
        }

        .admonition.note {
            background: rgba(21, 101, 192, 0.06);
            border-left: 6px solid #1565C0;
            border-top-color: #1565C0;
        }

        .admonition.warning {
            background: rgba(230, 81, 0, 0.06);
            border-left: 6px solid #E65100;
            border-top-color: #E65100;
        }

        .admonition.danger {
            background: rgba(198, 40, 40, 0.06);
            border-left: 6px solid #C62828;
            border-top-color: #C62828;
        }

        .admonition-title {
            font-weight: 700;
            margin-bottom: 12px;
            font-size: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        hr {
            border: none;
            height: 2px;
            background: linear-gradient(to right, transparent, rgba(21, 101, 192, 0.3), transparent);
            margin: 32px 0;
            border-radius: 1px;
        }

        .footnote {
            font-size: 12px;
            color: rgba(0, 0, 0, 0.55);
            background: rgba(0, 0, 0, 0.03);
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 16px;
        }

        .task-list-item {
            list-style: none;
            position: relative;
            padding-left: 32px;
        }

        .task-list-item input[type="checkbox"] {
            position: absolute;
            left: 0;
            top: 2px;
            width: 16px;
            height: 16px;
            accent-color: #2E7D32;
        }

        .highlight-box {
            background: linear-gradient(135deg, rgba(180, 83, 9, 0.08), rgba(180, 83, 9, 0.03));
            border: 2px solid rgba(180, 83, 9, 0.20);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }
        """

    def _get_dark_css(self) -> str:
        """深色模式 CSS（原有样式）"""
        return """
        body {
            font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
            background: transparent;
            color: #ffffff;
            line-height: 1.6;
            margin: 0;
            padding: 16px;
            font-size: 14px;
            font-variant-emoji: normal;
            text-rendering: optimizeLegibility;
            -webkit-font-feature-settings: "liga", "kern";
            font-feature-settings: "liga", "kern";
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #64B5F6;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 700;
            position: relative;
            padding: 12px 20px;
            background: linear-gradient(135deg, rgba(100, 181, 246, 0.15), rgba(33, 150, 243, 0.08));
            border-radius: 8px;
            border-left: 4px solid #64B5F6;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 8px rgba(100, 181, 246, 0.2);
        }
        
        h1 { 
            font-size: 22px; 
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(76, 175, 80, 0.1));
            border-left: 4px solid #4CAF50;
            color: #81C784;
            box-shadow: 0 3px 12px rgba(76, 175, 80, 0.3);
        }
        h2 { 
            font-size: 19px; 
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.18), rgba(33, 150, 243, 0.08));
            border-left: 4px solid #2196F3;
            color: #64B5F6;
        }
        h3 { 
            font-size: 17px; 
            background: linear-gradient(135deg, rgba(255, 152, 0, 0.15), rgba(255, 152, 0, 0.08));
            border-left: 4px solid #FF9800;
            color: #FFB74D;
        }
        h4 { 
            font-size: 15px; 
            background: linear-gradient(135deg, rgba(156, 39, 176, 0.15), rgba(156, 39, 176, 0.08));
            border-left: 4px solid #9C27B0;
            color: #BA68C8;
        }
        h5 { font-size: 14px; padding: 8px 16px; }
        h6 { font-size: 13px; padding: 6px 12px; }
        
        p:has-text(🎯), p:has-text(⚠️), p:has-text(🚨), p:has-text(💡), p:has-text(✅), p:has-text(❌) {
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.15), rgba(255, 193, 7, 0.05));
            border: 1px solid rgba(255, 193, 7, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            margin: 16px 0;
            position: relative;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 12px rgba(255, 193, 7, 0.2);
        }
        
        p {
            margin: 12px 0;
            text-align: justify;
        }
        
        strong, b {
            color: #FFD54F;
            font-weight: 700;
            background: linear-gradient(135deg, rgba(255, 213, 79, 0.2), rgba(255, 213, 79, 0.1));
            padding: 2px 6px;
            border-radius: 4px;
            text-shadow: 0 0 8px rgba(255, 213, 79, 0.3);
        }
        
        em, i {
            color: #81C784;
            font-style: italic;
            background: linear-gradient(135deg, rgba(129, 199, 132, 0.15), rgba(129, 199, 132, 0.05));
            padding: 1px 4px;
            border-radius: 3px;
        }
        
        p:contains('🎯') {
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.2), rgba(33, 150, 243, 0.1)) !important;
            border-left: 4px solid #2196F3 !important;
            border-radius: 0 8px 8px 0 !important;
            padding: 16px 20px !important;
            font-weight: 500;
            box-shadow: 0 4px 16px rgba(33, 150, 243, 0.25) !important;
        }
        
        p:contains('⚠️'), p:contains('🚨') {
            background: linear-gradient(135deg, rgba(255, 152, 0, 0.2), rgba(255, 152, 0, 0.1)) !important;
            border-left: 4px solid #FF9800 !important;
            border-radius: 0 8px 8px 0 !important;
            padding: 16px 20px !important;
            color: #FFE0B2;
            box-shadow: 0 4px 16px rgba(255, 152, 0, 0.25) !important;
        }
        
        p:contains('✅') {
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(76, 175, 80, 0.1)) !important;
            border-left: 4px solid #4CAF50 !important;
            border-radius: 0 8px 8px 0 !important;
            padding: 16px 20px !important;
            color: #C8E6C9;
            box-shadow: 0 4px 16px rgba(76, 175, 80, 0.25) !important;
        }
        
        p:contains('❌') {
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.2), rgba(244, 67, 54, 0.1)) !important;
            border-left: 4px solid #F44336 !important;
            border-radius: 0 8px 8px 0 !important;
            padding: 16px 20px !important;
            color: #FFCDD2;
            box-shadow: 0 4px 16px rgba(244, 67, 54, 0.25) !important;
        }
        
        p:contains('💡') {
            background: linear-gradient(135deg, rgba(255, 235, 59, 0.2), rgba(255, 235, 59, 0.1)) !important;
            border-left: 4px solid #FFEB3B !important;
            border-radius: 0 8px 8px 0 !important;
            padding: 16px 20px !important;
            color: #FFF9C4;
            box-shadow: 0 4px 16px rgba(255, 235, 59, 0.25) !important;
        }
        
        .highlight {
            background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.4));
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            border-left: 6px solid #64B5F6;
            border-top: 2px solid rgba(100, 181, 246, 0.3);
            backdrop-filter: blur(15px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(100, 181, 246, 0.2);
            overflow-x: auto;
            position: relative;
        }
        
        .highlight::before {
            content: "💻 代码";
            position: absolute;
            top: -8px;
            left: 16px;
            background: linear-gradient(135deg, #64B5F6, #2196F3);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .highlight pre {
            margin: 0;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #f8f8f2;
        }
        
        code {
            background: linear-gradient(135deg, rgba(255, 107, 107, 0.2), rgba(255, 107, 107, 0.1));
            padding: 3px 8px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            color: #FF8A80;
            border: 1px solid rgba(255, 107, 107, 0.3);
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(255, 107, 107, 0.15);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
            border-radius: 12px;
            overflow: hidden;
            backdrop-filter: blur(15px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(100, 181, 246, 0.2);
        }
        
        th, td {
            padding: 16px 20px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        th {
            background: linear-gradient(135deg, rgba(100, 181, 246, 0.3), rgba(33, 150, 243, 0.2));
            font-weight: 700;
            color: #E3F2FD;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid rgba(100, 181, 246, 0.4);
        }
        
        tr:hover {
            background: rgba(100, 181, 246, 0.1);
            transition: background 0.3s ease;
        }
        
        tr:nth-child(even) {
            background: rgba(255, 255, 255, 0.02);
        }
        
        blockquote {
            margin: 20px 0;
            padding: 20px 24px;
            background: linear-gradient(135deg, rgba(156, 39, 176, 0.15), rgba(156, 39, 176, 0.08));
            border-left: 6px solid #BA68C8;
            border-radius: 0 12px 12px 0;
            backdrop-filter: blur(15px);
            position: relative;
            font-style: italic;
            box-shadow: 0 6px 20px rgba(156, 39, 176, 0.2);
            border-top: 2px solid rgba(186, 104, 200, 0.3);
        }
        
        blockquote::before {
            content: "💬 引用";
            position: absolute;
            top: -10px;
            left: 20px;
            background: linear-gradient(135deg, #BA68C8, #9C27B0);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            font-style: normal;
        }
        
        blockquote p {
            margin: 0;
            color: #F3E5F5;
            font-weight: 500;
        }
        
        ul, ol {
            margin: 16px 0;
            padding-left: 28px;
        }
        
        li {
            margin: 8px 0;
            padding-left: 8px;
            position: relative;
        }
        
        ul li::before {
            content: "▸";
            color: #64B5F6;
            font-weight: bold;
            position: absolute;
            left: -16px;
            font-size: 16px;
        }
        
        a {
            color: #81C784;
            text-decoration: none;
            border-bottom: 2px solid rgba(129, 199, 132, 0.4);
            transition: all 0.3s ease;
            padding: 2px 4px;
            border-radius: 4px;
            background: linear-gradient(135deg, rgba(129, 199, 132, 0.1), rgba(129, 199, 132, 0.05));
        }
        
        a:hover {
            color: #A5D6A7;
            border-bottom-color: #A5D6A7;
            background: linear-gradient(135deg, rgba(165, 214, 167, 0.2), rgba(165, 214, 167, 0.1));
            box-shadow: 0 2px 8px rgba(129, 199, 132, 0.3);
        }
        
        .admonition {
            margin: 20px 0;
            padding: 20px;
            border-radius: 12px;
            backdrop-filter: blur(15px);
            position: relative;
            border-top: 3px solid;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        
        .admonition.note {
            background: linear-gradient(135deg, rgba(33, 150, 243, 0.15), rgba(33, 150, 243, 0.08));
            border-left: 6px solid #2196F3;
            border-top-color: #64B5F6;
            box-shadow: 0 6px 20px rgba(33, 150, 243, 0.25);
        }
        
        .admonition.warning {
            background: linear-gradient(135deg, rgba(255, 152, 0, 0.15), rgba(255, 152, 0, 0.08));
            border-left: 6px solid #FF9800;
            border-top-color: #FFB74D;
            box-shadow: 0 6px 20px rgba(255, 152, 0, 0.25);
        }
        
        .admonition.danger {
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.15), rgba(244, 67, 54, 0.08));
            border-left: 6px solid #F44336;
            border-top-color: #EF5350;
            box-shadow: 0 6px 20px rgba(244, 67, 54, 0.25);
        }
        
        .admonition-title {
            font-weight: 700;
            margin-bottom: 12px;
            font-size: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(to right, transparent, rgba(100, 181, 246, 0.6), transparent);
            margin: 32px 0;
            border-radius: 1px;
        }
        
        .footnote {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.7);
            background: rgba(255, 255, 255, 0.05);
            padding: 8px 12px;
            border-radius: 6px;
            margin-top: 16px;
        }
        
        .task-list-item {
            list-style: none;
            position: relative;
            padding-left: 32px;
        }
        
        .task-list-item input[type="checkbox"] {
            position: absolute;
            left: 0;
            top: 2px;
            width: 16px;
            height: 16px;
            accent-color: #4CAF50;
        }
        
        .highlight-box {
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
            border: 2px solid rgba(255, 193, 7, 0.4);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            backdrop-filter: blur(15px);
            box-shadow: 0 6px 20px rgba(255, 193, 7, 0.3);
        }
        """

    def _clean_garbled_text(self, text: str) -> str:
        """清理乱码字符，但保留所有有效Unicode字符"""
        import re
        
        # 强化乱码字符清理，包含特定的乱码符号
        replacements = {
            # 替换字符（菱形问号）
            r'[�]+': '',
            r'[\ufffd]+': '',
            # 特定的乱码符号（根据用户反馈的◇◇问题）
            r'[◇◆]+': '',
            r'[◇]+': '',
            r'[◆]+': '',
            # 控制字符（但保留换行、制表符、回车）
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]': '',
            # 移除NULL字符
            r'\x00': '',
            # 其他可能的特殊符号
            r'[\u2666\u25c7\u25c6]+': '',  # Unicode菱形符号
        }
        
        cleaned_text = text
        for pattern, replacement in replacements.items():
            cleaned_text = re.sub(pattern, replacement, cleaned_text)
        
        # 规范化空白字符（但保留所有换行）
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        # 限制连续空行为最多2个
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        
        return cleaned_text
    
    def _clean_title_characters(self, text: str) -> str:
        """清理标题中的非常规字符，保留中文、英文、数字、常用符号"""
        import re
        
        # 匹配markdown标题行
        def clean_title_line(match):
            title_prefix = match.group(1)  # ### 等标题标记
            title_content = match.group(2)  # 标题内容
            
            # 清理标题内容，保留中文、英文、数字、常用符号和emoji
            cleaned_content = re.sub(
                r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef'  # 中文字符范围
                r'a-zA-Z0-9\s'  # 英文字母、数字、空格
                r'\U0001f300-\U0001f9ff\u2600-\u26ff\u2700-\u27bf'  # emoji
                r'!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?/~`'  # 常用符号
                r'（）【】《》""''：；，。？！—…·'  # 中文标点
                r']+', '', title_content
            )
            
            # 移除多余空格
            cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
            
            return f"{title_prefix}{cleaned_content}"
        
        # 处理所有级别的markdown标题
        text = re.sub(r'^(#{1,6}\s*)(.*)$', clean_title_line, text, flags=re.MULTILINE)
        
        return text

class EnhancedTextBrowser(QTextBrowser):
    """增强的文本浏览器，支持高级markdown渲染"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.renderer = EnhancedMarkdownRenderer()
        
        # 启用链接处理
        self.setOpenExternalLinks(True)  # 允许外部链接直接打开
        self.setOpenLinks(True)  # 启用链接打开功能
        self.anchorClicked.connect(self._handle_link_click)
        
        # 设置基础样式，包含中文字体和emoji支持
        self.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                border: none;
                selection-background-color: rgba(33, 150, 243, 0.3);
                font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
            }
        """)
    
    def set_markdown_content(self, markdown_text: str):
        """设置markdown内容"""
        html = self.renderer.render(markdown_text)
        self.setHtml(html)
    
    def _handle_link_click(self, url: QUrl):
        """处理链接点击"""
        url_string = url.toString()
        print(f"🔗 链接点击: {url_string}")  # 调试信息
        
        try:
            if url.scheme() in ['http', 'https']:
                # 外部链接用浏览器打开
                print(f"🌐 打开外部链接: {url_string}")
                QDesktopServices.openUrl(url)
                return True
            elif url.scheme() == 'file':
                # 本地文件链接
                print(f"📁 打开本地文件: {url_string}")
                QDesktopServices.openUrl(url)
                return True
            elif url.scheme() == 'mailto':
                # 邮件链接
                print(f"📧 打开邮件: {url_string}")
                QDesktopServices.openUrl(url)
                return True
            elif url_string.startswith('#'):
                # 内部锚点链接
                fragment = url_string.lstrip('#')
                print(f"⚓ 跳转到锚点: {fragment}")
                self.scrollToAnchor(fragment)
                return True
            else:
                # 尝试作为HTTP链接处理（可能缺少协议）
                if '.' in url_string and not url_string.startswith('#'):
                    full_url = f"https://{url_string}" if not url_string.startswith(('http://', 'https://')) else url_string
                    print(f"🔗 补全协议后打开: {full_url}")
                    QDesktopServices.openUrl(QUrl(full_url))
                    return True
                else:
                    print(f"❓ 未知链接类型: {url_string}")
                    return False
        except Exception as e:
            print(f"❌ 链接处理错误: {e}")
            return False
    
    def get_renderer_info(self) -> Dict[str, any]:
        """获取渲染器信息"""
        return {
            'markdown_available': MARKDOWN_AVAILABLE,
            'cache_size': len(self.renderer.cache),
            'max_cache_size': self.renderer.max_cache_size,
            'extensions': [
                'codehilite', 'fenced_code', 'tables', 'toc',
                'admonition', 'attr_list', 'def_list', 'footnotes',
                'nl2br', 'sane_lists', 'smarty', 'abbr', 'meta'
            ] if MARKDOWN_AVAILABLE else []
        } 