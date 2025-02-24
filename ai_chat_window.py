"""AI聊天窗口模块"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
from openai import OpenAI
import threading
import webbrowser
import os
import sys
from config import WINDOW_WIDTH, WINDOW_HEIGHT

class AIChatWindow:
    def __init__(self, parent, api_key):
        """初始化聊天窗口"""
        self.parent = parent
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        # 添加对话历史列表
        self.conversation_history = []
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("AI历史顾问（请保持网络连接)")
        self.window.geometry("490x700")  # 更小的窗口尺寸
        
        # 设置窗口背景色为暖色调
        self.window.configure(bg='#FFF8F3')  # 米白色背景
        
        # 创建界面元素
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
        
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
        
        # 确保窗口不会移出屏幕
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        # 限制x坐标范围
        x = max(0, min(x, screen_width - window_width))
        # 限制y坐标范围
        y = max(0, min(y, screen_height - window_height))
        
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
        """发送消息"""
        message = self.message_entry.get().strip()
        if not message:
            return
            
        # 防止重复发送
        if self.send_button.cget('state') == 'disabled':
            return
            
        self._set_input_state(tk.DISABLED)
        self.message_entry.delete(0, tk.END)
        self._update_display(f"你: {message}\n", 'user')
        
        # 使用守护线程发送消息
        send_thread = threading.Thread(
            target=self._get_ai_response,
            args=(message,),
            daemon=True
        )
        send_thread.start()
        
        # 添加超时检查
        self.window.after(40000, self._check_response_timeout, send_thread)
    
    def _check_response_timeout(self, thread):
        """检查响应是否超时"""
        if thread.is_alive():
            self._update_display("错误: 响应超时，请重试\n", 'error')
            self._set_input_state(tk.NORMAL)
    
    def _get_ai_response(self, message):
        """获取AI响应（流式版本）"""
        try:
            # 初始化流式消息标记
            self._update_display("AI: ", 'ai_stream')
            
            # 构建消息历史
            messages = [
                {
                    "role": "system",
                    "content": "你是一位专精于中国历史的AI顾问，特别擅长解答关于历代皇帝、年号、政治制度、历史评价、同时期中西方对比等问题。要求客观、理性，请用中文回答，不要使用markdown格式，只使用普通文本。"
                }
            ]
            temperature = 0.9
            messages.extend(self.conversation_history[-4:])  # 保留最近4轮对话
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": message})
            
            # 发起流式请求
            response_stream = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=True,
                timeout=15
            )

            full_response = ""
            # 处理流式响应
            for chunk in response_stream:
                chunk_content = chunk.choices[0].delta.content
                if chunk_content:
                    full_response += chunk_content
                    self._update_display(chunk_content, 'ai_stream', append=True)

            # 保存对话历史
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
            # 最终处理
            self._update_display("\n\n", 'ai_stream', append=True)
            return full_response

        except Exception as e:
            error_msg = f"错误: {str(e)}\n" if str(e) else "发送失败，请重试\n"
            self._update_display(error_msg, 'error')
        finally:
            self._set_input_state(tk.NORMAL)

    def _update_display(self, text, msg_type='system', append=False):
        """更新聊天显示（支持流式模式）"""
        def _update():
            self.chat_display.config(state=tk.NORMAL)
            
            # 颜色配置（新增ai_stream类型）
            color_palette = {
                'user': '#8B4513',    # 深棕色
                'ai': '#5C4033',      # 中棕色
                'error': '#CD5C5C',   # 暖红色
                'ai_stream': '#5C4033' 
            }
            
            # 自动创建标签样式
            tag_name = f'msg_{msg_type}'
            if tag_name not in self.chat_display.tag_names():
                self.chat_display.tag_config(
                    tag_name, 
                    foreground=color_palette.get(msg_type, '#000000')
                )

            # 流式内容处理逻辑
            if append:
                # 直接追加内容
                self.chat_display.insert(tk.END, text, tag_name)
            else:
                # 非流式内容添加换行分隔
                if self.chat_display.index(tk.END) != "1.0":
                    self.chat_display.insert(tk.END, "\n")
                self.chat_display.insert(tk.END, text, tag_name)

            self.chat_display.config(state=tk.DISABLED)
            self.chat_display.see(tk.END)

        # 线程安全处理
        if threading.current_thread() is threading.main_thread():
            _update()
        else:
            self.window.after(0, _update)
    
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