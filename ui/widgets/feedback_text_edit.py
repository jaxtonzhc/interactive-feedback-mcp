# Custom Text Edit Widget for Interactive Feedback MCP
# 自定义文本编辑器组件 - 输入法位置智能调整版

import base64
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import QTextEdit, QApplication, QWidget
from PySide6.QtCore import Qt, Signal, QBuffer, QIODevice, QRect, QPoint, QTimer, QByteArray
from PySide6.QtGui import QKeyEvent, QPixmap, QInputMethodEvent, QTextCursor, QImage

class FeedbackTextEdit(QTextEdit):
    """支持图片粘贴和输入法位置智能调整的自定义文本编辑器"""
    
    # 图片处理常量
    DEFAULT_MAX_IMAGE_WIDTH = 1624
    DEFAULT_MAX_IMAGE_HEIGHT = 1624
    DEFAULT_IMAGE_FORMAT = "PNG"
    
    # 输入法位置调整常量 - 优化后的偏移量
    IME_OFFSET_Y = 15           # 输入法框向下偏移像素 (从25调整为15)
    IME_SAFETY_MARGIN = 10      # 安全边距
    IME_UPDATE_DELAY = 10       # 位置更新延迟(ms)

    # 定义类级别的信号
    image_pasted = Signal(QPixmap)
    ime_position_adjusted = Signal(QRect)  # 输入法位置调整信号
    submit_requested = Signal()  # 新增：提交请求信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAcceptRichText(False)
        
        # 输入法状态追踪
        self.ime_active = False
        self.original_cursor_rect = QRect()
        self.adjusted_ime_rect = QRect()
        
        # 图片数据存储
        self._images_list = []
        self._image_data = []
        
        # 设置定时器用于延迟更新输入法位置
        self.ime_update_timer = QTimer()
        self.ime_update_timer.setSingleShot(True)
        self.ime_update_timer.timeout.connect(self._update_ime_position)
        
        print("🎯 FeedbackTextEdit初始化完成 - 输入法位置智能调整模式 (优化偏移量: 15px)")

    def inputMethodEvent(self, event: QInputMethodEvent):
        """处理输入法事件，实现候选词位置智能调整"""
        try:
            # 调用父类处理基础输入法事件
            super().inputMethodEvent(event)
            
            # 检查是否有输入法组合文本或提交文本
            has_preedit = len(event.preeditString()) > 0
            has_commit = len(event.commitString()) > 0
            
            if has_preedit:
                # 输入法激活，开始组合输入
                if not self.ime_active:
                    self.ime_active = True
                    print("🎯 输入法激活 - 开始位置调整")
                
                # 延迟更新输入法位置，避免频繁调整
                self.ime_update_timer.start(self.IME_UPDATE_DELAY)
                
            elif has_commit:
                # 文本提交，但输入法可能仍然活跃
                print("📝 文本已提交")
                
            elif self.ime_active and not has_preedit:
                # 输入法关闭
                self.ime_active = False
                print("🔄 输入法关闭 - 恢复正常位置")
                self._reset_ime_position()
                
        except Exception as e:
            print(f"❌ 输入法事件处理错误: {e}")

    def _update_ime_position(self):
        """更新输入法位置 - 实现候选词框下偏移"""
        try:
            if not self.ime_active:
                return
                
            # 获取当前光标位置
            cursor_rect = self.cursorRect()
            if cursor_rect.isNull():
                return
                
            # 记录原始光标位置
            self.original_cursor_rect = cursor_rect
            
            # 计算调整后的输入法显示位置
            # 将候选词框位置向下偏移，避免遮挡正在编辑的文本
            adjusted_rect = QRect(cursor_rect)
            adjusted_rect.moveTop(cursor_rect.bottom() + self.IME_OFFSET_Y)
            
            # 确保调整后的位置在控件范围内
            widget_rect = self.rect()
            if adjusted_rect.bottom() > widget_rect.bottom():
                # 如果下偏移超出控件边界，则向上偏移
                adjusted_rect.moveTop(cursor_rect.top() - self.IME_OFFSET_Y - 30)
            
            self.adjusted_ime_rect = adjusted_rect
            
            # 设置输入法微焦点位置
            self._set_ime_micro_focus(adjusted_rect)
            
            # 发送位置调整信号
            self.ime_position_adjusted.emit(adjusted_rect)
            
            print(f"🎯 输入法位置已调整: 原始({cursor_rect.x()},{cursor_rect.y()}) → 调整后({adjusted_rect.x()},{adjusted_rect.y()})")
            
        except Exception as e:
            print(f"❌ 输入法位置更新错误: {e}")

    def _set_ime_micro_focus(self, rect: QRect):
        """设置输入法微焦点位置"""
        try:
            # 将相对位置转换为全局位置
            global_rect = QRect(
                self.mapToGlobal(rect.topLeft()),
                rect.size()
            )
            
            # 更新输入法微焦点
            self.setAttribute(Qt.WA_InputMethodEnabled, True)
            self.setInputMethodHints(Qt.ImhNone)
            
            # 触发输入法位置更新
            if hasattr(self, 'inputMethodQuery'):
                self.updateMicroFocus()
                
        except Exception as e:
            print(f"⚠️ 设置输入法微焦点错误: {e}")

    def _reset_ime_position(self):
        """重置输入法位置到原始状态"""
        try:
            if not self.original_cursor_rect.isNull():
                # 恢复到原始光标位置
                self._set_ime_micro_focus(self.original_cursor_rect)
                print("🔄 输入法位置已重置")
                
        except Exception as e:
            print(f"❌ 输入法位置重置错误: {e}")

    def inputMethodQuery(self, query):
        """提供输入法查询信息 - 返回调整后的位置"""
        try:
            # PySide6中使用Qt.InputMethodQuery的枚举值
            from PySide6.QtCore import Qt
            
            # 兼容性处理
            if hasattr(Qt, 'ImCursorRectangle'):
                cursor_rect_query = Qt.ImCursorRectangle
                micro_focus_query = getattr(Qt, 'ImMicroFocus', Qt.ImCursorRectangle)
                selection_query = getattr(Qt, 'ImCurrentSelection', None)
            else:
                cursor_rect_query = Qt.InputMethodQuery.ImCursorRectangle if hasattr(Qt.InputMethodQuery, 'ImCursorRectangle') else 1
                micro_focus_query = getattr(Qt.InputMethodQuery, 'ImMicroFocus', cursor_rect_query) if hasattr(Qt, 'InputMethodQuery') else cursor_rect_query
                selection_query = getattr(Qt.InputMethodQuery, 'ImCurrentSelection', None) if hasattr(Qt, 'InputMethodQuery') else None
            
            if query == cursor_rect_query or query == micro_focus_query:
                # 如果输入法活跃且有调整位置，返回调整后的位置
                if self.ime_active and not self.adjusted_ime_rect.isNull():
                    return self.adjusted_ime_rect
                else:
                    # 否则返回正常的光标位置
                    return self.cursorRect()
                    
            elif selection_query and query == selection_query:
                # 返回当前选择
                return self.textCursor().selectedText()
            
            return super().inputMethodQuery(query)
            
        except Exception as e:
            print(f"⚠️ 输入法查询异常: {e}")
            # 发生异常时返回光标位置作为默认值
            try:
                return self.cursorRect()
            except:
                return super().inputMethodQuery(query)

    def focusInEvent(self, event):
        """获得焦点时的处理"""
        super().focusInEvent(event)
        print("🎯 文本框获得焦点")

    def focusOutEvent(self, event):
        """失去焦点时的处理"""
        super().focusOutEvent(event)
        
        # 重置输入法状态
        if self.ime_active:
            self.ime_active = False
            self._reset_ime_position()
            print("🔄 失去焦点，重置输入法状态")

    def get_ime_status(self) -> Dict[str, Any]:
        """获取当前输入法状态信息"""
        return {
            'active': self.ime_active,
            'original_rect': {
                'x': self.original_cursor_rect.x(),
                'y': self.original_cursor_rect.y(),
                'width': self.original_cursor_rect.width(),
                'height': self.original_cursor_rect.height()
            },
            'adjusted_rect': {
                'x': self.adjusted_ime_rect.x(),
                'y': self.adjusted_ime_rect.y(),
                'width': self.adjusted_ime_rect.width(),
                'height': self.adjusted_ime_rect.height()
            }
        }

    # ========================
    # 图片粘贴功能保持不变
    # ========================
    def canInsertFromMimeData(self, source):
        """检查是否可以从MIME数据插入内容"""
        if source.hasImage() or source.hasUrls():
            return True
        if source.hasText() or source.hasHtml():
            return True
        return super().canInsertFromMimeData(source)

    def _store_pixmap(self, pixmap: QPixmap) -> bool:
        """统一存储图片并发出信号"""
        if pixmap.isNull():
            return False

        image_id = str(uuid.uuid4())
        image_uri = self.get_image_data_uri(pixmap)
        image_info = {
            'id': image_id,
            'base64': image_uri.split(',')[1] if ',' in image_uri else image_uri,
            'width': pixmap.width(),
            'height': pixmap.height(),
            'timestamp': datetime.now().isoformat()
        }
        self._image_data.append(image_info)
        self._images_list.append(image_uri)

        print(f"📷 图片已存储: {image_id}, 大小: {pixmap.width()}x{pixmap.height()}")
        self.image_pasted.emit(pixmap)
        return True

    def _extract_pixmap_from_mime(self, source) -> QPixmap:
        """尽量从各种剪贴板格式里提取图片"""
        try:
            if source.hasImage():
                image = source.imageData()
                if isinstance(image, QImage) and not image.isNull():
                    return QPixmap.fromImage(image)
                if isinstance(image, QPixmap) and not image.isNull():
                    return image
        except Exception as e:
            print(f"⚠️ 读取剪贴板 imageData 失败: {e}")

        try:
            if source.hasUrls():
                for url in source.urls():
                    local_path = url.toLocalFile()
                    if local_path:
                        pixmap = QPixmap(local_path)
                        if not pixmap.isNull():
                            print(f"📎 从文件URL读取到图片: {local_path}")
                            return pixmap
        except Exception as e:
            print(f"⚠️ 从URL读取图片失败: {e}")

        try:
            clipboard = QApplication.clipboard()
            pixmap = clipboard.pixmap()
            if not pixmap.isNull():
                print("📋 从系统剪贴板兜底读取到图片")
                return pixmap
        except Exception as e:
            print(f"⚠️ 从系统剪贴板读取图片失败: {e}")

        return QPixmap()

    def insertFromMimeData(self, source):
        """从MIME数据插入内容，图片保留，文本一律按纯文本粘贴"""
        pixmap = self._extract_pixmap_from_mime(source)
        if not pixmap.isNull() and self._store_pixmap(pixmap):
            return

        if source.hasText() or source.hasHtml():
            text = source.text()
            if text:
                self.insertPlainText(text)
                return
        
        # 兜底交给父类处理
        super().insertFromMimeData(source)

    def keyPressEvent(self, event: QKeyEvent):
        """处理按键事件"""
        # 检查焦点状态
        has_focus = self.hasFocus()
        is_enabled = self.isEnabled()
        is_visible = self.isVisible()
        print(f"🔍 组件状态检查: Focus={has_focus}, Enabled={is_enabled}, Visible={is_visible}")
        
        # 详细的按键调试信息
        key_name = event.text() if event.text() else f"Key_{event.key()}"
        modifiers = []
        
        # 改进的修饰键检测，支持macOS
        mod_flags = event.modifiers()
        if mod_flags & Qt.ControlModifier:
            modifiers.append("Ctrl")
        if mod_flags & Qt.MetaModifier:  # macOS上的Cmd键
            modifiers.append("Cmd")
        if mod_flags & Qt.ShiftModifier:
            modifiers.append("Shift")
        if mod_flags & Qt.AltModifier:
            modifiers.append("Alt")
        
        modifier_text = "+".join(modifiers) if modifiers else "None"
        print(f"🎹 按键检测: Key={event.key()}, Text='{event.text()}', Modifiers={modifier_text}")
        
        # 检测Enter/Return键
        is_return_enter = event.key() in (Qt.Key_Return, Qt.Key_Enter)
        
        if is_return_enter:
            # 检测修饰键状态
            has_shift = bool(mod_flags & Qt.ShiftModifier)
            has_ctrl_or_cmd = bool(mod_flags & (Qt.ControlModifier | Qt.MetaModifier))
            
            if has_shift:
                # Shift+Enter: 换行（默认行为）
                print("↩️ Shift+Enter检测 - 执行换行")
                super().keyPressEvent(event)
                return
            elif has_ctrl_or_cmd:
                # Ctrl+Enter 或 Cmd+Enter: 提交
                cmd_key = "Cmd" if mod_flags & Qt.MetaModifier else "Ctrl"
                print(f"⌨️ {cmd_key}+Enter快捷键触发提交 ✅")
                self.submit_requested.emit()
                event.accept()
                return
            else:
                # 单独的Enter: 提交 (three_column_layout的默认行为)
                print("⌨️ Enter键触发提交 ✅")
                print(f"📡 即将发射submit_requested信号...")
                
                # 发射信号 - 简化调试，避免API错误
                try:
                    self.submit_requested.emit()
                    print(f"✅ submit_requested信号已发射！")
                except Exception as e:
                    print(f"❌ 信号发射失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"🔗 信号发射操作完成")
                event.accept()
                return
        
        # 检测Esc键来取消输入法
        if event.key() == Qt.Key_Escape and self.ime_active:
            self.ime_active = False
            self._reset_ime_position()
            print("⌨️ Esc键取消输入法")
            event.accept()
            return
            
        # 处理其他按键
        super().keyPressEvent(event)

    def get_image_data_uri(self, pixmap: QPixmap, max_width: int = None, max_height: int = None, 
                          image_format: str = None) -> str:
        """将QPixmap转换为Base64数据URI"""
        if max_width is None:
            max_width = self.DEFAULT_MAX_IMAGE_WIDTH
        if max_height is None:
            max_height = self.DEFAULT_MAX_IMAGE_HEIGHT
        if image_format is None:
            image_format = self.DEFAULT_IMAGE_FORMAT

        # 缩放图片
        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 转换为字节数组
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, image_format)

        # 编码为Base64
        image_base64 = base64.b64encode(byte_array.data()).decode('utf-8')
        mime_type = f"image/{image_format.lower()}"
        
        return f"data:{mime_type};base64,{image_base64}"

    def get_image_data(self) -> List[Dict[str, Any]]:
        """获取当前存储的图片数据（与main_window兼容）"""
        return self._image_data.copy()

    def get_images_list(self) -> List[str]:
        """获取当前存储的图片列表"""
        return self._images_list.copy()
        
    def clear_images(self):
        """清空图片存储"""
        self._images_list.clear()
        self._image_data.clear()
        print("🗑️ 图片存储已清空") 