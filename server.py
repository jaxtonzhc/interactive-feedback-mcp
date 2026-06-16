# -*- coding: utf-8 -*-
# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import signal
import time
import tempfile
import subprocess
import base64
import argparse
import asyncio
from datetime import datetime
from typing import Tuple, List, Optional

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from pydantic import Field

# 解析命令行参数
def parse_command_line_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Interactive Feedback MCP Server')
    parser.add_argument('--caller-source',
                       choices=['cursor', 'augment', 'claude', 'vscode', 'custom'],
                       default=None,
                       help='调用来源标识 (cursor|augment|claude|vscode|custom)')
    parser.add_argument('--debug',
                       action='store_true',
                       help='启用调试模式')
    parser.add_argument('--log-level',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default=None,
                       help='设置日志级别')

    # 只解析已知参数，忽略其他参数（如 FastMCP 的参数）
    args, unknown = parser.parse_known_args()
    return args

# 解析命令行参数
cmd_args = parse_command_line_args()

# 设置全局调用来源（优先级：命令行参数 > 环境变量 > 默认值）
GLOBAL_CALLER_SOURCE = (
    cmd_args.caller_source or
    os.environ.get('MCP_FEEDBACK_CALLER_SOURCE', 'cursor')
)

# 设置调试模式
if cmd_args.debug:
    os.environ['MCP_FEEDBACK_DEBUG'] = 'true'

# 设置日志级别
if cmd_args.log_level:
    os.environ['MCP_FEEDBACK_LOG_LEVEL'] = cmd_args.log_level

# 导入日志系统
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui.utils.logging_system import init_logging, get_logger, log_performance, log_project_context

# 初始化日志系统
logging_manager = init_logging({
    'level': os.environ.get('MCP_FEEDBACK_LOG_LEVEL', 'INFO'),
    'console_enabled': True,
    'console_level': 'WARNING',  # 控制台只显示警告和错误
    'performance_enabled': True,
    'project_context_enabled': True
})

# FastMCP server initialization
mcp = FastMCP("Interactive Feedback MCP")

# 获取主日志记录器
logger = get_logger('mcp_server')

# 记录启动参数
logger.info(f"MCP服务器启动 - 调用来源: {GLOBAL_CALLER_SOURCE}")
if cmd_args.caller_source:
    logger.info(f"通过命令行参数设置调用来源: {cmd_args.caller_source}")
elif os.environ.get('MCP_FEEDBACK_CALLER_SOURCE'):
    logger.info(f"通过环境变量设置调用来源: {os.environ.get('MCP_FEEDBACK_CALLER_SOURCE')}")
else:
    logger.info("使用默认调用来源: cursor")

# ==================== 心跳 & 防重复弹窗状态 ====================
# 参考 keunsy/cursor-feedback-gate 的设计：
# Cursor IDE 的 MCP 工具调用有 ~1小时硬性超时，连续2次超时后 Agent 会彻底放弃。
# 通过定期返回心跳消息，让 Agent 重新调用工具来继续等待，避免超时。
# 同时通过跟踪活跃的 UI 进程，防止重复弹窗。

_active_process: asyncio.subprocess.Process | None = None
_active_output_file: str | None = None
_heartbeat_count: int = 0
_process_start_time: float = 0
_last_response_time: float = 0

_WAIT_SECONDS = int(os.environ.get("MCP_FEEDBACK_WAIT_SECONDS", "600"))
_MAX_TOTAL_SECONDS = 259200  # 72h
_COOLDOWN_SECONDS = 2.0

_HEARTBEAT_PREAMBLES = [
    "[WAITING] 用户尚未回复。",
    "[WAITING] 仍在等待用户反馈。",
    "[WAITING] 请继续等待，用户可能正在思考。",
    "[WAITING] 反馈窗口仍然打开中。",
    "[WAITING] 用户暂未回复，请再次调用此工具继续等待。",
]


def _build_heartbeat_msg(count: int, elapsed_min: float) -> str:
    """构造随机变化的心跳消息，避免 Agent 看到重复文本后放弃等待。"""
    preamble = _HEARTBEAT_PREAMBLES[count % len(_HEARTBEAT_PREAMBLES)]
    return (
        f"{preamble} "
        f"(已等待约 {elapsed_min:.0f} 分钟，第 {count} 次心跳) "
        f"请立即再次调用 interactive_feedback 工具继续等待用户回复。"
    )


def _clear_active_state():
    """清除所有活跃 UI 进程状态。"""
    global _active_process, _active_output_file, _heartbeat_count, _process_start_time
    if _active_process is not None and _active_process.returncode is None:
        try:
            _active_process.terminate()
        except Exception:
            pass
    _active_process = None
    if _active_output_file and os.path.exists(_active_output_file):
        try:
            os.unlink(_active_output_file)
        except Exception:
            pass
    _active_output_file = None
    _heartbeat_count = 0
    _process_start_time = 0


def _read_result_file(output_file: str | None) -> dict | None:
    """尝试从输出文件读取反馈结果。"""
    if not output_file or not os.path.exists(output_file):
        return None
    if os.path.getsize(output_file) == 0:
        return None
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        if isinstance(result, dict):
            return result
    except Exception:
        pass
    return None

# ==================== 心跳 & 防重复弹窗状态 END ====================


def _detect_caller_project_context():
    """检测调用方项目上下文信息"""
    with log_performance("detect_caller_project_context", "project_detection"):
        try:        
            # 尝试获取调用方工作目录
            caller_cwd = None
            
            # 方法1: 优先从环境变量获取（通常是最可靠的）
            env_cwd = os.environ.get('PWD')
            if env_cwd and os.path.exists(env_cwd) and _is_project_directory(env_cwd):
                caller_cwd = env_cwd
                logger.info(f"从PWD环境变量检测到项目: {env_cwd}")
            
            # 方法2: 使用当前工作目录
            if not caller_cwd:
                current_cwd = os.getcwd()
                script_dir = os.path.dirname(os.path.abspath(__file__))
                
                # 如果当前目录不是MCP服务器目录，且是有效项目目录
                if current_cwd != script_dir and _is_project_directory(current_cwd):
                    caller_cwd = current_cwd
                    logger.info(f"从当前工作目录检测到项目: {current_cwd}")
                # 即使是同一个目录，如果是有效项目目录也使用
                elif _is_project_directory(current_cwd):
                    caller_cwd = current_cwd
                    logger.info(f"使用当前目录作为项目: {current_cwd}")
            
            # 方法3: 尝试使用psutil从父进程获取
            if not caller_cwd:
                try:
                    import psutil
                    current_process = psutil.Process()
                    parent_process = current_process.parent()
                    if parent_process and hasattr(parent_process, 'cwd'):
                        parent_cwd = parent_process.cwd()
                        if _is_project_directory(parent_cwd):
                            caller_cwd = parent_cwd
                            logger.info(f"从父进程检测到项目: {parent_cwd}")
                except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
                    logger.debug(f"父进程检测失败: {e}")
            
            # 方法4: 回退到当前目录
            if not caller_cwd:
                caller_cwd = os.getcwd()
                logger.info(f"使用当前目录作为回退: {caller_cwd}")
            
            # 获取项目基本信息
            project_name = os.path.basename(caller_cwd)
            is_detected = _is_project_directory(caller_cwd)
            
            result = {
                'cwd': caller_cwd,
                'name': project_name,
                'is_detected': is_detected
            }
            
            logger.info(f"项目检测完成: 项目={project_name}, 路径={caller_cwd}, 有效={is_detected}")
            
            # 记录项目上下文
            log_project_context("project_detection", result)
            
            return result
                
        except Exception as e:
            logger.error(f"项目检测异常: {e}")
            fallback_cwd = os.getcwd()
            result = {
                'cwd': fallback_cwd,
                'name': os.path.basename(fallback_cwd),
                'is_detected': False
            }
            
            # 记录错误上下文
            log_project_context("project_detection_error", {
                'error': str(e),
                'fallback': result
            })
            
            return result

def _is_project_directory(path):
    """判断是否为项目目录"""
    if not os.path.exists(path):
        return False
    
    # 检查常见的项目标识文件
    project_indicators = [
        '.git', 'package.json', 'requirements.txt', 'pyproject.toml',
        'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
        '.gitignore', 'README.md', 'README.rst', '.cursorrules'
    ]
    
    for indicator in project_indicators:
        if os.path.exists(os.path.join(path, indicator)):
            return True
    
    return False

def _get_caller_git_info(project_dir):
    """获取调用方项目的Git信息"""
    try:
        git_commands = [
            (['git', 'branch', '--show-current'], 'branch'),
            (['git', 'status', '--porcelain'], 'status'),
            (['git', 'log', '-1', '--pretty=format:%s'], 'last_commit'),
            (['git', 'rev-parse', '--is-inside-work-tree'], 'is_git_repo')
        ]
        
        git_info = {}
        for cmd, key in git_commands:
            try:
                result = subprocess.run(cmd, cwd=project_dir,
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    git_info[key] = result.stdout.strip()
                else:
                    git_info[key] = ""
            except:
                git_info[key] = ""
        
        # 处理状态信息
        status_output = git_info.get('status', '')
        modified_files = len(status_output.split('\n')) if status_output.strip() else 0
        
        return {
            'branch': git_info.get('branch', 'unknown') or 'unknown',
            'modified_files': modified_files,
            'last_commit': git_info.get('last_commit', 'No commits') or 'No commits',
            'is_git_repo': git_info.get('is_git_repo') == 'true'
        }
    except:
        return {
            'branch': 'unknown',
            'modified_files': 0,
            'last_commit': 'unknown',
            'is_git_repo': False
        }

def _kill_feedback_process(process: subprocess.Popen) -> None:
    """尽量彻底清理反馈UI进程"""
    try:
        if process.poll() is not None:
            return

        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=2)
                return
            except Exception:
                pass

        process.terminate()
        process.wait(timeout=2)
    except Exception:
        try:
            if os.name == 'posix':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
        except Exception:
            pass


async def _kill_feedback_process_async(process: asyncio.subprocess.Process) -> None:
    """异步清理反馈UI进程，避免被取消的工具调用留下孤儿窗口。"""
    try:
        if process.returncode is not None:
            return

        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGTERM)
                await asyncio.wait_for(process.wait(), timeout=2)
                return
            except Exception:
                pass

        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=2)
    except Exception:
        try:
            if os.name == 'posix':
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            await asyncio.wait_for(process.wait(), timeout=2)
        except Exception:
            pass


def _normalize_feedback_inputs(
    message: Optional[str],
    summary: Optional[str],
    question: Optional[str],
    predefined_options: Optional[list],
    predefinedOptions: Optional[list],
    project_path: Optional[str],
    project_directory: Optional[str],
) -> tuple[str, Optional[list], Optional[str]]:
    """兼容旧版规则/提示词生成的参数名，避免 Cursor 模型调用旧 schema 时报错。"""
    message_parts = []
    for value in (message, summary, question):
        if isinstance(value, str) and value.strip():
            text = value.strip()
            if text not in message_parts:
                message_parts.append(text)

    normalized_message = "\n\n".join(message_parts) if message_parts else "请提供反馈。"
    normalized_options = predefined_options if isinstance(predefined_options, list) else predefinedOptions
    if not isinstance(normalized_options, list):
        normalized_options = None

    normalized_project_path = project_path if isinstance(project_path, str) and project_path.strip() else None
    if normalized_project_path is None and isinstance(project_directory, str) and project_directory.strip():
        normalized_project_path = project_directory

    return normalized_message, normalized_options, normalized_project_path


def launch_feedback_ui(
    summary: str, 
    predefinedOptions: list[str] | None = None,
    project_path: str | None = None,
    project_name: str | None = None,
    git_branch: str | None = None,
    task_title: str | None = None,
    priority: int = 3,
    category: str = "general",
    context_data: dict | None = None
) -> dict[str, str]:
    with log_performance("launch_feedback_ui", "ui_launch", 
                        summary_length=len(summary), 
                        options_count=len(predefinedOptions) if predefinedOptions else 0):
        
        # 使用全局调用源信息（已在启动时确定优先级）
        caller_source = GLOBAL_CALLER_SOURCE
        logger.info(f"启动反馈UI: 优先级={priority}, 类别={category}, 调用源={caller_source}")
        
        # Create a temporary file for the feedback result
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_file = tmp.name

        process: subprocess.Popen | None = None
        timeout_env = os.environ.get('MCP_FEEDBACK_UI_TIMEOUT_SECONDS', '').strip()
        ui_timeout_seconds = int(timeout_env) if timeout_env else 0

        try:
            # 检测调用方项目上下文
            caller_context = _detect_caller_project_context()
            
            # 使用传入的参数覆盖自动检测的值
            caller_cwd = project_path or caller_context['cwd']
            effective_project_name = project_name or caller_context['name']
            
            logger.info(f"使用项目路径: {caller_cwd}, 项目名称: {effective_project_name}")
            
            # 获取调用方Git信息
            caller_git_info = _get_caller_git_info(caller_cwd)
            effective_git_branch = git_branch or caller_git_info['branch']
            
            # Get the path to enhanced_feedback_ui.py relative to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            feedback_ui_path = os.path.join(script_dir, "enhanced_feedback_ui.py")

            # 准备环境变量，传递调用方项目上下文
            env = os.environ.copy()
            env['MCP_CALLER_CWD'] = caller_cwd
            env['MCP_CALLER_PROJECT_NAME'] = effective_project_name
            env['MCP_CALLER_IS_DETECTED'] = str(caller_context['is_detected'])
            env['MCP_CALLER_GIT_BRANCH'] = effective_git_branch
            env['MCP_CALLER_GIT_MODIFIED_FILES'] = str(caller_git_info['modified_files'])
            env['MCP_CALLER_GIT_LAST_COMMIT'] = caller_git_info['last_commit']
            env['MCP_CALLER_IS_GIT_REPO'] = str(caller_git_info['is_git_repo'])
            
            # 添加新的扩展参数
            env['MCP_FEEDBACK_PRIORITY'] = str(priority)
            env['MCP_FEEDBACK_CATEGORY'] = category
            env['MCP_FEEDBACK_CALLER_SOURCE'] = caller_source
            
            # 添加额外的上下文数据
            if context_data:
                env['MCP_FEEDBACK_CONTEXT_DATA'] = json.dumps(context_data, ensure_ascii=False)

            # Run feedback_ui.py as a separate process
            # NOTE: There appears to be a bug in uv, so we need
            # to pass a bunch of special flags to make this work
            args = [
                sys.executable,
                "-u",
                feedback_ui_path,
                "--prompt", summary,
                "--output-file", output_file,
                "--predefined-options", "|||".join(predefinedOptions) if predefinedOptions else "",
                "--task-title", task_title or summary,
            ]
            
            timeout_desc = f"{ui_timeout_seconds}s" if ui_timeout_seconds > 0 else "disabled"
            logger.info(f"启动UI进程: {' '.join(args[:3])}..., timeout={timeout_desc}")
            
            popen_kwargs = dict(
                args=args,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
                env=env,
            )
            if os.name == 'posix':
                popen_kwargs['start_new_session'] = True

            process = subprocess.Popen(**popen_kwargs)

            try:
                if ui_timeout_seconds > 0:
                    return_code = process.wait(timeout=ui_timeout_seconds)
                else:
                    return_code = process.wait()
            except subprocess.TimeoutExpired:
                logger.error(f"UI进程超时，准备清理，pid={process.pid}, timeout={ui_timeout_seconds}s")
                _kill_feedback_process(process)
                raise TimeoutError(f"Feedback UI timed out after {ui_timeout_seconds} seconds")
            finally:
                if process and process.poll() is None:
                    _kill_feedback_process(process)

            if return_code != 0:
                logger.error(f"UI进程异常退出，返回码: {return_code}")
                raise Exception(f"Failed to launch feedback UI: {return_code}")

            logger.info("UI进程执行完成，读取结果文件")

            if not os.path.exists(output_file):
                raise FileNotFoundError("Feedback UI finished but output file was not created")

            if os.path.getsize(output_file) == 0:
                raise ValueError("Feedback UI finished but output file is empty")
            
            # Read the result from the temporary file
            with open(output_file, 'r', encoding='utf-8') as f:
                ui_result = json.load(f)

            if not isinstance(ui_result, dict):
                raise ValueError("Feedback UI returned invalid JSON payload")

            logger.info(f"UI反馈结果: {len(ui_result.get('interactive_feedback', ''))} 字符")
            return ui_result
            
        except Exception as e:
            logger.error(f"UI启动失败: {str(e)}")
            if process and process.poll() is None:
                _kill_feedback_process(process)
            raise e
        finally:
            if os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except Exception as cleanup_error:
                    logger.warning(f"清理输出文件失败: {cleanup_error}")


async def launch_feedback_ui_async(
    summary: str,
    predefinedOptions: list[str] | None = None,
    project_path: str | None = None,
    project_name: str | None = None,
    git_branch: str | None = None,
    task_title: str | None = None,
    priority: int = 3,
    category: str = "general",
    context_data: dict | None = None
) -> dict[str, str]:
    with log_performance("launch_feedback_ui", "ui_launch",
                        summary_length=len(summary),
                        options_count=len(predefinedOptions) if predefinedOptions else 0):

        caller_source = GLOBAL_CALLER_SOURCE
        logger.info(f"启动反馈UI: 优先级={priority}, 类别={category}, 调用源={caller_source}")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            output_file = tmp.name

        process: asyncio.subprocess.Process | None = None
        timeout_env = os.environ.get('MCP_FEEDBACK_UI_TIMEOUT_SECONDS', '').strip()
        ui_timeout_seconds = int(timeout_env) if timeout_env else 0

        try:
            caller_context = _detect_caller_project_context()

            caller_cwd = project_path or caller_context['cwd']
            effective_project_name = project_name or caller_context['name']

            logger.info(f"使用项目路径: {caller_cwd}, 项目名称: {effective_project_name}")

            caller_git_info = _get_caller_git_info(caller_cwd)
            effective_git_branch = git_branch or caller_git_info['branch']

            script_dir = os.path.dirname(os.path.abspath(__file__))
            feedback_ui_path = os.path.join(script_dir, "enhanced_feedback_ui.py")

            env = os.environ.copy()
            env['MCP_CALLER_CWD'] = caller_cwd
            env['MCP_CALLER_PROJECT_NAME'] = effective_project_name
            env['MCP_CALLER_IS_DETECTED'] = str(caller_context['is_detected'])
            env['MCP_CALLER_GIT_BRANCH'] = effective_git_branch
            env['MCP_CALLER_GIT_MODIFIED_FILES'] = str(caller_git_info['modified_files'])
            env['MCP_CALLER_GIT_LAST_COMMIT'] = caller_git_info['last_commit']
            env['MCP_CALLER_IS_GIT_REPO'] = str(caller_git_info['is_git_repo'])
            env['MCP_FEEDBACK_PRIORITY'] = str(priority)
            env['MCP_FEEDBACK_CATEGORY'] = category
            env['MCP_FEEDBACK_CALLER_SOURCE'] = caller_source

            if context_data:
                env['MCP_FEEDBACK_CONTEXT_DATA'] = json.dumps(context_data, ensure_ascii=False)

            args = [
                sys.executable,
                "-u",
                feedback_ui_path,
                "--prompt", summary,
                "--output-file", output_file,
                "--predefined-options", "|||".join(predefinedOptions) if predefinedOptions else "",
                "--task-title", task_title or summary,
            ]

            timeout_desc = f"{ui_timeout_seconds}s" if ui_timeout_seconds > 0 else "disabled"
            logger.info(f"启动UI进程: {' '.join(args[:3])}..., timeout={timeout_desc}")

            popen_kwargs = dict(
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                env=env,
            )
            if os.name == 'posix':
                popen_kwargs['start_new_session'] = True

            process = await asyncio.create_subprocess_exec(*args, **popen_kwargs)

            try:
                if ui_timeout_seconds > 0:
                    return_code = await asyncio.wait_for(process.wait(), timeout=ui_timeout_seconds)
                else:
                    return_code = await process.wait()
            except asyncio.TimeoutError:
                logger.error(f"UI进程超时，准备清理，pid={process.pid}, timeout={ui_timeout_seconds}s")
                await _kill_feedback_process_async(process)
                raise TimeoutError(f"Feedback UI timed out after {ui_timeout_seconds} seconds")
            except asyncio.CancelledError:
                logger.warning(f"MCP工具调用被取消，准备清理UI进程，pid={process.pid}")
                await _kill_feedback_process_async(process)
                raise
            finally:
                if process and process.returncode is None:
                    await _kill_feedback_process_async(process)

            if return_code != 0:
                logger.error(f"UI进程异常退出，返回码: {return_code}")
                raise Exception(f"Failed to launch feedback UI: {return_code}")

            logger.info("UI进程执行完成，读取结果文件")

            if not os.path.exists(output_file):
                raise FileNotFoundError("Feedback UI finished but output file was not created")

            if os.path.getsize(output_file) == 0:
                raise ValueError("Feedback UI finished but output file is empty")

            with open(output_file, 'r', encoding='utf-8') as f:
                ui_result = json.load(f)

            if not isinstance(ui_result, dict):
                raise ValueError("Feedback UI returned invalid JSON payload")

            logger.info(f"UI反馈结果: {len(ui_result.get('interactive_feedback', ''))} 字符")
            return ui_result

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"UI启动失败: {str(e)}")
            if process and process.returncode is None:
                await _kill_feedback_process_async(process)
            raise e
        finally:
            if os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except Exception as cleanup_error:
                    logger.warning(f"清理输出文件失败: {cleanup_error}")

async def _spawn_feedback_ui_process(
    summary: str,
    predefinedOptions: list[str] | None = None,
    project_path: str | None = None,
    project_name: str | None = None,
    git_branch: str | None = None,
    task_title: str | None = None,
    priority: int = 3,
    category: str = "general",
    context_data: dict | None = None,
) -> tuple[asyncio.subprocess.Process, str]:
    """启动反馈 UI 子进程，返回 (process, output_file)，不等待进程结束。"""
    caller_source = GLOBAL_CALLER_SOURCE

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    caller_context = _detect_caller_project_context()
    caller_cwd = project_path or caller_context['cwd']
    effective_project_name = project_name or caller_context['name']
    caller_git_info = _get_caller_git_info(caller_cwd)
    effective_git_branch = git_branch or caller_git_info['branch']

    script_dir = os.path.dirname(os.path.abspath(__file__))
    feedback_ui_path = os.path.join(script_dir, "enhanced_feedback_ui.py")

    env = os.environ.copy()
    env['MCP_CALLER_CWD'] = caller_cwd
    env['MCP_CALLER_PROJECT_NAME'] = effective_project_name
    env['MCP_CALLER_IS_DETECTED'] = str(caller_context['is_detected'])
    env['MCP_CALLER_GIT_BRANCH'] = effective_git_branch
    env['MCP_CALLER_GIT_MODIFIED_FILES'] = str(caller_git_info['modified_files'])
    env['MCP_CALLER_GIT_LAST_COMMIT'] = caller_git_info['last_commit']
    env['MCP_CALLER_IS_GIT_REPO'] = str(caller_git_info['is_git_repo'])
    env['MCP_FEEDBACK_PRIORITY'] = str(priority)
    env['MCP_FEEDBACK_CATEGORY'] = category
    env['MCP_FEEDBACK_CALLER_SOURCE'] = caller_source

    if context_data:
        env['MCP_FEEDBACK_CONTEXT_DATA'] = json.dumps(context_data, ensure_ascii=False)

    args = [
        sys.executable, "-u", feedback_ui_path,
        "--prompt", summary,
        "--output-file", output_file,
        "--predefined-options", "|||".join(predefinedOptions) if predefinedOptions else "",
        "--task-title", task_title or summary,
    ]

    popen_kwargs = dict(
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        env=env,
    )
    if os.name == 'posix':
        popen_kwargs['start_new_session'] = True

    process = await asyncio.create_subprocess_exec(*args, **popen_kwargs)
    logger.info(f"🚀 反馈UI进程已启动 pid={process.pid}")
    return process, output_file


def _format_feedback_result(result_dict: dict) -> str | tuple:
    """格式化反馈结果，附加调用来源和图片信息。"""
    txt: str = result_dict.get("interactive_feedback", "").strip()
    images_data = result_dict.get("images", [])
    img_b64_list: list[str] = images_data if isinstance(images_data, list) else []

    caller_icons = {
        'cursor': '🖱️', 'augment': '🚀', 'claude': '🤖',
        'vscode': '💻', 'custom': '⚙️'
    }
    caller_icon = caller_icons.get(GLOBAL_CALLER_SOURCE, '❓')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    caller_source_info = f"\n\n{caller_icon} **调用来源**: {GLOBAL_CALLER_SOURCE.upper()} | ⏰ {timestamp}"

    if txt:
        txt += caller_source_info
    else:
        txt = f"✅ 反馈已收到{caller_source_info}"

    if GLOBAL_CALLER_SOURCE == "augment" and img_b64_list:
        txt += f"\n\n📷 检测到 {len(img_b64_list)} 张图片（Augment调用模式）"
        return txt

    images: list = []
    for b64 in img_b64_list:
        try:
            img_bytes = base64.b64decode(b64)
            images.append(Image(data=img_bytes, format="png"))
        except Exception:
            txt += "\n\n[warning] 有一张图片解码失败。"

    if txt and images:
        return (txt, *images)
    elif txt:
        return (txt,)
    elif images:
        return (images[0],) if len(images) == 1 else tuple(images)
    else:
        return (caller_source_info,)


@mcp.tool()
async def interactive_feedback(
    message: Optional[str] = Field(default=None, description="The specific question for the user"),
    summary: Optional[str] = Field(default=None, description="Deprecated alias for message, kept for backward compatibility"),
    question: Optional[str] = Field(default=None, description="Deprecated extra question text, appended to message when present"),
    predefined_options: Optional[list] = Field(default=None, description="Predefined options for the user to choose from (optional)"),
    predefinedOptions: Optional[list] = Field(default=None, description="Deprecated camelCase alias for predefined_options"),
    project_path: Optional[str] = Field(default=None, description="Override project path (optional, auto-detected if not provided)"),
    project_directory: Optional[str] = Field(default=None, description="Deprecated alias for project_path"),
    project_name: Optional[str] = Field(default=None, description="Override project name (optional, auto-detected if not provided)"),
    git_branch: Optional[str] = Field(default=None, description="Override git branch name (optional, auto-detected if not provided)"),
    task_title: Optional[str] = Field(default=None, description="Short title shown prominently at the top of the UI window for distinguishing multiple tasks"),
    priority: int = Field(default=3, description="Priority level 1-5 (1=lowest, 5=highest, default=3)"),
    category: str = Field(default="general", description="Category: bug|feature|review|performance|docs|test|deploy|other"),
    context_data: Optional[dict] = Field(default=None, description="Additional context data as key-value pairs"),
) -> str | Tuple[str | Image, ...]:
    """
    Request interactive feedback from the user.
    
    支持心跳机制和防重复弹窗：
    - 如果用户在 WAIT_SECONDS 内未回复，返回心跳消息让 Agent 重新调用
    - 如果上一次弹窗仍在等待，复用现有弹窗而不创建新的
    - 收到回复后有短暂冷却期，防止 Agent 立即重复触发
    """
    global _active_process, _active_output_file, _heartbeat_count, _process_start_time, _last_response_time

    normalized_message, predefined_options_list, normalized_project_path = _normalize_feedback_inputs(
        message, summary, question, predefined_options, predefinedOptions,
        project_path, project_directory,
    )

    normalized_project_name = project_name if isinstance(project_name, str) and project_name.strip() else None
    normalized_git_branch = git_branch if isinstance(git_branch, str) and git_branch.strip() else None
    normalized_task_title = task_title if isinstance(task_title, str) and task_title.strip() else None
    normalized_priority = priority if isinstance(priority, int) else 3
    normalized_category = category if isinstance(category, str) and category.strip() else "general"
    normalized_context_data = context_data if isinstance(context_data, dict) else None

    # 冷却机制：收到用户回复后短暂等待，防止 Agent 立即重复触发
    if _last_response_time > 0:
        cooldown_remaining = _COOLDOWN_SECONDS - (time.time() - _last_response_time)
        if cooldown_remaining > 0:
            await asyncio.sleep(cooldown_remaining)

    # 复用现有活跃 UI 进程（防重复弹窗的核心逻辑）
    if _active_process is not None:
        if _active_process.returncode is not None:
            # 进程已结束，读取结果
            result = _read_result_file(_active_output_file)
            if result:
                _last_response_time = time.time()
                output = _format_feedback_result(result)
                _clear_active_state()
                return output
            _clear_active_state()
            # 结果无效，继续往下创建新进程
        else:
            # 进程仍在运行 - 等待 + 心跳超时
            logger.info(f"⏳ 复用现有UI进程 pid={_active_process.pid}, 心跳#{_heartbeat_count}")
            try:
                await asyncio.wait_for(_active_process.wait(), timeout=_WAIT_SECONDS)
                result = _read_result_file(_active_output_file)
                if result:
                    _last_response_time = time.time()
                    output = _format_feedback_result(result)
                    _clear_active_state()
                    return output
                _clear_active_state()
            except asyncio.TimeoutError:
                _heartbeat_count += 1
                elapsed_min = (time.time() - _process_start_time) / 60
                if elapsed_min * 60 >= _MAX_TOTAL_SECONDS:
                    logger.warning(f"⏰ 超过最大等待时间 {_MAX_TOTAL_SECONDS / 3600:.0f}h")
                    _clear_active_state()
                    return "TIMEOUT: 用户在最大等待时间内未回复，已停止等待。"
                logger.info(f"💓 心跳 #{_heartbeat_count} | 已等待 {elapsed_min:.1f} 分钟")
                return _build_heartbeat_msg(_heartbeat_count, elapsed_min)
            except asyncio.CancelledError:
                # 不杀进程，保留状态以便下次调用时复用
                logger.info(f"⚠️ 工具调用被取消，保留UI进程 pid={_active_process.pid}")
                raise

    # 没有活跃进程，启动新的 UI
    try:
        process, output_file = await _spawn_feedback_ui_process(
            normalized_message, predefined_options_list,
            normalized_project_path, normalized_project_name,
            normalized_git_branch, normalized_task_title,
            normalized_priority, normalized_category,
            normalized_context_data,
        )
    except Exception as e:
        logger.error(f"❌ UI启动失败: {e}")
        return f"ERROR: 反馈UI启动失败 - {e}"

    _active_process = process
    _active_output_file = output_file
    _process_start_time = time.time()
    _heartbeat_count = 0

    # 等待用户回复，超时返回心跳
    try:
        await asyncio.wait_for(process.wait(), timeout=_WAIT_SECONDS)
        result = _read_result_file(output_file)
        if result:
            _last_response_time = time.time()
            output = _format_feedback_result(result)
            _clear_active_state()
            return output
        _clear_active_state()
        return "ERROR: 反馈UI已关闭但未返回有效结果"
    except asyncio.TimeoutError:
        _heartbeat_count += 1
        elapsed_min = (time.time() - _process_start_time) / 60
        logger.info(f"💓 首次心跳 | 已等待 {elapsed_min:.1f} 分钟")
        return _build_heartbeat_msg(_heartbeat_count, elapsed_min)
    except asyncio.CancelledError:
        # 不杀进程，保留状态以便下次调用时复用
        logger.info(f"⚠️ 工具调用被取消，保留UI进程 pid={process.pid}")
        raise



if __name__ == "__main__":
    # stdio MCP 只能输出协议数据到 stdout，关闭 FastMCP 横幅和启动日志，
    # 避免 Cursor 在握手或工具调用时把普通文本误判为协议内容。
    mcp.run(transport="stdio", show_banner=False, log_level="ERROR")
