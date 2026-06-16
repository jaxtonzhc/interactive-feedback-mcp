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
        
        # 获取 Pygments token 颜色，剥离所有 background 属性避免 QTextBrowser 全行背景
        raw_pygments = HtmlFormatter(style='monokai').get_style_defs('.highlight')
        import re as _re
        cleaned = _re.sub(r'\.highlight\s*\{[^}]*\}', '', raw_pygments)
        cleaned = _re.sub(r'background:\s*[^;]+;?', '', cleaned)
        cleaned = _re.sub(r'background-color:\s*[^;]+;?', '', cleaned)
        self.pygments_css = cleaned
    
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
        """浅色模式 CSS — QTextBrowser 兼容版"""
        return """
        body {
            font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
            background: transparent;
            color: #1a2a3a;
            line-height: 1.6;
            margin: 0;
            padding: 16px;
            font-size: 14px;
        }

        h1, h2, h3, h4, h5, h6 {
            margin-top: 20px;
            margin-bottom: 12px;
            font-weight: 700;
            padding: 6px 0 6px 14px;
            border-left: 4px solid #1565C0;
            color: #0d47a1;
        }
        h1 { font-size: 22px; border-left-color: #2E7D32; color: #1b5e20; }
        h2 { font-size: 19px; border-left-color: #1565C0; color: #0d47a1; }
        h3 { font-size: 17px; border-left-color: #E65100; color: #bf360c; }
        h4 { font-size: 15px; border-left-color: #6A1B9A; color: #4a148c; }
        h5 { font-size: 14px; padding: 4px 0 4px 12px; }
        h6 { font-size: 13px; padding: 4px 0 4px 12px; }

        p { margin: 12px 0; }

        strong, b { color: #b45309; font-weight: 700; }
        em, i { color: #2E7D32; font-style: italic; }

        .highlight {
            padding: 12px;
            margin: 12px 0;
            border-left: 4px solid #1565C0;
        }
        .highlight pre {
            margin: 0;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #263238;
        }
        code {
            padding: 1px 4px;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            color: #c62828;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            border: 1px solid #e0e0e0;
        }
        th, td {
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            font-weight: 700;
            color: #0d47a1;
            font-size: 14px;
            border-bottom: 2px solid rgba(21, 101, 192, 0.2);
        }

        blockquote {
            margin: 12px 0;
            padding: 8px 16px;
            border-left: 4px solid #7B1FA2;
            font-style: italic;
        }
        blockquote p { margin: 0; color: #4a148c; }

        ul, ol { margin: 12px 0; padding-left: 28px; }
        li { margin: 6px 0; padding-left: 4px; }

        a { color: #1565C0; text-decoration: underline; }

        .admonition { margin: 12px 0; padding: 12px; }
        .admonition.note { border-left: 4px solid #1565C0; }
        .admonition.warning { border-left: 4px solid #E65100; }
        .admonition.danger { border-left: 4px solid #C62828; }
        .admonition-title { font-weight: 700; margin-bottom: 8px; font-size: 15px; }

        hr { border: none; height: 1px; background-color: rgba(21, 101, 192, 0.2); margin: 24px 0; }
        .footnote { font-size: 12px; color: rgba(0, 0, 0, 0.5); padding: 6px 0; margin-top: 8px; }
        .highlight-box { border-left: 4px solid #E65100; padding: 12px; margin: 12px 0; }
        """

    def _get_dark_css(self) -> str:
        """深色模式 CSS — QTextBrowser 兼容版"""
        return """
        body {
            font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'SimHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
            background: transparent;
            color: #e0e8f0;
            line-height: 1.6;
            margin: 0;
            padding: 16px;
            font-size: 14px;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #64B5F6;
            margin-top: 20px;
            margin-bottom: 12px;
            font-weight: 700;
            padding: 6px 0 6px 14px;
            border-left: 4px solid #64B5F6;
        }
        h1 { font-size: 22px; border-left-color: #4CAF50; color: #81C784; }
        h2 { font-size: 19px; border-left-color: #2196F3; color: #64B5F6; }
        h3 { font-size: 17px; border-left-color: #FF9800; color: #FFB74D; }
        h4 { font-size: 15px; border-left-color: #9C27B0; color: #BA68C8; }
        h5 { font-size: 14px; padding: 4px 0 4px 12px; }
        h6 { font-size: 13px; padding: 4px 0 4px 12px; }

        p { margin: 12px 0; }

        strong, b { color: #FFD54F; font-weight: 700; }
        em, i { color: #81C784; font-style: italic; }

        .highlight {
            padding: 12px;
            margin: 12px 0;
            border-left: 4px solid #64B5F6;
        }
        .highlight pre {
            margin: 0;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #f8f8f2;
        }
        code {
            padding: 1px 4px;
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
            font-size: 13px;
            color: #FF8A80;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            border: 1px solid rgba(100, 181, 246, 0.25);
        }
        th, td {
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        th {
            font-weight: 700;
            color: #E3F2FD;
            font-size: 14px;
            border-bottom: 2px solid rgba(100, 181, 246, 0.35);
        }

        blockquote {
            margin: 12px 0;
            padding: 8px 16px;
            border-left: 4px solid #BA68C8;
            font-style: italic;
        }
        blockquote p { margin: 0; color: #F3E5F5; }

        ul, ol { margin: 12px 0; padding-left: 28px; }
        li { margin: 6px 0; padding-left: 4px; }

        a { color: #81C784; text-decoration: underline; }

        .admonition { margin: 12px 0; padding: 12px; }
        .admonition.note { border-left: 4px solid #2196F3; }
        .admonition.warning { border-left: 4px solid #FF9800; }
        .admonition.danger { border-left: 4px solid #F44336; }
        .admonition-title { font-weight: 700; margin-bottom: 8px; font-size: 15px; }

        hr { border: none; height: 1px; background-color: rgba(100, 181, 246, 0.3); margin: 24px 0; }
        .footnote { font-size: 12px; color: rgba(255, 255, 255, 0.6); padding: 6px 0; margin-top: 8px; }
        .highlight-box { border-left: 4px solid #FFC107; padding: 12px; margin: 12px 0; }
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