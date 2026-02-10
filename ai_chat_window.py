"""AI聊天窗口模块"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import customtkinter as ctk
import threading
import webbrowser
import os
import sys
import json
import ssl
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from config import WINDOW_WIDTH, WINDOW_HEIGHT

# DeepSeek API 地址（与 OpenAI 兼容格式）
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"

class AIChatWindow:
    def __init__(self, parent, api_key, initial_question=None, send_immediately=False):
        """初始化聊天窗口。initial_question 若提供则预填到输入框；send_immediately 为 True 则预填后自动发送。"""
        self.parent = parent
        self.api_key = api_key
        # 添加对话历史列表
        self.conversation_history = []
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        # 设置 Tcl/Tk 使用 UTF-8，避免在 Windows 上显示中文时出现 ascii 编码错误
        try:
            self.window.tk.call('encoding', 'system', 'utf-8')
        except Exception:
            pass
        self.window.title("AI历史顾问（请保持网络连接）")
        self.window.geometry("490x700")  # 更小的窗口尺寸
        
        # 设置窗口背景色为暖色调
        self.window.configure(bg='#FFF8F3')  # 米白色背景
        
        # 创建界面元素
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
        
        if initial_question and initial_question.strip():
            self._set_initial_question(initial_question.strip())
            if send_immediately:
                q = initial_question.strip()
                self.window.after(80, lambda: self._send_message_with_text(q))
        
        # 设置图标
        self.has_icon = False
        try:
            # 获取正确的基础路径
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "assets", "images", "seal.ico")
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
                self.has_icon = True
            else:
                print(f"图标文件不存在: {icon_path}")
        except tk.TclError as e:
            print(f"加载图标时发生Tcl错误: {e}")
        except Exception as e:
            print(f"加载图标时发生未知错误: {e}")
    
    def _create_widgets(self):
        """创建界面元素"""
        # 标题栏
        title_label = ttk.Label(
            self.window,
            text="AI历史顾问",
            font=('微软雅黑', 18),
            foreground='#8B4513',  # 暖棕色
            background='#FFF8F3'
        )
        title_label.pack(pady=(10,5))
        
        # 聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(
            self.window,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('微软雅黑', 14),
            bg='#FFFAF5',  # 更浅的米色
            fg='#5C4033',  # 深棕色文字
            relief='flat',
            height=22,
            padx=8,
            pady=8
        )
        self.chat_display.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # 添加右键菜单绑定
        self.chat_display.bind("<Button-3>", self.show_context_menu)  # Windows右键
        self.chat_display.bind("<Button-2>", self.show_context_menu)  # Mac右键
        
        # 底部输入区域
        input_frame = ttk.Frame(self.window)
        input_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        
        # 输入框
        self.message_entry = ctk.CTkEntry(
            input_frame,
            font=('微软雅黑', 11),
            height=40,
            placeholder_text="请提问...",
            border_width=1,
            corner_radius=4,
            fg_color='#FFFAF5',  # 浅米色
            text_color='#5C4033',  # 深棕色
            placeholder_text_color='#B38B6D'  # 浅棕色
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        # 发送按钮
        self.send_button = ctk.CTkButton(
            input_frame,
            text="发送",
            command=self._send_message,
            font=('微软雅黑', 11, 'bold'),
            height=40,
            width=60,
            fg_color='#A0522D',  # 深棕色
            hover_color='#CD853F',  # 浅棕色
            text_color='#FFF8DC',  # 米色文字
            corner_radius=8,
            border_width=2,
            border_color='#8B4513',  # 深棕色边框
            cursor='hand2'  # 鼠标悬停时显示手型光标
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))
    
    def _move_window(self, direction):
        """移动窗口"""
        print(f"Moving window: {direction}")  # 添加调试输出
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        
        step = 20  # 每次移动的像素数
        
        if direction == 'left':
            x -= step
        elif direction == 'right':
            x += step
        elif direction == 'up':
            y -= step
        elif direction == 'down':
            y += step
        
        # # 确保窗口不会移出屏幕
        # screen_width = self.window.winfo_screenwidth()
        # screen_height = self.window.winfo_screenheight()
        # window_width = self.window.winfo_width()
        # window_height = self.window.winfo_height()
        
        # # 限制x坐标范围
        # x = max(0, min(x, screen_width - window_width))
        # # 限制y坐标范围
        # y = max(0, min(y, screen_height - window_height))
        
        print(f"New position: x={x}, y={y}")  # 添加调试输出
        self.window.geometry(f"+{x}+{y}")
    def _bind_events(self):
        """绑定事件"""
        self.message_entry.bind('<Return>', lambda e: self._send_message())
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.window.bind('<Left>', lambda e: self._move_window('left'))
        self.window.bind('<Right>', lambda e: self._move_window('right'))
        self.window.bind('<Up>', lambda e: self._move_window('up'))
        self.window.bind('<Down>', lambda e: self._move_window('down'))
    
    def _send_message(self):
        """发送消息（从输入框读取内容）"""
        message = self.message_entry.get().strip()
        if not message:
            return
        self._clear_message_entry()
        self._send_message_with_text(message)

    def _send_message_with_text(self, message):
        """直接发送指定文本，不依赖输入框（用于「询问AI」等程序触发发送）；发送后清空输入框。"""
        if not message or not str(message).strip():
            return
        message = str(message).strip()
        if self.send_button.cget('state') == 'disabled':
            return
        try:
            self.message_entry.delete(0, "end")
        except Exception:
            try:
                n = len(self.message_entry.get())
                if n:
                    self.message_entry.delete(0, n)
            except Exception:
                pass
        self._set_input_state(tk.DISABLED)
        self._update_display(f"你: {message}\n", 'user')
        send_thread = threading.Thread(
            target=self._get_ai_response,
            args=(message,),
            daemon=True
        )
        send_thread.start()
        self.window.after(40000, self._check_response_timeout, send_thread)
    
    def _check_response_timeout(self, thread):
        """检查响应是否超时"""
        if thread.is_alive():
            self._update_display("错误: 响应超时，请重试\n", 'error')
            self._set_input_state(tk.NORMAL)
    
    def _get_ai_response(self, message):
        """获取AI响应（流式版本）：用 HTTP + 显式 UTF-8 请求，避免 Windows 下 ascii 编码错误"""
        # HTTP 头仅支持 latin-1，API Key 必须为纯 ASCII
        api_key_ascii = ''.join(c for c in (self.api_key or '') if ord(c) < 128).strip()
        if not api_key_ascii:
            self._update_display("错误: 未配置有效 API Key。请在程序目录的 api_key.txt 中填入 DeepSeek API Key（仅英文/数字）。\n", 'error')
            self._set_input_state(tk.NORMAL)
            return
        try:
            self._update_display("AI: ", 'ai_stream')

            messages = [
                {
                    "role": "system",
                    "content": "你是一位专精于中国历史的AI顾问，特别擅长解答关于历代皇帝、年号、政治制度、历史评价、同时期中西方对比等问题。要求客观、理性，请用中文回答，不要使用 markdown 格式，只使用普通文本。"
                }
            ]
            messages.extend(self.conversation_history[-4:])
            messages.append({"role": "user", "content": message})

            # 使用 ensure_ascii=False 保留中文，再显式按 UTF-8 编码，避免库内 ascii 编码
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "stream": True,
                "temperature": 0.9,
            }
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')

            req = Request(
                DEEPSEEK_CHAT_URL,
                data=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": "Bearer " + api_key_ascii,
                },
                method="POST",
            )
            # 使用 SSL 默认上下文，避免证书问题
            ctx = ssl.create_default_context()
            resp = urlopen(req, timeout=20, context=ctx)

            full_response = ""
            buf = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf or b"\r\n" in buf:
                    line, _, buf = buf.partition(b"\n")
                    line = line.strip()
                    if not line or line == b"data: [DONE]":
                        continue
                    if line.startswith(b"data: "):
                        try:
                            part = line[6:].decode("utf-8")
                            obj = json.loads(part)
                            delta = obj.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content") or ""
                            if content:
                                full_response += content
                                self._update_display(content, 'ai_stream', append=True)
                        except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                            pass

            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": full_response})
            self._update_display("\n\n", 'ai_stream', append=True)
            return full_response

        except HTTPError as e:
            try:
                err_body = e.read().decode("utf-8", errors="replace")
                error_msg = f"错误: API 返回 {e.code} - {err_body[:200]}\n"
            except Exception:
                error_msg = f"错误: API 返回 {e.code}\n"
            self._update_display(error_msg, 'error')
        except (URLError, OSError, Exception) as e:
            try:
                error_msg = f"错误: {str(e)}\n" if str(e) else "发送失败，请重试\n"
            except (UnicodeEncodeError, UnicodeDecodeError):
                error_msg = "错误: 请求失败，请检查网络与 API 设置后重试。\n"
            self._update_display(error_msg, 'error')
        finally:
            self._set_input_state(tk.NORMAL)

    def _update_display(self, text, msg_type='system', append=False):
        """更新聊天显示（支持流式模式）"""
        def _update():
            self.chat_display.config(state=tk.NORMAL)
            color_palette = {
                'user': '#8B4513',
                'ai': '#5C4033',
                'error': '#CD5C5C',
                'ai_stream': '#5C4033'
            }
            tag_name = f'msg_{msg_type}'
            if tag_name not in self.chat_display.tag_names():
                self.chat_display.tag_config(tag_name, foreground=color_palette.get(msg_type, '#000000'))

            if append:
                self.chat_display.insert(tk.END, text, tag_name)
            else:
                if self.chat_display.index(tk.END) != "1.0":
                    self.chat_display.insert(tk.END, "\n")
                self.chat_display.insert(tk.END, text, tag_name)

            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)

        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.window.after(0, _update)
    
    def _set_initial_question(self, text):
        """预填输入框内容（仅清空一次，不触发延迟清空）。"""
        try:
            try:
                self.message_entry.delete(0, "end")
            except Exception:
                n = len(self.message_entry.get())
                if n:
                    self.message_entry.delete(0, n)
            if text:
                self.message_entry.insert(0, text)
        except Exception:
            pass

    def set_initial_question(self, text):
        """供外部调用：预填输入框并拉前窗口。"""
        if text and str(text).strip():
            self._set_initial_question(str(text).strip())
        self.window.lift()
        self.window.focus_force()

    def send_question(self, text):
        """供外部调用：直接发送指定问题（不依赖输入框）。"""
        if not text or not str(text).strip():
            self.window.lift()
            self.window.focus_force()
            return
        self.window.lift()
        self.window.focus_force()
        self._send_message_with_text(str(text).strip())

    def _clear_message_entry(self):
        """清空输入框内容（兼容 CTkEntry 多种版本）"""
        def _do_clear():
            try:
                self.message_entry.delete(0, "end")
            except Exception:
                try:
                    n = len(self.message_entry.get())
                    if n > 0:
                        self.message_entry.delete(0, n)
                except Exception:
                    pass
        _do_clear()
        # 延迟再清一次，确保禁用/启用后显示已更新
        self.window.after(50, _do_clear)

    def _set_input_state(self, state):
        """设置输入状态"""
        def _update():
            self.message_entry.configure(state=state)
            self.send_button.configure(state=state)
        
        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.window.after(0, _update)
    
    def _on_closing(self):
        """窗口关闭时的处理"""
        self.window.destroy()

    def create_context_menu(self):
        """创建右键菜单"""
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(label="导出聊天记录", command=self.export_chat)
        return menu

    def show_context_menu(self, event):
        """显示右键菜单"""
        menu = self.create_context_menu()
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def export_chat(self):
        """导出聊天记录"""
        content = self.chat_display.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("提示", "当前没有可导出的内容")
            return

        file_types = [
            ('Excel 文件', '*.xlsx'),
            ('CSV 文件', '*.csv'),
            ('文本文件', '*.txt')
        ]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=file_types,
            title="导出聊天记录"
        )
        
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("成功", "聊天记录导出成功！")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")