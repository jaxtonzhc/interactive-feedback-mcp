"""server.py 中可独立测试的纯函数 / 工具逻辑。"""

import os
import json
import tempfile

import pytest


def _import_server():
    """延迟导入，避免在收集阶段触发 FastMCP 副作用。"""
    import server
    return server


class TestNormalizeFeedbackInputs:
    """_normalize_feedback_inputs 参数兼容层测试。"""

    def _call(self, **kw):
        srv = _import_server()
        defaults = dict(
            message=None, summary=None, question=None,
            predefined_options=None, predefinedOptions=None,
            project_path=None, project_directory=None,
        )
        defaults.update(kw)
        return srv._normalize_feedback_inputs(**defaults)

    def test_message_only(self):
        msg, opts, path = self._call(message="hello")
        assert msg == "hello"
        assert opts is None
        assert path is None

    def test_summary_fallback(self):
        msg, _, _ = self._call(summary="from summary")
        assert msg == "from summary"

    def test_message_and_question_merged(self):
        msg, _, _ = self._call(message="msg", question="q?")
        assert "msg" in msg
        assert "q?" in msg

    def test_predefined_options_takes_priority(self):
        _, opts, _ = self._call(predefined_options=["a", "b"])
        assert opts == ["a", "b"]

    def test_camel_case_fallback(self):
        _, opts, _ = self._call(predefinedOptions=["x"])
        assert opts == ["x"]

    def test_project_directory_fallback(self):
        _, _, path = self._call(project_directory="/tmp/proj")
        assert path == "/tmp/proj"

    def test_all_empty_returns_default_message(self):
        msg, _, _ = self._call()
        assert len(msg) > 0


class TestIsProjectDirectory:
    """_is_project_directory 项目目录识别。"""

    def test_nonexistent_path(self):
        srv = _import_server()
        assert srv._is_project_directory("/nonexistent_path_xyz") is False

    def test_directory_with_git(self, tmp_path):
        srv = _import_server()
        (tmp_path / ".git").mkdir()
        assert srv._is_project_directory(str(tmp_path)) is True

    def test_directory_with_pyproject(self, tmp_path):
        srv = _import_server()
        (tmp_path / "pyproject.toml").touch()
        assert srv._is_project_directory(str(tmp_path)) is True

    def test_empty_directory(self, tmp_path):
        srv = _import_server()
        assert srv._is_project_directory(str(tmp_path)) is False


class TestReadResultFile:
    """_read_result_file 结果文件解析。"""

    def test_none_input(self):
        srv = _import_server()
        assert srv._read_result_file(None) is None

    def test_missing_file(self):
        srv = _import_server()
        assert srv._read_result_file("/nonexistent.json") is None

    def test_empty_file(self, tmp_path):
        srv = _import_server()
        f = tmp_path / "empty.json"
        f.touch()
        assert srv._read_result_file(str(f)) is None

    def test_valid_json(self, tmp_path):
        srv = _import_server()
        f = tmp_path / "result.json"
        data = {"interactive_feedback": "test reply", "images": []}
        f.write_text(json.dumps(data), encoding="utf-8")
        result = srv._read_result_file(str(f))
        assert result == data

    def test_invalid_json(self, tmp_path):
        srv = _import_server()
        f = tmp_path / "bad.json"
        f.write_text("not json", encoding="utf-8")
        assert srv._read_result_file(str(f)) is None


class TestBuildHeartbeatMsg:
    """_build_heartbeat_msg 心跳消息构造。"""

    def test_contains_count_and_time(self):
        srv = _import_server()
        msg = srv._build_heartbeat_msg(3, 5.0)
        assert "5" in msg
        assert "3" in msg

    def test_different_counts_produce_different_messages(self):
        srv = _import_server()
        msgs = {srv._build_heartbeat_msg(i, 1.0) for i in range(5)}
        assert len(msgs) == 5


class TestFormatFeedbackResult:
    """_format_feedback_result 返回值格式化。"""

    def test_text_only(self):
        srv = _import_server()
        result = srv._format_feedback_result(
            {"interactive_feedback": "hello", "images": []}
        )
        assert isinstance(result, tuple)
        assert "hello" in result[0]

    def test_empty_feedback(self):
        srv = _import_server()
        result = srv._format_feedback_result(
            {"interactive_feedback": "", "images": []}
        )
        assert isinstance(result, tuple)
