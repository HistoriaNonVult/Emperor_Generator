# -*- coding: utf-8 -*-
import random
import re
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import scrolledtext
from tkinter import font
import os
import opencc
import sys
import webbrowser
import fnmatch
import customtkinter as ctk
from tkinter import scrolledtext
import threading
from openai import OpenAI
from ai_chat_window import AIChatWindow
from emperor_generator import EmperorGenerator
from data import emperor_text
can_access_google = None

class EmperorApp:
    def _move_window(self, direction):
        """移动窗口"""
        print(f"Moving window: {direction}")  # 添加调试输出
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        
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
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # 限制x坐标范围
        x = max(0, min(x, screen_width - window_width))
        # 限制y坐标范围
        y = max(0, min(y, screen_height - window_height))
        
        print(f"New position: x={x}, y={y}")  # 添加调试输出
        self.root.geometry(f"+{x}+{y}")
    def __init__(self, root):
        self.root = root
        self.root.title("受命於天，既壽永昌")
        
        # 设置初始透明度为0
        self.root.attributes('-alpha', 0.0)
        self.chat_window = None
        # 设置图标
        self.has_icon = False
        try:
            if getattr(sys, 'frozen', False):
                # 打包后的路径
                base_path = sys._MEIPASS
            else:
                # 开发环境路径
                base_path = os.path.abspath(".")
                
            icon_path = os.path.join(base_path, "assets", "images", "seal.ico")
            self.root.iconbitmap(icon_path)
            self.has_icon = True
        except Exception as e:
            print(f"无法加载图标: {e}")
        
        # 设窗口大小和位置
        window_width = 800
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.generator = EmperorGenerator()
        
        # 设置全局字体样式
        self.setup_fonts()
        self.create_widgets()
        
        # 开始淡入效果
        self.fade_in()
        self.check_vpn_status()
        
        self.root.bind('<Left>', lambda e: self._move_window('left'))
        self.root.bind('<Right>', lambda e: self._move_window('right'))
        self.root.bind('<Up>', lambda e: self._move_window('up'))
        self.root.bind('<Down>', lambda e: self._move_window('down'))
        
    def check_vpn_status(self):
        """检测Windows代理状态"""
        global can_access_google  # global 声明需要在最前面
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings', 
                                0, winreg.KEY_READ)
            proxy_enable, _ = winreg.QueryValueEx(key, 'ProxyEnable')
            winreg.CloseKey(key)
            can_access_google = bool(proxy_enable)
        except:
            can_access_google = False
    def fade_in(self):
        """实现窗口淡入效果"""
        alpha = self.root.attributes('-alpha')
        if alpha < 1.0:
            alpha += 0.2
            self.root.attributes('-alpha', alpha)
            self.root.after(50, self.fade_in)

        # 解析皇帝数据
        self.generator.parse_emperor_data(emperor_text)
        
        self.is_traditional = False  # 默认使用简体
        
        # 创建繁简转换器
        self.converter_t2s = opencc.OpenCC('t2s')  # 繁体到简体
        self.converter_s2t = opencc.OpenCC('s2t')  # 简体到繁体

    def setup_fonts(self):
        """设置字体"""
        self.is_traditional = False  # 在这里初始化繁简体设置
        
        # 设置字体
        self.title_font = ('华文行楷', 16)
        self.button_font = ('华文行楷', 12)
        self.text_font = ('华文行楷', 12)
        
        # 配置标签样式
        style = ttk.Style()
        style.configure('Title.TLabel', font=self.title_font)
        style.configure('TButton', font=self.button_font)

    def create_widgets(self):
        """创建GUI组件"""
        # 设置主题色
        THEME_COLORS = {
            'primary': '#8B0000',     # 深红色：象征皇权
            'secondary': '#704214',   # 深褐色：象征历史的沉淀
            'accent': '#DAA520',      # 古铜金：象征皇家气派
            'text': '#2B1B17',        # 墨黑色：典籍颜色
            'bg': '#F5E6CB'           # 宣纸色：传统背景
        }

        # 标题区域
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', pady=(20,0))
        
        title_label = ttk.Label(
            title_frame,
            text="皇帝生成器",
            style='Title.TLabel',
            font=('华文行楷', 36, 'bold'),
            foreground='#8B0000'  # 深红色
        )
        title_label.pack(pady=(10,5))

        # 添加简约饰线
        separator_frame = ttk.Frame(self.root)
        separator_frame.pack(fill='x', padx=150, pady=(0,20))
        separator = ttk.Separator(separator_frame, orient='horizontal')
        separator.pack(fill='x', pady=5)

        # 添加搜索框和繁体切换按钮到同一行
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=20, pady=(0,10))
        
        # 搜索框区域
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side='left')
        
        self.search_label = ttk.Label(
            search_frame,
            text="搜索皇帝：",
            font=self.button_font
        )
        self.search_label.pack(side='left', padx=(0, 10))
        
        self.search_entry = ttk.Entry(
            search_frame,
            font=self.text_font,
            width=20
        )
        self.search_entry.pack(side='left')
        
        # 搜索按钮和高级搜索按钮放在同一个容器中
        buttons_frame = ttk.Frame(search_frame)
        buttons_frame.pack(side='left', padx=5)
        
        self.search_button = tk.Button(
            buttons_frame,
            text="搜索",
            command=self.search_emperor,
            font=('微软雅黑', 10),
            width=6,
            relief='flat',
            bg='#F5E6CB',
            fg='#8B2323',
            activebackground='#DAA520',
            activeforeground='#800000',
            cursor='hand2'
        )
        self.search_button.pack(side='left', padx=5)
        
        # 添加高级搜索按钮
        self.advanced_search_button = tk.Button(
            buttons_frame,
            text="高级搜索",
            command=self.create_advanced_search_dialog,
            font=('微软雅黑', 10),
            width=8,
            relief='flat',
            bg='#F5E6CB',
            fg='#8B2323',
            activebackground='#DAA520',
            activeforeground='#800000',
            cursor='hand2'
        )
        self.advanced_search_button.pack(side='left', padx=5)
        
        # 添加鼠标悬停效果
        def on_enter(e, button):
            button.config(
                bg='#DAA520',
                fg='#800000'
            )
        
        def on_leave(e, button):
            button.config(
                bg='#F5E6CB',
                fg='#8B2323'
            )
        
        # 为两个按钮都添加悬停效果
        for button in (self.search_button, self.advanced_search_button):
            button.bind('<Enter>', lambda e, b=button: on_enter(e, b))
            button.bind('<Leave>', lambda e, b=button: on_leave(e, b))
        
        # 繁体切换按钮在右边
        self.switch_button = tk.Button(
            control_frame,
            text="繁體",
            command=self.toggle_traditional,
            font=('微软雅黑', 10),
            width=6,
            relief='flat',
            bg='#F5E6CB',
            fg='#8B2323',
            activebackground='#DAA520',
            activeforeground='#800000',
            cursor='hand2'
        )
        self.switch_button.pack(side='right')
        
        # 绑定回车键搜索
        self.search_entry.bind('<Return>', lambda e: self.search_emperor())
        
        # 按钮样式
        button_styles = [
            {
                "text": "随机生成一位皇帝",
                "command": self.generate_random_emperor,
                "bg": "#8B2323",  # 深红褐色
                "hover_bg": "#800000",
                "icon": ""
            },
            {
                "text": "随机生成多位皇帝",
                "command": self.generate_multiple_emperors,
                "bg": "#704214",  # 深褐色
                "hover_bg": "#5C3317",
                "icon": ""
            },

            {
                "text": "按朝代查询皇帝",
                "command": self.query_emperors_by_dynasty,
                "bg": "#8B4513",  # 赭石
                "hover_bg": "#8B4500",
                "icon": ""
            }
        ]
        
        # 创建动画效果
        def on_enter(e, btn, hover_color):
            btn.configure(bg=hover_color)
            # 添加缩放动画
            btn.configure(relief="raised")
            
        def on_leave(e, btn, normal_color):
            btn.configure(bg=normal_color)
            btn.configure(relief="flat")
        
        # 按钮区域
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)
        
        for i, btn_style in enumerate(button_styles):
            btn = tk.Button(
                button_frame,
                text=f"{btn_style['icon']} {btn_style['text']}",
                command=btn_style["command"],
                font=('LiSu', 16),  # 使用隶书字体
                width=20,
                height=2,
                bg=btn_style["bg"],
                fg="white",
                relief="flat",
                cursor="hand2"
            )
            btn.bind("<Enter>", lambda e, b=btn, c=btn_style["hover_bg"]: on_enter(e, b, c))
            btn.bind("<Leave>", lambda e, b=btn, c=btn_style["bg"]: on_leave(e, b, c))
            btn.grid(row=0, column=i, padx=15, pady=5)

        # 在文本框上方添加排序控件
        sort_frame = ttk.Frame(self.root)
        sort_frame.pack(fill="x", padx=10, pady=(5,0))
        
        # 添加排序标签
        sort_label = ttk.Label(
            sort_frame,
            text="排序方式：" if not self.is_traditional else "排序方式：",
            font=('微雅黑', 9)
        )
        sort_label.pack(side="left", padx=(0,5))
        
        # 排序选项
        self.sort_var = tk.StringVar(value='dynasty')
        sort_options = [
            ('按朝代', 'dynasty'),
            ('按年代', 'year'),
            #('按名字', 'name'),
            #('按称号', 'title'),
            ('按在位时间', 'reign_length')  # 新增选项
        ]
        
        # 创建排序按钮
        self.sort_buttons = []
        for text, value in sort_options:
            rb = ttk.Radiobutton(
                sort_frame,
                text=text if not self.is_traditional else text.replace('名字', '名諱').replace('称号', '稱號'),
                variable=self.sort_var,
                value=value,
                command=self.resort_results  # 添加排序回调
            )
            rb.pack(side="left", padx=5)
        self.sort_buttons.append(rb)
        # 添加统计分析按钮
        self.analyze_button = ctk.CTkButton(  # 使用 CTkButton 而不是 ttk.Button
            sort_frame,
            text="統計分析" if self.is_traditional else "统计分析",
            command=self.analyze_emperors,
            font=('华文行楷', 16),  # 使用与其他按钮一致的字体和大小
            fg_color='#E6D5AC',    
            hover_color='#D4C391', # 悬停颜色
            text_color='#4A4A4A',  # 文字颜色
            corner_radius=6,
            border_width=1,
            border_color='#8B4513',
            width=100,
            height=32
        )
        self.analyze_button.pack(side="right", padx=20)

        # AI助手按钮
        self.chat_button = ctk.CTkButton(
            sort_frame,
            text="AI助手",
            command=self.show_chat_window,
            font=('华文行楷', 16),   # 改用典雅的华文行楷字体
            fg_color='#2C3E50',    # 深蓝灰色背景
            hover_color='#34495E',  # 悬停时的颜色
            text_color='#7DF9FF',   # 电光蓝色文字
            corner_radius=8,        # 圆角
            border_width=2,
            border_color='#00CED1', # 暗青色边框
            width=100,
            height=32
        )
        self.chat_button.pack(side="right", padx=5)
        
        # 文本显示区域
        text_frame = ttk.Frame(self.root)
        text_frame.pack(padx=30, pady=20, fill=tk.BOTH, expand=True)
        
        # 自定义滚动条样式
        style = ttk.Style()
        style.element_create("Custom.Vertical.TScrollbar.trough", "from", "default")
        style.element_create("Custom.Vertical.TScrollbar.thumb", "from", "default")
        style.layout("Custom.Vertical.TScrollbar", [
            ('Custom.Vertical.TScrollbar.trough', {'children':
                [('Custom.Vertical.TScrollbar.thumb', {'expand': '1'})],
                'sticky': 'ns'})
        ])
        
        # 配置滚动条样式
        style.configure("Custom.Vertical.TScrollbar",
            background='#F5E6CB',  # 滚动条背景色，与整体主题协调
            troughcolor='#FFF8DC',  # 滚动槽颜色，与本框背景色致
            width=16,  # 适当加宽滚动条
            borderwidth=0,  # 无边框
            relief="flat",  # 扁平化效果
            arrowsize=14  # 略微加大箭头
        )
        
        # 鼠标悬停时的样式
        style.map("Custom.Vertical.TScrollbar",
            background=[('active', '#DAA520')],  # 鼠标悬停时变为金色
            troughcolor=[('active', '#FFF8DC')]
        )
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(
            text_frame,
            style="Custom.Vertical.TScrollbar",
            orient="vertical"
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 1))  # 稍微调整右边距
        
        # 文本框设置保持不变
        self.display_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            width=65,
            height=22,
            font=('KaiTi', 16),
            bg='#FFF8DC',
            fg='#2B1B17',
            padx=15,
            pady=10,
            relief="solid",
            borderwidth=1,
            yscrollcommand=scrollbar.set
        )
        self.display_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        scrollbar.config(command=self.display_text.yview)
        
        # 添加鼠标滚轮支持
        def on_mousewheel(event):
            self.display_text.yview_scroll(-1 * (event.delta // 120), "units")
        self.display_text.bind("<MouseWheel>", on_mousewheel)
        
        # 文本框样式配置
        self.TEXT_TAGS = {
            'hyperlink': {
                'font': ('KaiTi', 12),
                'foreground': "#8B2323",
                'underline': 1
            },
            'section_title': {
                'font': ('Microsoft YaHei', 16, 'bold'),
                'foreground': '#8B0000',
                'spacing1': 10,
                'spacing3': 10
            },
            'dynasty_title': {
                'font': ('Microsoft YaHei', 14, 'bold'),
                'foreground': '#704214',
                'spacing1': 5,
                'spacing3': 5
            }
        }
        
        # 配置文本样式
        for tag, style in self.TEXT_TAGS.items():
            self.display_text.tag_configure(tag, **style)

        # 添加快捷键绑定
        self.root.bind('<Return>', lambda e: self.search_emperor())  # 回车键触发搜索
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())  # Ctrl+F 聚焦搜索框
        self.root.bind('<Escape>', lambda e: self.root.focus())  # ESC键取消焦点
        
        # 为搜索框单独添加回车键绑定
        self.search_entry.bind('<Return>', lambda e: self.search_emperor())

    def convert_text(self, text, to_traditional=True):
        """转换文字"""
        if to_traditional:
            return self.converter_s2t.convert(text)
        return self.converter_t2s.convert(text)
    
    def toggle_traditional(self):
        """切换繁简显示"""
        self.is_traditional = not self.is_traditional
        
        # 更新切换按钮文字
        if self.is_traditional:
            self.switch_button.config(text="繁體")
        else:
            self.switch_button.config(text="简体")
        
        # 转换所有界面文字
        def convert_widget_text(widget):
            """递归转换所有控件的文字"""
            if isinstance(widget, (tk.Button, ttk.Button)):
                if widget != self.switch_button:  # 排除繁简切换按钮
                    current_text = widget.cget('text')
                    new_text = self.convert_text(current_text, self.is_traditional)
                    widget.config(text=new_text)
            elif isinstance(widget, (ttk.Label, ttk.Radiobutton)):  # 添加 ttk.Radiobutton
                current_text = widget.cget('text')
                new_text = self.convert_text(current_text, self.is_traditional)
                widget.config(text=new_text)
            elif isinstance(widget, ttk.Combobox):
                values = widget.cget('values')
                if values:
                    new_values = [self.convert_text(v, self.is_traditional) for v in values]
                    current = widget.get()
                    new_current = self.convert_text(current, self.is_traditional)
                    widget.config(values=new_values)
                    widget.set(new_current)
            
            # 递归处理子控件
            for child in widget.winfo_children():
                convert_widget_text(child)
        
        # 转换所有控件文字
        convert_widget_text(self.root)
        
        # 转换搜索标签文字
        search_label_text = "搜索皇帝："
        new_search_label_text = self.convert_text(search_label_text, self.is_traditional)
        self.search_label.config(text=new_search_label_text)
        
        # 转换搜索按钮文字
        search_button_text = "搜索"
        new_search_button_text = self.convert_text(search_button_text, self.is_traditional)
        self.search_button.config(text=new_search_button_text)
        
        # 保存当前文本和链接信息
        current_content = []
        current_pos = "1.0"
        
        while True:
            next_tag = self.display_text.tag_nextrange("hyperlink", current_pos)
            if not next_tag:
                # 添加剩余文本
                remaining = self.display_text.get(current_pos, "end")
                if remaining.strip():
                    current_content.append({"text": remaining, "tags": []})
                break
            
            # 添加非链接文本
            non_link_text = self.display_text.get(current_pos, next_tag[0])
            if non_link_text.strip():
                current_content.append({"text": non_link_text, "tags": []})
            
            # 添加链接文本
            link_text = self.display_text.get(next_tag[0], next_tag[1])
            tags = self.display_text.tag_names(next_tag[0])
            current_content.append({"text": link_text, "tags": tags})
            
            current_pos = next_tag[1]
        
        # 清空并重新插入后的文本
        self.display_text.delete("1.0", tk.END)
        
        # 重新插入文本并保持标签
        for item in current_content:
            start = self.display_text.index("end-1c")
            text = self.convert_text(item["text"], self.is_traditional)
            self.display_text.insert(tk.END, text)
            end = self.display_text.index("end-1c")
            
            # 重新应用标签
            for tag in item["tags"]:
                self.display_text.tag_add(tag, start, end)
                if tag.startswith("link_"):
                    # 重新绑定事件
                    self.display_text.tag_bind(tag, "<Button-1>", self._on_click)
                    self.display_text.tag_bind(tag, "<Enter>", self._on_enter)
                    self.display_text.tag_bind(tag, "<Leave>", self._on_leave)
                    
        # 如果高级搜索对话框打开，更新其内容
        if hasattr(self, 'advanced_search_dialog') and self.advanced_search_dialog.winfo_exists():
            widgets = self.advanced_search_widgets
            
            # 更新对话框标题
            self.advanced_search_dialog.title(
                "進階搜索" if self.is_traditional else "高级搜索"
            )
            
            # 更新搜索条件框架标题
            widgets['search_frame'].configure(
                text="搜索條件" if self.is_traditional else "搜索条件"
            )
            
            # 更新选项框架标题
            widgets['options_frame'].configure(
                text="搜索選項" if self.is_traditional else "搜索选项"
            )
            
            # ��新字段标签
            fields = {
                'dynasty': '朝代',
                'title': '稱號' if self.is_traditional else '称号',
                'name': '名諱' if self.is_traditional else '名讳',
                'temple_name': '廟號' if self.is_traditional else '庙号',
                'posthumous_name': '謚號' if self.is_traditional else '谥号',
                'reign_period': '在位時間' if self.is_traditional else '在位时间',
                'era_names': '年號' if self.is_traditional else '年号'
            }
            
            # 更新标签文本
            for label in widgets['labels']:
                old_text = label.cget('text').rstrip(':')
                for key, value in fields.items():
                    if old_text == self.convert_text(value, not self.is_traditional):
                        new_text = value
                        label.configure(text=f"{new_text}:")
                        break
            
            # 更新单选按钮文本
            radio_texts = [
                "匹配任意條件" if self.is_traditional else "匹配任意条件",
                "匹配所有條件" if self.is_traditional else "匹配所有条件"
            ]
            for btn, text in zip(widgets['match_buttons'], radio_texts):
                btn.configure(text=text)
            
            # 更新区分大小写复选框文本
            widgets['case_button'].configure(
                text="區分大小寫" if self.is_traditional else "区分大小写"
            )
            
            # 更新按钮文本
            widgets['search_btn'].configure(
                text="搜索" if self.is_traditional else "搜索"
            )
            widgets['cancel_btn'].configure(
                text="取消" if self.is_traditional else "取消"
            )
        
        # 更新排序标签和选项的文字
        sort_label_text = "排序方式：" if not self.is_traditional else "排序方式："
        self.sort_label.configure(text=sort_label_text)
        
        # 更新排序选项的文本
        sort_texts = {
            'dynasty': '按朝代',
            'year': '按年代',
           # 'name': '按名字' if not self.is_traditional else '按名諱',
           # 'title': '按称号' if not self.is_traditional else '按稱號'
        }
        
        # 直接遍历排序选项的 Frame 中的单选按钮
        for child in self.control_frame.winfo_children():
            if isinstance(child, ttk.Frame):  # 找到排序选项的 Frame
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Radiobutton):
                        value = widget.cget('value')
                        if value in sort_texts:
                            text = sort_texts[value]
                            # 转换文本
                            text = self.convert_text(text, self.is_traditional)
                            widget.configure(text=text)
    def insert_emperor_with_link(self, emperor):
        """插入带有搜索链接的皇帝信息"""
        info = self.generator.format_emperor_info(emperor)
        
        # 根据当前模式转换文本
        if self.is_traditional:
            info = self.convert_text(info, True)
        else:
            info = self.convert_text(info, False)
            
        self.display_text.insert(tk.END, f"{info}\n")
        
        # 构造更精确的搜索关键词
        search_parts = []
        if emperor['dynasty']:
            search_parts.append(emperor['dynasty'])
        if emperor['title']:
            search_parts.append(emperor['title'])
        if emperor['name']:
            search_parts.append(emperor['name'])
        
        search_term = ' '.join(search_parts)
        
        # URL编码搜索关键词
        from urllib.parse import quote
        encoded_term = quote(search_term)
        if can_access_google:
            # 使用Google搜索，添加中文参数
            print("使用Google搜索")
            url = f"https://www.google.com/search?q={encoded_term}&hl=zh-CN&lr=lang_zh-CN"
        # 使用中文版Bing搜索链接，添加语言和区域参数
        else:
            url = f"https://cn.bing.com/search?q={encoded_term}&setlang=zh-CN&setmkt=zh-CN"
        # 插入链接
        link_text = "查看详细资料"
        if self.is_traditional:
            link_text = self.convert_text(link_text, True)
        
        # 获取当前插入位置
        start_index = self.display_text.index("end-1c linestart")
        self.display_text.insert(tk.END, link_text + "\n\n")
        end_index = f"{start_index} + {len(link_text)}c"
        
        # 为每个接创建独立的标签
        link_tag = f"link_{url}"
        hover_tag = f"hover_{url}"  # 新增：每个链接独立的悬停样式标签
        
        # 配置标签样式
        self.display_text.tag_configure(hover_tag, 
            font=('KaiTi', 12),
            foreground="#1565C0",
            underline=1
        )
        
        # 添加标签
        self.display_text.tag_add(link_tag, start_index, end_index)
        self.display_text.tag_add("hyperlink", start_index, end_index)
        
        # 添加鼠标悬停效果
        def on_link_enter(event):
            self.display_text.config(cursor="hand2")
            # 只改变当前链接的样式
            self.display_text.tag_remove("hyperlink", start_index, end_index)
            self.display_text.tag_add(hover_tag, start_index, end_index)
            
        def on_link_leave(event):
            self.display_text.config(cursor="")
            # 恢复原始样式
            self.display_text.tag_remove(hover_tag, start_index, end_index)
            self.display_text.tag_add("hyperlink", start_index, end_index)
        
        # 绑定事件
        self.display_text.tag_bind(link_tag, "<Button-1>", 
            lambda e: webbrowser.open(url))
        self.display_text.tag_bind(link_tag, "<Enter>", on_link_enter)
        self.display_text.tag_bind(link_tag, "<Leave>", on_link_leave)

    def generate_random_emperor(self):
        """生成一位随机皇帝并显示"""
        if not self.generator.all_emperors:
            messagebox.showerror("错误", "皇帝据未加载。")
            return
        emperor = self.generator.generate_random_emperor()
        self.display_text.delete(1.0, tk.END)
        self.display_text.insert(tk.END, "随机生成的皇帝：\n\n")
        self.insert_emperor_with_link(emperor)

    def generate_multiple_emperors(self):
        """生成多位随机皇帝并显示"""
        def submit():
            count_str = entry.get()
            try:
                count = int(count_str)
                if count <= 0:
                    raise ValueError
                if count > len(self.generator.all_emperors):
                    messagebox.showwarning("警告", f"最多只能生成{len(self.generator.all_emperors)}位帝。")
                    count = len(self.generator.all_emperors)
                emperors = self.generator.generate_multiple_emperors(count)
                self.display_text.delete(1.0, tk.END)
                self.display_text.insert(tk.END, f"随机生成的{len(emperors)}位皇帝：\n\n")
                for i, emp in enumerate(emperors, 1):
                    self.display_text.insert(tk.END, f"第{i}位：\n")
                    self.insert_emperor_with_link(emp)
                popup.destroy()
            except ValueError:
                messagebox.showerror("输入错误", "请输入一个有效的正整数")

        popup = self.create_popup("生成多位皇帝")
        
        ttk.Label(
            popup, 
            text="请输入想成的皇帝数量：", 
            font=self.button_font
        ).pack(pady=20)
        
        entry = ttk.Entry(
            popup, 
            font=self.text_font,
            width=20
        )
        entry.pack(pady=15)
        
        submit_button = ttk.Button(
            popup, 
            text="生成", 
            command=submit,
            width=15
        )
        submit_button.pack(pady=15)

    def query_emperors_by_dynasty(self):
        """按朝代查询皇帝"""
        popup = self.create_popup("按朝代查询皇帝")
        
        def submit():
            nonlocal popup
            selected_dynasty = combo.get()
            if not selected_dynasty:
                error_msg = "请选择一个朝代。"
                if self.is_traditional:
                    error_msg = self.convert_text(error_msg, True)
                messagebox.showerror("选择错误", error_msg)
                return
            
            self.display_text.delete(1.0, tk.END)
            
            # 处理时间轴选项
            if selected_dynasty == "时间轴" or selected_dynasty == self.convert_text("时间轴", True):
                self.show_dynasty_timeline()
            elif selected_dynasty == "总览" or selected_dynasty == self.convert_text("总览", True):
                # 显示皇帝列表
                title = "历代皇帝总览：\n\n"
                if self.is_traditional:
                    title = self.convert_text(title, True)
                self.display_text.insert(tk.END, title, "section_title")
                
                # 使用集合去重
                displayed_emperors = set()
                
                for dynasty in self.generator.get_dynasties_list():
                    emperors = self.generator.get_emperors_by_dynasty(dynasty)
                    if emperors:
                        dynasty_title = f"【{dynasty}】\n"
                        if self.is_traditional:
                            dynasty_title = self.convert_text(dynasty_title, True)
                        self.display_text.insert(tk.END, dynasty_title, "dynasty_title")
                        
                        for emp in emperors:
                            # 创建唯一标识
                            emp_id = f"{emp['title']}_{emp['name']}"
                            if emp_id not in displayed_emperors:
                                displayed_emperors.add(emp_id)
                                if emp['name']:
                                    emp_text = f"- {emp['title']}（{emp['name']}）\n"
                                else:
                                    emp_text = f"- {emp['title']}\n"
                                if self.is_traditional:
                                    emp_text = self.convert_text(emp_text, True)
                                self.display_text.insert(tk.END, emp_text)
                        self.display_text.insert(tk.END, "\n")
            else:
                # 显示单个朝代的皇帝列表
                emperors = self.generator.get_emperors_by_dynasty(selected_dynasty)
                if emperors:
                    title = f"【{selected_dynasty}】皇帝列表：\n\n"
                    if self.is_traditional:
                        title = self.convert_text(title, True)
                    self.display_text.insert(tk.END, title, "section_title")
                    
                    # 使用集合去重
                    displayed_emperors = set()
                    for emp in emperors:
                        emp_id = f"{emp['title']}_{emp['name']}"
                        if emp_id not in displayed_emperors:
                            displayed_emperors.add(emp_id)
                            self.insert_emperor_with_link(emp)
                            self.display_text.insert(tk.END, "\n")
                else:
                    msg = f"未找到{selected_dynasty}的皇帝记录。"
                    if self.is_traditional:
                        msg = self.convert_text(msg, True)
                    self.display_text.insert(tk.END, msg)
            
            popup.destroy()
        
        # 创建界面元素
        ttk.Label(
            popup, 
            text="请选择朝代：", 
            font=self.button_font
        ).pack(pady=20)
        
        # 在朝代列表开头添加"时间轴"和"总览"选项
        dynasties = ["时间轴", "总览"] + self.generator.get_dynasties_list()
        combo = ttk.Combobox(
            popup, 
            values=dynasties, 
            state="readonly", 
            font=self.text_font,
            width=20
        )
        combo.pack(pady=15)
        combo.set("时间轴")  # 默认选中时间轴选项
        
        submit_button = ttk.Button(
            popup, 
            text="查询", 
            command=submit,
            width=15
        )
        submit_button.pack(pady=15)

    def _on_enter(self, event):
        self.display_text.config(cursor="hand2")

    def _on_leave(self, event):
        self.display_text.config(cursor="")

    def _on_click(self, event):
        # 获取点击位置的标签
        for tag in self.display_text.tag_names(tk.CURRENT):
            if tag.startswith("link_"):
                url = tag.replace("link_", "")
                import webbrowser
                webbrowser.open(url)

    def create_popup(self, title, width=400, height=250):
        """创建统一样式的弹窗"""
        popup = tk.Toplevel(self.root)
        if self.is_traditional:
            title = self.convert_text(title, True)
        popup.title(title)
        popup.geometry(f"{width}x{height}")
        popup.resizable(False, False)
        
        # 设置弹窗图标
        if self.has_icon:
            icon_path = self.get_icon_path()
            if icon_path:
                try:
                    popup.iconbitmap(icon_path)
                except Exception as e:
                    print(f"无法为弹窗加载图标: {e}")
        
        # 设置为模态窗口
        popup.grab_set()
        
        return popup
    def show_chat_window(self):
        """显示聊天窗口"""
        # 检查chat_window是否存在且窗口是否仍然有效
        if hasattr(self, 'chat_window') and self.chat_window is not None:
            try:
                # 尝试访问窗口属性来检查窗口是否仍然存在
                if self.chat_window.window.winfo_exists():
                    self.chat_window.window.lift()  # 窗口存在，将其提升到前面
                    self.chat_window.window.focus_force()
                    return
            except (AttributeError):
                # 如果窗口已被销毁，将chat_window设为None
                self.chat_window = None
        
        # 如果没有有效的聊天窗口，创建新窗口
        try:
            api_key = 'sk-0937b0ede5ea49ae9ceaa9cecfe8a690'
            self.chat_window = AIChatWindow(self.root, api_key)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开聊天窗口：{str(e)}")
    def get_icon_path(self):
        """获取图标的正确路径"""
        try:
            if getattr(sys, 'frozen', False):
                # 打后的径
                base_path = sys._MEIPASS
            else:
                # 开发环境路
                base_path = os.path.abspath(".")
            
            return os.path.join(base_path, "assets", "images", "seal.ico")
        except Exception as e:
            print(f"无法获取图标路径: {e}")
            return None

    def search_emperor(self):
        """搜索皇帝"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning(
                "提示", 
                self.convert_text("请输入搜索关键词", self.is_traditional)
            )
            return
        
        # 转换关键词（同时支持繁简体搜索）
        traditional_keyword = self.convert_text(keyword, True)
        simplified_keyword = self.convert_text(keyword, False)
        
        results = []
        for emperor in self.generator.all_emperors:
            # 在标题、名字和朝代中搜索（支持繁简体）
            searchable_fields = [
                (emperor['title'], self.convert_text(emperor['title'], True)),
                (emperor['name'], self.convert_text(emperor['name'], True)),
                (emperor['dynasty'], self.convert_text(emperor['dynasty'], True))
            ]
            
            # 如果任何字段包含关键词（繁体或简体），添加到结果中
            if any(keyword in field[0] or keyword in field[1] or 
                  traditional_keyword in field[0] or traditional_keyword in field[1] or
                  simplified_keyword in field[0] or simplified_keyword in field[1]
                  for field in searchable_fields if field[0]):
                results.append(emperor)
        
        # 显示搜索结果
        self.display_text.delete(1.0, tk.END)
        if results:
            title = f"找到 {len(results)} 位相关皇帝：\n\n"
            if self.is_traditional:
                title = self.convert_text(title, True)
            self.display_text.insert(tk.END, title, "section_title")
            
            for emp in results:
                self.insert_emperor_with_link(emp)
                self.display_text.insert(tk.END, "\n")
        else:
            msg = "未找到相关结果。"
            if self.is_traditional:
                msg = self.convert_text(msg, True)
            self.display_text.insert(tk.END, msg)

    def show_dynasty_timeline(self):
        """显示朝代时间轴"""
        # 定义主要朝代的起止时间
        DYNASTY_YEARS = [
            ("秦朝", "前221年-前206年"),
            ("西汉", "前202年-公元8年"),
            ("新朝", "9年-23年"),
            ("东汉", "25年-220年"),
            ("曹魏", "220年-265年"),
            ("蜀汉", "221年-263年"),
            ("东吴", "222年-280年"),
            ("西晋", "265年-316年"),
            ("东晋", "317年-420年"),
            ("刘宋", "420年-479年"),
            ("南齐", "479年-502年"),
            ("南梁", "502年-557年"),
            ("陈  ", "557年-589年"),
            ("北魏", "386年-534年"),
            ("东魏", "534年-550年"),
            ("西魏", "535年-557年"),
            ("北齐", "550年-577年"),
            ("北周", "557年-581年"),
            ("隋朝", "581年-619年"),
            ("唐朝", "618年-907年"),
            ("后梁", "907年-923年"),
            ("后唐", "923年-936年"),
            ("后晋", "936年-947年"),
            ("后汉", "947年-951年"),
            ("后周", "951年-960年"),
            ("北宋", "960年-1127年"),
            ("辽  ", "916年-1125年"),
            ("金  ", "1115年-1234年"),
            ("南宋", "1127年-1279年"),
            ("元朝", "1271年-1368年"),
            ("明朝", "1368年-1644年"),
            ("大顺", "1644年"),
            ("南明", "1644年-1662年"),
            ("清朝", "1644年-1912年")
        ]
        
        # 在文本框中显示时间轴
        self.display_text.delete(1.0, tk.END)
        
        # 添加标题
        title = "历代王朝时间轴\n\n"
        if self.is_traditional:
            title = self.convert_text(title, True)
        self.display_text.insert(tk.END, title, "section_title")
        
        # 添时间轴内容
        for dynasty, years in DYNASTY_YEARS:
            # 朝代名称和年份
            line = f"{dynasty}  【{years}】\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert(tk.END, line, "timeline_entry")
        
        # 添加注释
        note = "\n注：以上时间均为公历纪年，部分时期存在政权并立情况，仅供参考。\n"
        if self.is_traditional:
            note = self.convert_text(note, True)
        self.display_text.insert(tk.END, note, "note")

    def create_advanced_search_dialog(self):
        """创建高级搜索对话框"""
        # 使用create_popup方法创建窗口，这样会自动设置图标
        dialog = self.create_popup(
            "高级搜索" if not self.is_traditional else "進階搜索",
            width=400,
            height=600  # 增加高度以容纳排序���项
        )
        
        # 搜索条件框架
        search_frame = ttk.LabelFrame(
            dialog, 
            text="搜索条件" if not self.is_traditional else "搜索條件", 
            padding=10
        )
        search_frame.pack(fill="x", padx=10, pady=5)
        
        # 搜索字段 - 使用字典方便繁简转换
        fields = {
            'dynasty': '朝代',
            'title': '称号' if not self.is_traditional else '稱號',
            'name': '名讳' if not self.is_traditional else '名諱',
            'temple_name': '庙号' if not self.is_traditional else '廟號',
            'posthumous_name': '谥号' if not self.is_traditional else '謚號',
            'reign_period': '在位时间' if not self.is_traditional else '在位時間',
            'era_names': '年號' if self.is_traditional else '年号'
        }
        
        entries = {}
        for key, label in fields.items():
            frame = ttk.Frame(search_frame)
            frame.pack(fill="x", pady=2)
            
            # 使用微软雅黑字体的标签
            label = tk.Label(
                frame, 
                text=f"{label}:",
                font=('微软雅黑', 11),
                bg='#F5E6CB',  # 保持背景色一致
                anchor='e',    # 右对齐
                width=8        # 固定宽度确保对齐
            )
            label.pack(side="left", padx=5)
            
            # 输入框也使用相同的字体
            entry = ttk.Entry(
                frame,
                font=('微软雅黑', 11)
            )
            entry.pack(side="left", fill="x", expand=True, padx=5)
            entries[key] = entry
        
        # 搜索选项框架
        options_frame = ttk.LabelFrame(
            dialog, 
            text="搜索选项" if not self.is_traditional else "搜索選項", 
            padding=10
        )
        options_frame.pack(fill="x", padx=10, pady=5)
        
        # 单按钮也使用相同字体
        match_var = tk.StringVar(value="any")
        ttk.Radiobutton(
            options_frame, 
            text="匹配任意条件" if not self.is_traditional else "匹配任意條件", 
            variable=match_var, 
            value="any",
            style='Custom.TRadiobutton'  # 使用自定义样式
        ).pack(anchor="w")
        ttk.Radiobutton(
            options_frame, 
            text="匹配所有条件" if not self.is_traditional else "匹配所有條件", 
            variable=match_var, 
            value="all",
            style='Custom.TRadiobutton'
        ).pack(anchor="w")
        
        # 复选也使用相同字体
        case_sensitive = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, 
            text="区分大小写" if not self.is_traditional else "區分大小寫", 
            variable=case_sensitive,
            style='Custom.TCheckbutton'
        ).pack(anchor="w")
        
        # 添加排序选项框架
        sort_frame = ttk.LabelFrame(
            dialog,
            text="排序方式" if not self.is_traditional else "排序方式",
            padding=10
        )
        sort_frame.pack(fill="x", padx=10, pady=5)
        
        # 排序选项
        self.sort_var = tk.StringVar(value='dynasty')
        sort_options = [
            ('按朝代排序', 'dynasty'),
            ('按年代排序', 'year'),
        #    ('按名字排序', 'name'),
        #    ('按称号排序', 'title'),
            ('按在位时间', 'reign_length')  # 新增选项
        ]
        
        # 转换排序项文本
        if self.is_traditional:
            sort_options = [
                ('按朝代排序', 'dynasty'),
                ('按年代排序', 'year'),
             #   ('按名諱排序', 'name'),
             #   ('按稱號排序', 'title'),
                ('按在位時間', 'reign_length')  # 新增选项
            ]
        
        # 保存排序按钮的引用以便切换繁简体
        self.sort_buttons = []
        for text, value in sort_options:
            rb = ttk.Radiobutton(
                sort_frame,
                text=text,
                variable=self.sort_var,
                value=value,
                style='Custom.TRadiobutton'
            )
            rb.pack(anchor="w", pady=2)
            self.sort_buttons.append(rb)
        
        def do_search():
            # 获取搜索条件
            criteria = {k: v.get().strip() for k, v in entries.items()}
            
            # 执行搜索
            results = self.advanced_search(
                criteria, 
                match_all=match_var.get() == "all",
                case_sensitive=case_sensitive.get()
            )
            
            # 对结果进行排序
            sorted_results = self.sort_results(results, self.sort_var.get())
            
            # 显示结果
            self.display_search_results(sorted_results)
            
            # 关闭对话框
            dialog.destroy()
        
        # 按钮框架
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # 按钮使用相同字体
        search_btn = ttk.Button(
            button_frame, 
            text="搜索" if not self.is_traditional else "搜索", 
            command=do_search,
            style='Custom.TButton'
        )
        search_btn.pack(side="right")
        
        # 取消按钮
        cancel_btn = ttk.Button(
            button_frame, 
            text="取消" if not self.is_traditional else "取消", 
            command=dialog.destroy,
            style='Custom.TButton'
        )
        cancel_btn.pack(side="right", padx=5)
        
        # 配置自定义样式
        style = ttk.Style()
        style.configure('Custom.TRadiobutton', font=('微软雅黑', 11))
        style.configure('Custom.TCheckbutton', font=('微软雅黑', 11))
        style.configure('Custom.TButton', font=('微软雅黑', 11))
        
        # 保存对话框引用，以便在切换繁简时更新
        self.advanced_search_dialog = dialog
        self.advanced_search_widgets = {
            'title': dialog.title,
            'search_frame': search_frame,
            'options_frame': options_frame,
            'fields': fields,
            'labels': [child for frame in search_frame.winfo_children() 
                      for child in frame.winfo_children() 
                      if isinstance(child, tk.Label)],  # 保存所有标签引用
            'match_buttons': [child for child in options_frame.winfo_children() 
                            if isinstance(child, ttk.Radiobutton)],
            'case_button': [child for child in options_frame.winfo_children() 
                           if isinstance(child, ttk.Checkbutton)][0],
            'search_btn': search_btn,
            'cancel_btn': cancel_btn,
            'sort_frame': sort_frame,
            'sort_buttons': self.sort_buttons
        }

    def advanced_search(self, criteria, match_all=False, case_sensitive=False):
        """执行高级搜索"""
        results = []
        
        # 过滤空条件
        valid_criteria = {k: v for k, v in criteria.items() if v}
        if not valid_criteria:
            return results
        
        for emperor in self.generator.all_emperors:
            matches = []
            for field, search_term in valid_criteria.items():
                value = str(emperor.get(field, ''))
                
                # 特殊处理在位时间搜索
                if field == 'reign_period':
                    try:
                        # 处理搜索区间
                        if '-' in search_term:  # 用户输入了时间范围
                            search_start, search_end = map(
                                lambda x: int(x.replace('年', '')), 
                                search_term.split('-')
                            )
                        else:  # 用户输入单一年份
                            search_start = search_end = int(search_term.replace('年', ''))
                        
                        # 处理皇帝在位时间
                        reign_period = value
                        if '-' in reign_period:  # 皇帝有在位时间范围
                            reign_start, reign_end = map(
                                lambda x: int(x.replace('年', '')), 
                                reign_period.split('-')
                            )
                        else:  # 皇帝只有单一年份记录
                            reign_start = reign_end = int(reign_period.replace('��', ''))
                        
                        # 检查时间范围是否重叠
                        # 两个范围重叠的条件：个范围的开始不在另一个范围的结束之后
                        match = not (search_end < reign_start or search_start > reign_end)
                        
                    except (ValueError, IndexError):
                        # 如果年份解析失败，使用默认的文本匹配
                        if not case_sensitive:
                            value = value.lower()
                            search_term = search_term.lower()
                        match = search_term in value
                else:
                    # 其他字段使用普通文本匹配
                    if not case_sensitive:
                        value = value.lower()
                        search_term = search_term.lower()
                        
                    # 支持模糊匹配
                    if '*' in search_term or '?' in search_term:
                        import fnmatch
                        match = fnmatch.fnmatch(value, search_term)
                    else:
                        match = search_term in value
                        
                matches.append(match)
            
            # 根据匹配模式决定是否添加到结果
            if match_all and all(matches) or not match_all and any(matches):
                results.append(emperor)
        
        return results

    def display_search_results(self, results):
        """显示搜索结果"""
        self.display_text.delete(1.0, tk.END)
        
        if not results:
            msg = "未找到匹配的结果"
            if self.is_traditional:
                msg = self.convert_text(msg, True)
            self.display_text.insert(tk.END, msg)
            return
        
        title = f"找到 {len(results)} 条匹配结果：\n\n"
        if self.is_traditional:
            title = self.convert_text(title, True)
        self.display_text.insert(tk.END, title, "section_title")
        
        for emperor in results:
            self.insert_emperor_with_link(emperor)

    def search_emperor(self):
        """搜索皇帝(原有的简单搜索功能改进)"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            return
            
        # 保��搜索历史
        self.save_search_history(keyword)
        
        # 使用高级搜索功能进行简单搜索
        results = self.advanced_search({
            'dynasty': keyword,
            'title': keyword,
            'name': keyword,
            'temple_name': keyword,
            'posthumous_name': keyword,
            'era_names': keyword
        }, match_all=False)
        
        self.display_search_results(results)

    def save_search_history(self, keyword):
        """保存搜索历史"""
        # 从文件加载现有历史
        try:
            with open('search_history.txt', 'r', encoding='utf-8') as f:
                history = f.read().splitlines()
        except FileNotFoundError:
            history = []
        
        # 添加新关键词到历史记录开头
        if keyword in history:
            history.remove(keyword)
        history.insert(0, keyword)
        
        # 只保留最近的20条记录
        history = history[:20]
        
        # 保存历史记录
        with open('search_history.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(history))

    def sort_results(self, results, sort_by):
        """对搜索结果进行排序"""
        def get_year(reign_period):
            """从在位时间中提取年份"""
            try:
                if '-' in reign_period:
                    return int(reign_period.split('-')[0].replace('年', ''))
                return int(reign_period.replace('年', ''))
            except (ValueError, IndexError):
                return 0
        
        def get_dynasty_order(dynasty):
            """获取朝代的顺序权重"""
            dynasty_order = [
                "秦朝",
                "西汉", "新朝", "东汉",
                "曹魏", "蜀汉", "东吴",  # 三国
                "西晋", "东晋",
                "刘宋", "齐", "梁", "陈",  # 南朝
                "北魏", "东魏", "西魏", "北齐", "北周",  # 北朝 - 添加了缺失的朝代
                "隋朝",
                "唐朝",
                "后梁", "后唐", "后晋", "后汉", "后周",  # 五代
                "北宋", "辽", "金", "南宋",
                "元朝",
                "明朝", "大顺","南明",
                "清朝"
            ]
            # 返回朝代在表中的索引，如果不在列表中返回最大值
            try:
                return dynasty_order.index(dynasty)
            except ValueError:
                return len(dynasty_order)
        
        if sort_by == 'year':
            # 按在位时间排序
            results.sort(key=lambda x: get_year(x.get('reign_period', '')))
        elif sort_by == 'dynasty':
            # 按朝代顺序排序，同朝代内按在位时间排序
            results.sort(key=lambda x: (
                get_dynasty_order(x.get('dynasty', '')),
                get_year(x.get('reign_period', ''))
            ))
        elif sort_by == 'name':
            # 按名字排序
            results.sort(key=lambda x: x.get('name', ''))
        elif sort_by == 'title':
            # 按称号排序
            results.sort(key=lambda x: x.get('title', ''))
        elif sort_by == 'reign_length':
            # 解析在位时间并计算时长
            def get_reign_length(emperor):
                if 'reign_period' not in emperor:
                    return 0
                reign_info = emperor['reign_period']
                try:
                    # 提取年份
                    years = re.findall(r'(\d+)年', reign_info)
                    if len(years) >= 2:
                        start_year = int(years[0])
                        end_year = int(years[1])
                        return max(end_year - start_year,start_year - end_year)
                    return 0
                except:
                    return 0
            
            results.sort(key=get_reign_length, reverse=True)
        
        return results

    def resort_results(self):
        """重新排序当前显示的结果"""
        # 获取当前文本框中的内容
        current_text = self.display_text.get("1.0", "end-1c")
        if not current_text.strip():
            return
            
        # 解析当前显示的皇帝信息
        emperors = []
        current_emperor = {}
        
        # 按段落分割，跳过标题
        paragraphs = current_text.split('\n\n')
        count = 0  # 记录实际的皇帝数量
        
        for paragraph in paragraphs:
            if not paragraph.strip() or "随机生成" in paragraph:
                continue
                
            current_emperor = {}
            lines = paragraph.split('\n')
            
            # 跳过序号行
            for line in lines:
                if ':' in line or '：' in line:
                    if '第' in line and '位' in line:
                        continue
                        
                    key, value = line.replace('：',':').split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 映射显示文本到实际字段
                    field_mapping = {
                        '朝代': 'dynasty',
                        '政权': 'dynasty',
                        '称号': 'title',
                        '稱號': 'title',
                        '名讳': 'name',
                        '名諱': 'name',
                        '在位': 'reign_period',
                        '庙号': 'temple_name',
                        '廟號': 'temple_name',
                        '谥号': 'posthumous_name',
                        '諡號': 'posthumous_name',
                        '年号': 'era_names',  # 添加年号映射
                        '年號': 'era_names'   # 添加繁体年号映射
                    }
                    
                    if key in field_mapping:
                        current_emperor[field_mapping[key]] = value
            
            if current_emperor:
                emperors.append(current_emperor)
                count += 1
        
        if not emperors:  # 如果没有解析到皇帝信息，直接返回
            return
            
        # 根据排序方式进行排序
        sort_type = self.sort_var.get()
        if sort_type == 'year':
            def get_start_year(emp):
                reign = emp.get('reign_period', '')
                try:
                    # 处理年份字串
                    year_str = reign.split('-')[0].strip()
                    
                    # 检查是否是公元前年份
                    if '前' in year_str:
                        # 提取公元前年份的数字，并转为负数
                        year = -int(''.join(filter(str.isdigit, year_str)))
                    else:
                        # 处理公元年份
                        year = int(''.join(filter(str.isdigit, year_str)))
                    return year
                except:
                    return 9999  # 如果无法解析年份，放到最后
            sorted_emperors = sorted(emperors, key=get_start_year)
        elif sort_type == 'name':
            # 按名字排序
            sorted_emperors = sorted(emperors, key=lambda x: x.get('name', ''))
        elif sort_type == 'title':
            # 按称号排序
            sorted_emperors = sorted(emperors, key=lambda x: x.get('title', ''))
        elif sort_type == 'dynasty':
            # 按朝代顺序排序，同朝代内按在位时间排序
            def get_dynasty_order(dynasty):
                """获取朝代的顺序权重"""
                dynasty_order = [
                    "秦朝",
                    "西汉", "新朝", "东汉",
                    "曹魏", "蜀汉", "东吴",  # 三国
                    "西晋", "东晋",
                    "刘宋", "南齐", "南梁", "陈",  # 南朝
                    "北魏", "东魏", "西魏", "北齐", "北周",  # 北朝
                    "隋朝",
                    "唐朝",
                    "后梁", "后唐", "后晋", "后汉", "后周",  # 五代
                    "北宋", "辽", "金", "南宋",
                    "元朝",
                    "明朝", "大顺", "南明",
                    "清朝"
                ]
                # 处理可能的朝代名称变体
                dynasty = dynasty.replace("政权", "").replace("朝", "").strip()
                for d in dynasty_order:
                    if dynasty in d:
                        return dynasty_order.index(d)
                return len(dynasty_order)
            
            def get_start_year(emp):
                reign = emp.get('reign_period', '')
                try:
                    # 处理年份字符串
                    year_str = reign.split('-')[0].strip()
                    
                    # 检查是否是公元前年份
                    if '前' in year_str:
                        # 提取公元前年份的数字，并转为负数
                        year = -int(''.join(filter(str.isdigit, year_str)))
                    else:
                        # 处理公元年份
                        year = int(''.join(filter(str.isdigit, year_str)))
                    return year
                except:
                    return 9999  # 如果无法解析年份，放到最后
            
            def get_sort_key(emp):
                dynasty = emp.get('dynasty', '')
                return (get_dynasty_order(dynasty), get_start_year(emp))
            
            sorted_emperors = sorted(emperors, key=get_sort_key)
        elif sort_type == 'reign_length':
            # 解析在位时间并计算时长
            def get_reign_length(emperor):
                if 'reign_period' not in emperor:
                    return 0
                reign_info = emperor['reign_period']
                try:
                    # 提取年份
                    years = re.findall(r'(\d+)年', reign_info)
                    if len(years) >= 2:
                        start_year = int(years[0])
                        end_year = int(years[1])
                        return max(end_year - start_year,start_year - end_year)
                    return 0
                except:
                    return 0
            
            sorted_emperors = sorted(emperors, key=get_reign_length, reverse=True)
        
        # 清空文本框前配置超链接样式
        self.display_text.tag_configure("hyperlink", 
            foreground="#0066cc",
            underline=1
        )
        
        # 清空文本框
        self.display_text.delete("1.0", "end")
        
        # 显示排序后的结果
        title = f"随机生成的{count}位皇帝：\n\n"
        if self.is_traditional:
            title = self.convert_text(title, True)
        self.display_text.insert("end", title)
        
        # 显示每个皇帝的信息
        for i, emperor in enumerate(sorted_emperors, 1):
            # 添加序号
            number = f"第{i}位：\n"
            if self.is_traditional:
                number = self.convert_text(number, True)
            self.display_text.insert("end", number)
            
            # 显示皇帝信息
            for field, value in emperor.items():
                field_display = {
                    'dynasty': '朝代',
                    'title': '称号',
                    'name': '名讳',
                    'reign_period': '在位',
                    'temple_name': '庙号',
                    'posthumous_name': '谥号',
                    'era_names': '年号'
                }
                
                if self.is_traditional:
                    field_display = {k: self.convert_text(v, True) for k, v in field_display.items()}
                
                if field in field_display:
                    self.display_text.insert("end", f"{field_display[field]}：{value}\n")
            
            # 添加查看详细资料的链接
            link_text = "查看詳細資料\n" if self.is_traditional else "查看详细资料\n"
            start_index = self.display_text.index("end-1c")
            self.display_text.insert("end", link_text, ("hyperlink", f"link_{i}"))
            end_index = self.display_text.index("end-1c")
            
            # 构造搜索关键词
            search_term = f"{emperor['dynasty']}{emperor['title']}"
            if emperor['name']:
                search_term += f"{emperor['name']}"
            url = f"https://www.bing.com/search?q={search_term}"
            
            # 为每个链接绑定事件
            self.display_text.tag_bind(f"link_{i}", "<Button-1>", 
                lambda e, url=url: webbrowser.open(url))
            self.display_text.tag_bind(f"link_{i}", "<Enter>", 
                lambda e: self.display_text.configure(cursor="hand2"))
            self.display_text.tag_bind(f"link_{i}", "<Leave>", 
                lambda e: self.display_text.configure(cursor=""))
            
            self.display_text.insert("end", "\n")

    def analyze_emperors(self):
        """统计分析皇帝数据"""
        stats = {
            'dynasty_stats': {},
            'reign_stats': {
                'shortest': None,
                'longest': None,
                'distribution': {
                    "0-9年": 0,
                    "10-19年": 0,
                    "20-29年": 0,
                    "30-39年": 0,
                    "40-49年": 0,
                    "50-59年": 0,
                    "60年以上": 0
                }
            },
            'name_stats': {},
            'era_name_stats': {},
            'temple_name_stats': {},  # 新增：庙号统计
            'posthumous_name_stats': {}  # 新增：谥号统计
        }
        
        for emperor in self.generator.all_emperors:
            # 1. 朝代统计
            dynasty = emperor['dynasty']
            if dynasty not in stats['dynasty_stats']:
                stats['dynasty_stats'][dynasty] = {
                    'count': 0,
                    'dynasty_start': float('inf'),  # 初始化为正无穷
                    'dynasty_end': float('-inf'),   # 初始化为负无穷
                    'avg_reign': 0
                }
            stats['dynasty_stats'][dynasty]['count'] += 1
            
            # 2. 计算朝代的起始年和结束年
            if emperor['reign_period']:
                try:
                    # 解析在位时期
                    period = emperor['reign_period'].strip('{}')
                    
                    # 处理可能只有单一年份的情况
                    if '-' in period:
                        start_str, end_str = period.split('-')
                    else:
                        start_str = end_str = period
                    
                    def parse_year(year_str):
                        year_str = year_str.strip()
                        if year_str.startswith('前'):
                            return -int(year_str[1:-1])  # 去掉"前"和"年"，转为负数
                        else:
                            return int(year_str[:-1])  # 去掉"年"
                    
                    start_year = parse_year(start_str)
                    end_year = parse_year(end_str)
                    
                    # 更新朝代的起始年和结束年
                    if start_year < stats['dynasty_stats'][dynasty]['dynasty_start']:
                        stats['dynasty_stats'][dynasty]['dynasty_start'] = start_year
                    if end_year > stats['dynasty_stats'][dynasty]['dynasty_end']:
                        stats['dynasty_stats'][dynasty]['dynasty_end'] = end_year
                    
                    # 计算在位时长（包含起始年）
                    reign_years = end_year - start_year + 1 if end_year >= start_year else start_year - end_year + 1
                    if reign_years > 0:
                        if not stats['reign_stats']['longest'] or reign_years > stats['reign_stats']['longest']['years']:
                            stats['reign_stats']['longest'] = {
                                'emperor': emperor,
                                'years': reign_years
                            }
                        if not stats['reign_stats']['shortest'] or reign_years < stats['reign_stats']['shortest']['years']:
                            stats['reign_stats']['shortest'] = {
                                'emperor': emperor,
                                'years': reign_years
                            }
                        
                        # 统计在位时长分布
                        if reign_years >= 60:
                            range_key = "60年以上"
                        else:
                            range_key = f"{(reign_years//10)*10}-{(reign_years//10)*10+9}年"
                        if range_key in stats['reign_stats']['distribution']:
                            stats['reign_stats']['distribution'][range_key] += 1
                        else:
                            stats['reign_stats']['distribution'][range_key] = 1
                except Exception as e:
                    print(f"解析在位时长时出错: {emperor['reign_period']}，错误信息: {e}")
            
            # 3. 名字用字统计
            if emperor['name']:
                for char in emperor['name']:
                    stats['name_stats'][char] = stats['name_stats'].get(char, 0) + 1
            
            # 4. 年号用字统计
            if emperor['era_names']:
                for era_name in emperor['era_names']:
                    for char in era_name:
                        stats['era_name_stats'][char] = stats['era_name_stats'].get(char, 0) + 1
            
            # 5. 庙号用字统计           # 新增部分
            if emperor['temple_name']:
                for char in emperor['temple_name']:
                    stats['temple_name_stats'][char] = stats['temple_name_stats'].get(char, 0) + 1
            
            # 6. 谥号用字统计           # 新增部分
            if emperor['posthumous_name']:
                for char in emperor['posthumous_name']:
                    stats['posthumous_name_stats'][char] = stats['posthumous_name_stats'].get(char, 0) + 1
        
        # 计算各朝代平均在位时长（朝代总时长除以皇帝总数）
        for dynasty in stats['dynasty_stats']:
            dynasty_start = stats['dynasty_stats'][dynasty]['dynasty_start']
            dynasty_end = stats['dynasty_stats'][dynasty]['dynasty_end']
            count = stats['dynasty_stats'][dynasty]['count']
            
            if dynasty_start < float('inf') and dynasty_end > float('-inf'):
                dynasty_duration = dynasty_end - dynasty_start + 1  # 包含起始年
                stats['dynasty_stats'][dynasty]['avg_reign'] = dynasty_duration / count
            else:
                # 如果朝代的起始年或结束年未设置，可能是因为reign_period缺失或格式错误
                stats['dynasty_stats'][dynasty]['avg_reign'] = 0  # 或者根据需求设置为其他值
        
        # 显示统计分析结果
        self._display_analysis_results(stats)

    def _display_analysis_results(self, stats):
        """显示统计分析结果"""
        self.display_text.delete(1.0, tk.END)
        
        # 标题
        title = "皇帝数据统计分析\n"
        title += "_" * 32 + "\n\n"
        if self.is_traditional:
            title = self.convert_text(title, True)
        self.display_text.insert(tk.END, title)
        
        # 1. 总体统计
        total_count = sum(data['count'] for data in stats['dynasty_stats'].values())
        total_title = f"总体统计：\n共计{total_count}位皇帝\n"
        if self.is_traditional:
            total_title = self.convert_text(total_title, True)
        self.display_text.insert(tk.END, total_title + "\n")
        
        # 2. 朝代统计
        dynasty_title = "各朝代统计：\n"
        if self.is_traditional:
            dynasty_title = self.convert_text(dynasty_title, True)
        self.display_text.insert(tk.END, dynasty_title)
        
        # 按皇帝数量排序显示朝代统计
        sorted_dynasties = sorted(
            stats['dynasty_stats'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for dynasty, data in sorted_dynasties:
            line = f"▪ {dynasty}: {data['count']}位皇帝"
            if data['avg_reign'] > 0:
                line += f", 平均在位{data['avg_reign']:.1f}年"
            line += "\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert(tk.END, line)
        
        # 3. 名字用字统计
        name_title = "\n名讳常用字TOP50：\n"
        if self.is_traditional:
            name_title = self.convert_text(name_title, True)
        self.display_text.insert(tk.END, name_title)
        
        for i, (char, count) in enumerate(sorted(
            stats['name_stats'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert(tk.END, line)
        
        # 4. 年号用字统计
        era_title = "\n年号常用字TOP50：\n"
        if self.is_traditional:
            era_title = self.convert_text(era_title, True)
        self.display_text.insert(tk.END, era_title)
        
        for i, (char, count) in enumerate(sorted(
            stats['era_name_stats'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert(tk.END, line)
        
        # 5. 庙号用字统计           # 新增部分
        temple_title = "\n庙号常用字TOP50：\n"
        if self.is_traditional:
            temple_title = self.convert_text(temple_title, True)
        self.display_text.insert(tk.END, temple_title)
        
        for i, (char, count) in enumerate(sorted(
            stats['temple_name_stats'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert(tk.END, line)
        
        # 6. 谥号用字统计           # 新增部分
        posthumous_title = "\n谥号常用字TOP50：\n"
        if self.is_traditional:
            posthumous_title = self.convert_text(posthumous_title, True)
        self.display_text.insert(tk.END, posthumous_title)
        
        for i, (char, count) in enumerate(sorted(
            stats['posthumous_name_stats'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert(tk.END, line)

    def _calculate_reign_length(self, reign_period):
        """计算在位时长"""
        try:
            # 处理特殊情况：只有一年的情况
            if '-' not in reign_period:
                return 1
                
            start, end = reign_period.split('-')
            
            # 处理起始年份
            if '前' in start:
                start_year = -int(''.join(filter(str.isdigit, start)))
            else:
                start_year = int(''.join(filter(str.isdigit, start)))
                
            # 处理结束年份
            if '前' in end:
                end_year = -int(''.join(filter(str.isdigit, end)))
            else:
                end_year = int(''.join(filter(str.isdigit, end)))
                
            # 计算在位时长
            reign_length = max(end_year - start_year,start_year - end_year)
            if reign_length == 0:
                return 1  # 如果同年即位又退位，记为1年
            return abs(reign_length) + 1  # +1是因为包含起始年
            
        except Exception as e:
            print(f"计算在位时长出错: {reign_period}, 错误: {str(e)}")
            return 0

def main():
    root = tk.Tk()
    app = EmperorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()