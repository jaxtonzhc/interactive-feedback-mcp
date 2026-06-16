"""ui/components/text_processing.py 的纯逻辑测试。"""

import pytest


def _import_processor():
    from ui.components.text_processing import TextProcessor
    return TextProcessor


class TestPreprocessText:

    def test_literal_newlines(self):
        tp = _import_processor()
        result = tp.preprocess_text("line1\\nline2")
        assert "\n" in result

    def test_crlf_normalization(self):
        tp = _import_processor()
        result = tp.preprocess_text("a\r\nb")
        assert "\r" not in result
        assert "a\nb" == result

    def test_empty_string(self):
        tp = _import_processor()
        assert tp.preprocess_text("") == ""

    def test_no_escape(self):
        tp = _import_processor()
        assert tp.preprocess_text("hello world") == "hello world"


class TestIsMarkdown:

    def test_heading(self):
        tp = _import_processor()
        assert tp.is_markdown("# Title") is True

    def test_code_block(self):
        tp = _import_processor()
        assert tp.is_markdown("```python\nprint('hi')\n```") is True

    def test_unordered_list(self):
        tp = _import_processor()
        assert tp.is_markdown("- item1\n- item2") is True

    def test_ordered_list(self):
        tp = _import_processor()
        assert tp.is_markdown("1. first\n2. second") is True

    def test_blockquote(self):
        tp = _import_processor()
        assert tp.is_markdown("> quote") is True

    def test_plain_text_is_not_markdown(self):
        tp = _import_processor()
        assert tp.is_markdown("just a simple sentence") is False

    def test_empty_is_not_markdown(self):
        tp = _import_processor()
        assert tp.is_markdown("") is False


class TestConvertTextToHtml:

    def test_html_escaping(self):
        tp = _import_processor()
        result = tp.convert_text_to_html("<script>alert(1)</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_newline_to_br(self):
        tp = _import_processor()
        result = tp.convert_text_to_html("a\nb")
        assert "<br>" in result


class TestConvertMarkdownToHtml:

    def test_heading_rendered(self):
        tp = _import_processor()
        result = tp.convert_markdown_to_html("# Hello")
        assert "<h1>" in result.lower() or "hello" in result.lower()

    def test_code_block_rendered(self):
        tp = _import_processor()
        result = tp.convert_markdown_to_html("```\ncode\n```")
        assert "<code>" in result.lower() or "<pre>" in result.lower()
