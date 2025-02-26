# -*- coding: utf-8 -*-
import random
import re
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from customtkinter import CTk, CTkFrame, CTkLabel, CTkButton, CTkEntry, CTkToplevel, CTkTabview, CTkOptionMenu, CTkRadioButton, CTkCheckBox, CTkScrollbar
import os
import opencc
import sys
import webbrowser
import fnmatch
import threading
from openai import OpenAI
from ai_chat_window import AIChatWindow
from emperor_generator import EmperorGenerator
from data import emperor_text
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

can_access_google = None
import matplotlib

ctk.set_appearance_mode("light")  # Set to light mode for a modern look
ctk.set_default_color_theme("blue")  # Use blue as a base theme
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 使用黑体

class EmperorApp:
    def _move_window(self, direction):
        """移动窗口"""
        step = 20
        x, y = self.root.winfo_x(), self.root.winfo_y()
        
        if direction == 'left':
            x -= step
        elif direction == 'right':
            x += step
        elif direction == 'up':
            y -= step
        elif direction == 'down':
            y += step
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        self.root.geometry(f"+{x}+{y}")

    def _bind_arrow_keys(self):
        for direction, key in [('left', '<Left>'), ('right', '<Right>'), ('up', '<Up>'), ('down', '<Down>')]:
            self.root.bind(key, lambda e, d=direction: self._move_window(d))

    def __init__(self, root):
        self.root = root
        self.root.title("受命於天，既壽永昌")
        
        self.root.attributes('-alpha', 0.0)
        self.chat_window = None
        
        self.has_icon = False
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
                
            self.icon_path = os.path.join(base_path, "assets", "images", "seal.ico")
            self.root.iconbitmap(self.icon_path)
            self.has_icon = True
        except Exception as e:
            print(f"无法加载图标: {e}")
            messagebox.showerror("图标加载错误", "无法加载图标，请检查文件路径和文件格式。")
        
        window_width = 900  # 稍微增加窗口宽度以适应更大的字体
        window_height = 900  # 稍微增加窗口高度
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.generator = EmperorGenerator()
        
        self.setup_fonts()
        self.create_widgets()
        
        self.fade_in()
        self.check_vpn_status()
        
        self.root.bind('<Left>', lambda e: self._move_window('left'))
        self.root.bind('<Right>', lambda e: self._move_window('right'))
        self.root.bind('<Up>', lambda e: self._move_window('up'))
        self.root.bind('<Down>', lambda e: self._move_window('down'))
        
        # 添加一个属性用于跟踪当前显示的皇帝
        self.displayed_emperors = []

    def check_vpn_status(self):
        global can_access_google
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
        alpha = self.root.attributes('-alpha')
        if alpha < 1.0:
            alpha += 0.2
            self.root.attributes('-alpha', alpha)
            self.root.after(50, self.fade_in)

        self.generator.parse_emperor_data(emperor_text)
        self.is_traditional = False
        self.converter_t2s = opencc.OpenCC('t2s')
        self.converter_s2t = opencc.OpenCC('s2t')

    def setup_fonts(self):
        self.is_traditional = False
        # 字体放大到约30%-40%
        self.title_font = ('华文行楷', 22)  # 原16，放大到22
        self.button_font = ('华文行楷', 16)  # 原12，放大到16
        self.text_font = ('华文行楷', 16)    # 原12，放大到16

    def create_widgets(self):
        THEME_COLORS = {
            'primary': '#8B0000',     # 深红色：皇权
            'secondary': '#704214',   # 深褐色：历史沉淀
            'accent': '#DAA520',      # 古铜金：皇家气派
            'text': '#2B1B17',        # 墨黑色：典籍
            'bg': '#EBEBEB',          # 背景色
            'scrollbar_bg': '#D3D3D3',    # 现代灰色背景，略透明
            'scrollbar_button': '#A9A9A9', # 滑块默认颜色（深灰）
            'scrollbar_hover': '#FFD700',  # 滑块悬停时为亮金色，现代与古典结合
            'scrollbar_active': '#FF4500', # 滑块拖动时的活跃颜色（橘红）
        }

        # 主窗口使用 CTkFrame 保持 customtkinter 风格
        title_frame = ctk.CTkFrame(self.root, fg_color=THEME_COLORS['bg'])
        title_frame.pack(fill='x', pady=(25, 0))  # 增加pady以适应更大字体
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="皇帝生成器",
            font=('华文行楷', 50, 'bold'),  # 原36，放大到50
            text_color='#8B0000'
        )
        title_label.pack(pady=(12, 6))

        # 分隔线使用 CTkFrame 模拟
        separator_frame = ctk.CTkFrame(self.root, height=2, fg_color='#704214')
        separator_frame.pack(fill='x', padx=150, pady=(0, 25))

        # 控制框架
        control_frame = ctk.CTkFrame(self.root, fg_color=THEME_COLORS['bg'])
        control_frame.pack(fill='x', padx=25, pady=(0, 12))
        
        search_frame = ctk.CTkFrame(control_frame, fg_color=THEME_COLORS['bg'])
        search_frame.pack(side='left')
        
        self.search_label = ctk.CTkLabel(
            search_frame,
            text="搜索皇帝：",
            font=self.button_font,  # 使用放大的button_font (16)
            text_color=THEME_COLORS['text']
        )
        self.search_label.pack(side='left', padx=(0, 12))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            font=self.text_font,  # 使用放大的text_font (16)
            width=240,  # 增加宽度以适应更大字体
            fg_color='#FFF8DC',
            text_color=THEME_COLORS['text']
        )
        self.search_entry.pack(side='left')
        
        buttons_frame = ctk.CTkFrame(search_frame, fg_color=THEME_COLORS['bg'])
        buttons_frame.pack(side='left', padx=6)
        
        self.search_button = ctk.CTkButton(
            buttons_frame,
            text="搜索",
            command=self.search_emperor,
            font=('微软雅黑', 14),  # 原10，放大到14
            width=72,  # 增加宽度
            fg_color='#F5E6CB',
            text_color='#8B2323',
            hover_color='#DAA520'
        )
        self.search_button.pack(side='left', padx=6)
        
        self.advanced_search_button = ctk.CTkButton(
            buttons_frame,
            text="高级搜索",
            command=self.create_advanced_search_dialog,
            font=('微软雅黑', 14),  # 原10，放大到14
            width=96,  # 增加宽度
            fg_color='#F5E6CB',
            text_color='#8B2323',
            hover_color='#DAA520'
        )
        self.advanced_search_button.pack(side='left', padx=6)
        
        self.switch_button = ctk.CTkButton(
            control_frame,
            text="繁體",
            command=self.toggle_traditional,
            font=('微软雅黑', 14),  # 原10，放大到14
            width=72,  # 增加宽度
            fg_color='#F5E6CB',
            text_color='#8B2323',
            hover_color='#DAA520'
        )
        self.switch_button.pack(side='right')
        
        self.search_entry.bind('<Return>', lambda e: self.search_emperor())
        
        button_styles = [
            {
                "text": "随机生成一位皇帝",
                "command": self.generate_random_emperor,
                "bg": "#8B2323",
                "hover_bg": "#800000",
                "icon": ""
            },
            {
                "text": "随机生成多位皇帝",
                "command": self.generate_multiple_emperors,
                "bg": "#704214",
                "hover_bg": "#5C3317",
                "icon": ""
            },
            {
                "text": "按朝代查询皇帝",
                "command": self.query_emperors_by_dynasty,
                "bg": "#8B4513",
                "hover_bg": "#8B4500",
                "icon": ""
            }
        ]
        
        button_frame = ctk.CTkFrame(self.root, fg_color=THEME_COLORS['bg'])
        button_frame.pack(pady=25)
        
        for i, btn_style in enumerate(button_styles):
            btn = ctk.CTkButton(
                button_frame,
                text=f"{btn_style['icon']} {btn_style['text']}",
                command=btn_style["command"],
                font=('LiSu', 22),  # 原16，放大到22
                width=240,  # 增加宽度
                height=48,  # 增加高度
                fg_color=btn_style["bg"],
                text_color="white",
                hover_color=btn_style["hover_bg"]
            )
            btn.grid(row=0, column=i, padx=18, pady=6)

        # 排序和按钮区域
        sort_frame = ctk.CTkFrame(self.root, fg_color=THEME_COLORS['bg'])
        sort_frame.pack(fill="x", padx=12, pady=(6, 0))
        
        self.sort_label = ctk.CTkLabel(
            sort_frame,
            text="排序方式：",
            font=('微软雅黑', 15),  # 原9，放大到12
            text_color=THEME_COLORS['text']
        )
        self.sort_label.pack(side="left", padx=(0, 6))
        
        self.sort_var = ctk.StringVar(value='dynasty')
        sort_options = [
            ('按朝代', 'dynasty'),
            ('按年代', 'year'),
            ('按在位时间', 'reign_length')
        ]
        
        self.sort_buttons = []
        for text, value in sort_options:
            rb = ctk.CTkRadioButton(
                sort_frame,
                text=text,
                variable=self.sort_var,
                value=value,
                command=self.resort_results,
                font=('微软雅黑', 15),  # 原9，放大到12
                text_color=THEME_COLORS['text'],
                fg_color=THEME_COLORS['bg']
            )
            rb.pack(side="left", padx=6)
            self.sort_buttons.append(rb)
        
        self.analyze_button = ctk.CTkButton(
            sort_frame,
            text="统计分析",  # 固定文本
            command=self.analyze_emperors,
            font=('华文行楷', 22),  # 原16，放大到22
            fg_color='#E6D5AC',
            hover_color='#D4C391',
            text_color='#4A4A4A',
            corner_radius=6,
            border_width=1,
            border_color='#8B4513',
            width=120,  # 增加宽度
            height=38   # 增加高度
        )
        self.analyze_button.pack(side="right", padx=25)

        self.chat_button = ctk.CTkButton(
            sort_frame,
            text="AI助手",
            command=self.show_chat_window,
            font=('华文行楷', 22),  # 原16，放大到22
            fg_color='#2C3E50',
            hover_color='#34495E',
            text_color='#7DF9FF',
            corner_radius=8,
            border_width=2,
            border_color='#00CED1',
            width=120,  # 增加宽度
            height=38   # 增加高度
        )
        self.chat_button.pack(side="right", padx=6)
        
        text_frame = ctk.CTkFrame(self.root, fg_color=THEME_COLORS['bg'])
        text_frame.pack(padx=35, pady=25, fill="both", expand=True)
        
        # 使用 tk.Text 保持标签功能，并添加 customtkinter 滚动条
        self.display_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            width=65,
            height=22,
            font=('KaiTi', 26),  # 原16，放大到25
            bg='#FFF8DC',
            fg=THEME_COLORS['text'],
            relief="solid",
            borderwidth=1
        )
        
        # 添加 customtkinter 滚动条
        # scrollbar = ctk.CTkScrollbar(text_frame, orientation="vertical", command=self.display_text.yview)
        # scrollbar.pack(side="right", fill="y")
        # self.display_text.configure(yscrollcommand=scrollbar.set)
        
        # 改进后的代码
        scrollbar = ctk.CTkScrollbar(
            text_frame,
            orientation="vertical",
            command=self.display_text.yview,
            fg_color=THEME_COLORS['scrollbar_bg'],      # 滚动条背景色
            button_color=THEME_COLORS['scrollbar_button'],  # 滑块默认颜色
            button_hover_color=THEME_COLORS['scrollbar_hover'],  # 滑块悬停颜色
            border_spacing=2,                           # 滑块与边缘的间距
            minimum_pixel_length=22,                    # 滑块最小长度
            corner_radius=6,                            # 圆角半径，与按钮风格一致
            width=18                                    # 宽度稍增加，增强可操作性
        )
        scrollbar.pack(side="right", fill="y", padx=2)  # 增加一点间距，避免紧贴文本框
        self.display_text.configure(yscrollcommand=scrollbar.set)

        self.display_text.pack(side="left", fill="both", expand=True)
        
        def on_mousewheel(event):
            self.display_text.yview_scroll(-1 * (event.delta // 120), "units")
        self.display_text.bind("<MouseWheel>", on_mousewheel)
        
        self.TEXT_TAGS = {
            'hyperlink': {
                'font': ('KaiTi', 16),  # 原12，放大到16
                'foreground': "#8B2323",
                'underline': 1
            },
            'section_title': {
                'font': ('Microsoft YaHei', 22, 'bold'),  # 原16，放大到22
                'foreground': '#8B0000',
                'spacing1': 12,  # 稍微增加间距
                'spacing3': 12
            },
            'dynasty_title': {
                'font': ('Microsoft YaHei', 19, 'bold'),  # 原14，放大到19
                'foreground': '#704214',
                'spacing1': 6,
                'spacing3': 6
            }
        }
        
        for tag, style in self.TEXT_TAGS.items():
            self.display_text.tag_configure(tag, **style)

        self.root.bind('<Return>', lambda e: self.search_emperor())
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.root.bind('<Escape>', lambda e: self.root.focus())
        self.search_entry.bind('<Return>', lambda e: self.search_emperor())

    def convert_text(self, text, to_traditional=True):
        """转换文字"""
        if to_traditional:
            return self.converter_s2t.convert(text)
        return self.converter_t2s.convert(text)
    
    def toggle_traditional(self):
        """切换繁简显示"""
        self.is_traditional = not self.is_traditional
        
        self.switch_button.configure(text="繁體" if self.is_traditional else "简体")
        
        def convert_widget_text(widget):
            if isinstance(widget, (ctk.CTkButton, ctk.CTkLabel, ctk.CTkRadioButton)):
                if widget != self.switch_button and widget != self.analyze_button:
                    current_text = widget.cget('text')
                    new_text = self.convert_text(current_text, self.is_traditional)
                    widget.configure(text=new_text)
            elif isinstance(widget, ctk.CTkEntry):
                current_text = widget.get()
                new_text = self.convert_text(current_text, self.is_traditional)
                widget.delete(0, "end")
                widget.insert(0, new_text)
            elif isinstance(widget, tk.Text):
                current_content = widget.get("1.0", "end-1c")
                if current_content:
                    widget.delete("1.0", "end")
                    widget.insert("1.0", self.convert_text(current_content, self.is_traditional))
                    self.reapply_tags()
            
            for child in widget.winfo_children():
                convert_widget_text(child)
        
        convert_widget_text(self.root)
        
        self.search_label.configure(text=self.convert_text("搜索皇帝：", self.is_traditional))
        self.search_button.configure(text=self.convert_text("搜索", self.is_traditional))
        
        current_content = self.display_text.get("1.0", "end").strip()
        if current_content:
            self.display_text.delete("1.0", "end")
            converted_content = self.convert_text(current_content, self.is_traditional)
            self.display_text.insert("1.0", converted_content)
            self.reapply_tags()

    def reapply_tags(self):
        """重新应用文本标签（如超链接）"""
        content = self.display_text.get("1.0", "end").strip().split('\n\n')
        self.display_text.delete("1.0", "end")
        
        link_count = 0
        for paragraph in content:
            if paragraph:
                lines = paragraph.split('\n')
                emperor_info = {}
                
                # 首先收集皇帝信息
                for line in lines:
                    if "：" in line:
                        parts = line.split("：", 1)
                        if len(parts) == 2:
                            key, value = parts
                            emperor_info[key.strip()] = value.strip()
                
                # 处理段落中的每一行
                for line in lines:
                    if "查看详细资料" in line or "查看詳細資料" in line:
                        start_index = self.display_text.index("end-1c linestart")
                        self.display_text.insert("end", line + "\n")
                        end_index = self.display_text.index("end-1c")
                        
                        # 创建唯一的标签名
                        link_tag = f"link_{link_count}"
                        link_count += 1
                        
                        # 构建搜索URL
                        search_parts = []
                        if "朝代" in emperor_info:
                            search_parts.append(emperor_info["朝代"])
                        if "称号" in emperor_info or "稱號" in emperor_info:
                            search_parts.append(emperor_info.get("称号", emperor_info.get("稱號", "")))
                        if "名讳" in emperor_info or "名諱" in emperor_info:
                            search_parts.append(emperor_info.get("名讳", emperor_info.get("名諱", "")))
                        
                        search_term = " ".join(filter(None, search_parts))
                        from urllib.parse import quote
                        encoded_term = quote(search_term)
                        url = f"https://cn.bing.com/search?q={encoded_term}"
                        
                        # 添加标签和绑定事件
                        self.display_text.tag_add(link_tag, start_index, end_index)
                        self.display_text.tag_add("hyperlink", start_index, end_index)
                        
                        # 使用闭包捕获当前URL值
                        def make_callback(url):
                            return lambda e: webbrowser.open(url)
                        
                        self.display_text.tag_bind(link_tag, "<Button-1>", make_callback(url))
                    else:
                        self.display_text.insert("end", line + "\n")
                
                self.display_text.insert("end", "\n")

    def insert_emperor_with_link(self, emperor):
        """插入带有搜索链接的皇帝信息"""
        info = self.generator.format_emperor_info(emperor)
        if self.is_traditional:
            info = self.convert_text(info, True)
        else:
            info = self.convert_text(info, False)
            
        self.display_text.insert("end", f"{info}\n")
        
        search_parts = []
        if emperor['dynasty']:
            search_parts.append(emperor['dynasty'])
        if emperor['title']:
            search_parts.append(emperor['title'])
        if emperor['name']:
            search_parts.append(emperor['name'])
        
        search_term = ' '.join(search_parts)
        from urllib.parse import quote
        encoded_term = quote(search_term)
        url = f"https://cn.bing.com/search?q={encoded_term}&setlang=zh-CN&setmkt=zh-CN" if not can_access_google else f"https://www.google.com/search?q={encoded_term}&hl=zh-CN&lr=lang_zh-CN"
        
        link_text = "查看详细资料" if not self.is_traditional else self.convert_text("查看详细资料", True)
        start_index = self.display_text.index("end-1c linestart")
        self.display_text.insert("end", link_text + "\n\n")
        end_index = f"{start_index}+{len(link_text)}c"
        
        link_tag = f"link_{url}"
        self.display_text.tag_add(link_tag, start_index, end_index)
        self.display_text.tag_add("hyperlink", start_index, end_index)
        
        def on_link_enter(event):
            self.display_text.configure(cursor="hand2")
        
        def on_link_leave(event):
            self.display_text.configure(cursor="")
        
        self.display_text.tag_bind(link_tag, "<Button-1>", lambda e: webbrowser.open(url))
        self.display_text.tag_bind(link_tag, "<Enter>", on_link_enter)
        self.display_text.tag_bind(link_tag, "<Leave>", on_link_leave)

    def generate_random_emperor(self):
        """生成一位随机皇帝并显示"""
        if not self.generator.all_emperors:
            messagebox.showerror("错误", "皇帝数据未加载。")
            return
        emperor = self.generator.generate_random_emperor()
        self.display_text.delete("1.0", "end")
        self.display_text.insert("end", "随机生成的皇帝：\n\n")
        
        # 保存当前显示的皇帝
        self.displayed_emperors = [emperor]
        
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
                    messagebox.showwarning("警告", f"最多只能生成{len(self.generator.all_emperors)}位皇帝。")
                    count = len(self.generator.all_emperors)
                emperors = self.generator.generate_multiple_emperors(count)
                self.display_text.delete("1.0", "end")
                self.display_text.insert("end", f"随机生成的{len(emperors)}位皇帝：\n\n")
                
                # 保存当前显示的皇帝
                self.displayed_emperors = emperors.copy()
                
                for i, emp in enumerate(emperors, 1):
                    self.display_text.insert("end", f"第{i}位：\n")
                    self.insert_emperor_with_link(emp)
                popup.destroy()
            except ValueError:
                messagebox.showerror("输入错误", "请输入一个有效的正整数")

        popup = self.create_popup("生成多位皇帝")
        ctk.CTkLabel(popup, text="请输入想生成的皇帝数量：", font=('华文行楷', 21)).pack(pady=20)
        entry = ctk.CTkEntry(popup, font=self.text_font, width=240, fg_color='#FFF8DC', text_color='#2B1B17')
        entry.pack(pady=18)
        submit_button = ctk.CTkButton(popup, text="生成", command=submit, width=180, fg_color='#F5E6CB', text_color='#8B2323', hover_color='#DAA520')
        submit_button.pack(pady=18)

    def query_emperors_by_dynasty(self):
        """按朝代查询皇帝"""
        popup = self.create_popup("按朝代查询皇帝")
        
        def submit():
            selected_dynasty = combo.get()
            if not selected_dynasty:
                messagebox.showerror("选择错误", self.convert_text("请选择一个朝代。", self.is_traditional))
                return
            
            self.display_text.delete("1.0", "end")
            
            # 清空当前显示的皇帝列表
            self.displayed_emperors = []
            
            if selected_dynasty == "时间轴" or selected_dynasty == self.convert_text("时间轴", True):
                popup.destroy()
                self.show_dynasty_timeline()
            elif selected_dynasty == "总览" or selected_dynasty == self.convert_text("总览", True):
                title = "历代皇帝总览：\n\n"
                if self.is_traditional:
                    title = self.convert_text(title, True)
                self.display_text.insert("end", title, "section_title")
                
                displayed_emperors = set()
                for dynasty in self.generator.get_dynasties_list():
                    emperors = self.generator.get_emperors_by_dynasty(dynasty)
                    if emperors:
                        dynasty_title = f"【{dynasty}】\n"
                        if self.is_traditional:
                            dynasty_title = self.convert_text(dynasty_title, True)
                        self.display_text.insert("end", dynasty_title, "dynasty_title")
                        for emp in emperors:
                            emp_id = f"{emp['title']}_{emp['name']}"
                            if emp_id not in displayed_emperors:
                                displayed_emperors.add(emp_id)
                                emp_text = f"- {emp['title']}（{emp['name']}）\n" if emp['name'] else f"- {emp['title']}\n"
                                if self.is_traditional:
                                    emp_text = self.convert_text(emp_text, True)
                                self.display_text.insert("end", emp_text)
                        self.display_text.insert("end", "\n")
            else:
                emperors = self.generator.get_emperors_by_dynasty(selected_dynasty)
                if emperors:
                    title = f"【{selected_dynasty}】皇帝列表：\n\n"
                    if self.is_traditional:
                        title = self.convert_text(title, True)
                    self.display_text.insert("end", title, "section_title")
                    
                    # 保存当前显示的皇帝
                    self.displayed_emperors = emperors.copy()
                    
                    displayed_set = set()
                    for emp in emperors:
                        emp_id = f"{emp['title']}_{emp['name']}"
                        if emp_id not in displayed_set:
                            displayed_set.add(emp_id)
                            self.insert_emperor_with_link(emp)
                            self.display_text.insert("end", "\n")
                else:
                    msg = f"未找到{selected_dynasty}的皇帝记录。"
                    if self.is_traditional:
                        msg = self.convert_text(msg, True)
                    self.display_text.insert("end", msg)
            
            popup.destroy()
        
        ctk.CTkLabel(popup, text="请选择朝代：", font=self.button_font, text_color='#2B1B17').pack(pady=25)
        dynasties = ["时间轴", "总览"] + self.generator.get_dynasties_list()
        combo = ctk.CTkOptionMenu(popup, values=dynasties, font=self.text_font, width=240, fg_color='#FFF8DC', text_color='#2B1B17', button_color='#F5E6CB', button_hover_color='#DAA520')
        combo.set("时间轴")
        combo.pack(pady=18)
        submit_button = ctk.CTkButton(popup, text="查询", command=submit, width=180, fg_color='#F5E6CB', text_color='#8B2323', hover_color='#DAA520')
        submit_button.pack(pady=18)

    def _on_click(self, event):
        for tag in self.display_text.tag_names("current"):
            if tag.startswith("link_"):
                url = tag.replace("link_", "")
                webbrowser.open(url)

    def _set_icon_for_toplevel(self, toplevel):
        """为CTkToplevel窗口设置图标的特殊方法"""
        try:
            # 获取底层的tk窗口
            toplevel_tk = toplevel.winfo_toplevel()
            
            # 尝试使用wm_iconbitmap
            if self.icon_path.lower().endswith('.ico'):
                toplevel_tk.wm_iconbitmap(self.icon_path)
                # 重要：防止图标被覆盖
                toplevel_tk.after(100, lambda: toplevel_tk.wm_iconbitmap(self.icon_path))
                toplevel_tk.after(500, lambda: toplevel_tk.wm_iconbitmap(self.icon_path))
                print(f"成功为弹窗设置图标(wm_iconbitmap): {self.icon_path}")
            else:
                # 对于非ico文件，使用iconphoto
                icon = tk.PhotoImage(file=self.icon_path)
                toplevel_tk.wm_iconphoto(True, icon)
                # 保存引用防止垃圾回收
                toplevel_tk.icon_ref = icon
                print("成功为弹窗设置图标(wm_iconphoto)")
        except Exception as e:
            print(f"设置弹窗图标失败: {e}")
            
            # 备用方法：尝试直接使用tk的方法
            try:
                if hasattr(toplevel, '_root'):
                    if self.icon_path.lower().endswith('.ico'):
                        toplevel._root().iconbitmap(self.icon_path)
                        # 重要：防止图标被覆盖
                        toplevel._root().after(100, lambda: toplevel._root().iconbitmap(self.icon_path))
                        toplevel._root().after(500, lambda: toplevel._root().iconbitmap(self.icon_path))
                    else:
                        icon = tk.PhotoImage(file=self.icon_path)
                        toplevel._root().iconphoto(True, icon)
                        # 保存引用防止垃圾回收
                        toplevel._root().icon_ref = icon
                    print("使用备用方法成功设置图标")
            except Exception as e2:
                print(f"备用方法也失败: {e2}")

    def create_popup(self, title, width=480, height=300):
        popup = ctk.CTkToplevel(self.root)
        if self.is_traditional:
            title = self.convert_text(title, True)
        popup.title(title)
        popup.geometry(f"{width}x{height}")
        popup.resizable(False, False)
        
        # 为弹窗设置图标 - 使用多次延迟设置防止被覆盖
        if self.icon_path and os.path.exists(self.icon_path):
            try:
                # 立即尝试设置一次
                self._set_icon_for_toplevel(popup)
                # 然后在窗口完全加载后再次设置
                popup.after(10, lambda: self._set_icon_for_toplevel(popup))
                popup.after(100, lambda: self._set_icon_for_toplevel(popup))
                # 再延迟设置一次，确保不被其他操作覆盖
                popup.after(500, lambda: self._set_icon_for_toplevel(popup))
            except Exception as e:
                print(f"为弹窗设置图标失败: {e}")
        
        # 确保弹窗在前台显示
        popup.lift()
        popup.focus_force()
        popup.grab_set()  # 添加模态特性，防止用户与主窗口交互
        
        # 保存对图标路径的引用，防止被垃圾回收
        popup.icon_path_ref = self.icon_path
        
        return popup

    def show_chat_window(self):
        if hasattr(self, 'chat_window') and self.chat_window is not None:
            try:
                if self.chat_window.window.winfo_exists():
                    self.chat_window.window.lift()
                    self.chat_window.window.focus_force()
                    return
            except AttributeError:
                self.chat_window = None
        
        try:
            api_key = 'sk-0937b0ede5ea49ae9ceaa9cecfe8a690'
            self.chat_window = AIChatWindow(self.root, api_key)
            
            # 为聊天窗口设置图标 - 使用多次延迟设置
            if hasattr(self.chat_window, 'window') and self.icon_path and os.path.exists(self.icon_path):
                self.chat_window.window.after(10, lambda: self._set_icon_for_toplevel(self.chat_window.window))
                self.chat_window.window.after(100, lambda: self._set_icon_for_toplevel(self.chat_window.window))
                self.chat_window.window.after(500, lambda: self._set_icon_for_toplevel(self.chat_window.window))
                # 保存引用防止垃圾回收
                self.chat_window.window.icon_path_ref = self.icon_path
        except Exception as e:
            messagebox.showerror("错误", f"无法打开聊天窗口：{str(e)}")

    def get_icon_path(self):
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, "assets", "images", "seal.ico")
        except Exception as e:
            print(f"无法获取图标路径: {e}")
            return None

    def search_emperor(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("提示", self.convert_text("请输入搜索关键词", self.is_traditional))
            return
        
        traditional_keyword = self.convert_text(keyword, True)
        simplified_keyword = self.convert_text(keyword, False)
        
        results = []
        for emperor in self.generator.all_emperors:
            searchable_fields = [
                (emperor['title'], self.convert_text(emperor['title'], True)),
                (emperor['name'], self.convert_text(emperor['name'], True)),
                (emperor['dynasty'], self.convert_text(emperor['dynasty'], True))
            ]
            if any(keyword in field[0] or keyword in field[1] or 
                   traditional_keyword in field[0] or traditional_keyword in field[1] or
                   simplified_keyword in field[0] or simplified_keyword in field[1]
                   for field in searchable_fields if field[0]):
                results.append(emperor)
        
        self.display_text.delete("1.0", "end")
        if results:
            title = f"找到 {len(results)} 位相关皇帝：\n\n"
            if self.is_traditional:
                title = self.convert_text(title, True)
            self.display_text.insert("end", title, "section_title")
            for emp in results:
                self.insert_emperor_with_link(emp)
                self.display_text.insert("end", "\n")
        else:
            msg = "未找到相关结果。"
            if self.is_traditional:
                msg = self.convert_text(msg, True)
            self.display_text.insert("end", msg)

    def show_dynasty_timeline(self):
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
        
        self.display_text.delete("1.0", "end")
        
        title = "历代王朝时间轴\n\n"
        if self.is_traditional:
            title = self.convert_text(title, True)
        self.display_text.insert("end", title, "section_title")
        
        for dynasty, years in DYNASTY_YEARS:
            line = f"{dynasty}  【{years}】\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert("end", line)
        
        note = "\n注：以上时间均为公历纪年，部分时期存在政权并立情况，仅供参考。\n"
        if self.is_traditional:
            note = self.convert_text(note, True)
        self.display_text.insert("end", note)

        plt.figure(figsize=(16, 8))
        dynasties = ["秦朝", "西汉", "新朝", "东汉", "曹魏", "蜀汉", "东吴", "西晋", "东晋", "刘宋", "南齐", "南梁", "陈", "北魏", "东魏", "西魏", "北齐", "北周", "隋朝", "唐朝", "后梁", "后唐", "后晋", "后汉", "后周", "北宋", "辽", "金", "南宋", "元朝", "明朝", "大顺", "南明", "清朝"]
        years = [15, 210, 14, 195, 45, 42, 58, 51, 103, 59, 23, 55, 32, 148, 16, 22, 27, 24, 38, 289, 16, 13, 11, 4, 9, 167, 209, 119, 152, 97, 276, 1, 18, 268]
        plt.bar(dynasties, years)
        plt.xlabel("朝代", fontsize=18)
        plt.ylabel("国祚", fontsize=18)
        plt.title("国祚图", fontsize=20)
        plt.xticks(rotation=45, ha='right', fontsize=14)
        plt.yticks(fontsize=16)
        plt.tight_layout()
        plt.show()

    def create_advanced_search_dialog(self):
        dialog = self.create_popup("高级搜索" if not self.is_traditional else "進階搜索", width=380, height=520)  # 增加高度以适应更大字体
        
        search_frame = ctk.CTkFrame(dialog, fg_color='#FFFFFF')
        search_frame.pack(fill="x", padx=12, pady=6)
        
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
            frame = ctk.CTkFrame(search_frame, fg_color='#FFFFFF')
            frame.pack(fill="x", pady=3)
            ctk.CTkLabel(frame, text=f"{label}：", font=('微软雅黑', 14), text_color='#2B1B17', width=96, anchor="e").pack(side="left", padx=6)  # 原11，放大到14
            entry = ctk.CTkEntry(frame, font=('微软雅黑', 14), fg_color='#FFF8DC', text_color='#2B1B17')  # 原11，放大到14
            entry.pack(side="left", fill="x", expand=True, padx=6)
            entries[key] = entry
        
        options_frame = ctk.CTkFrame(dialog, fg_color='#FFFFFF')
        options_frame.pack(fill="x", padx=12, pady=6)
        
        match_var = ctk.StringVar(value="any")
        ctk.CTkRadioButton(options_frame, text="匹配任意条件" if not self.is_traditional else "匹配任意條件", variable=match_var, value="any", font=('微软雅黑', 14), text_color='#2B1B17').pack(anchor="w")  # 原11，放大到14
        ctk.CTkRadioButton(options_frame, text="匹配所有条件" if not self.is_traditional else "匹配所有條件", variable=match_var, value="all", font=('微软雅黑', 14), text_color='#2B1B17').pack(anchor="w")  # 原11，放大到14
        
        case_sensitive = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_frame, text="区分大小写" if not self.is_traditional else "區分大小寫", variable=case_sensitive, font=('微软雅黑', 14), text_color='#2B1B17').pack(anchor="w")  # 原11，放大到14
        
        sort_frame = ctk.CTkFrame(dialog, fg_color='#FFFFFF')
        sort_frame.pack(fill="x", padx=12, pady=6)
        
        self.sort_var = ctk.StringVar(value='dynasty')
        sort_options = [
            ('按朝代排序', 'dynasty'),
            ('按年代排序', 'year'),
            ('按在位时间', 'reign_length')
        ]
        if self.is_traditional:
            sort_options = [
                ('按朝代排序', 'dynasty'),
                ('按年代排序', 'year'),
                ('按在位時間', 'reign_length')
            ]
        
        self.sort_buttons = []
        for text, value in sort_options:
            rb = ctk.CTkRadioButton(sort_frame, text=text, variable=self.sort_var, value=value, font=('微软雅黑', 14), text_color='#2B1B17')  # 原11，放大到14
            rb.pack(anchor="w", pady=3)
            self.sort_buttons.append(rb)
        
        def do_search():
            criteria = {k: v.get().strip() for k, v in entries.items()}
            results = self.advanced_search(criteria, match_all=match_var.get() == "all", case_sensitive=case_sensitive.get())
            sorted_results = self.sort_results(results, self.sort_var.get())
            self.display_search_results(sorted_results)
            dialog.destroy()
        
        button_frame = ctk.CTkFrame(dialog, fg_color='#FFFFFF')
        button_frame.pack(fill="x", padx=12, pady=12)
        
        search_btn = ctk.CTkButton(button_frame, text="搜索" if not self.is_traditional else "搜索", command=do_search, font=('微软雅黑', 14), fg_color='#F5E6CB', text_color='#8B2323', hover_color='#DAA520')  # 原11，放大到14
        search_btn.pack(side="right")
        
        cancel_btn = ctk.CTkButton(button_frame, text="取消" if not self.is_traditional else "取消", command=dialog.destroy, font=('微软雅黑', 14), fg_color='#F5E6CB', text_color='#8B2323', hover_color='#DAA520')  # 原11，放大到14
        cancel_btn.pack(side="right", padx=6)

    def advanced_search(self, criteria, match_all=False, case_sensitive=False):
        results = []
        valid_criteria = {k: v for k, v in criteria.items() if v}
        if not valid_criteria:
            return results
        
        for emperor in self.generator.all_emperors:
            matches = []
            for field, search_term in valid_criteria.items():
                value = str(emperor.get(field, ''))
                if field == 'reign_period':
                    try:
                        if '-' in search_term:
                            search_start, search_end = map(lambda x: int(x.replace('年', '')), search_term.split('-'))
                        else:
                            search_start = search_end = int(search_term.replace('年', ''))
                        reign_period = value
                        if '-' in reign_period:
                            reign_start, reign_end = map(lambda x: int(x.replace('年', '')), reign_period.split('-'))
                        else:
                            reign_start = reign_end = int(reign_period.replace('年', ''))
                        match = not (search_end < reign_start or search_start > reign_end)
                    except (ValueError, IndexError):
                        if not case_sensitive:
                            value = value.lower()
                            search_term = search_term.lower()
                        match = search_term in value
                else:
                    if not case_sensitive:
                        value = value.lower()
                        search_term = search_term.lower()
                    if '*' in search_term or '?' in search_term:
                        match = fnmatch.fnmatch(value, search_term)
                    else:
                        match = search_term in value
                matches.append(match)
            
            if match_all and all(matches) or not match_all and any(matches):
                results.append(emperor)
        
        return results

    def display_search_results(self, results):
        self.display_text.delete("1.0", "end")
        if not results:
            msg = "未找到匹配的结果"
            if self.is_traditional:
                msg = self.convert_text(msg, True)
            self.display_text.insert("end", msg)
            self.displayed_emperors = []  # 清空当前显示的皇帝列表
            return
        
        title = f"找到 {len(results)} 条匹配结果：\n\n"
        if self.is_traditional:
            title = self.convert_text(title, True)
        self.display_text.insert("end", title, "section_title")
        
        # 保存当前显示的皇帝列表
        self.displayed_emperors = results.copy()
        
        for emperor in results:
            self.insert_emperor_with_link(emperor)

    def save_search_history(self, keyword):
        try:
            with open('search_history.txt', 'r', encoding='utf-8') as f:
                history = f.read().splitlines()
        except FileNotFoundError:
            history = []
        
        if keyword in history:
            history.remove(keyword)
        history.insert(0, keyword)
        history = history[:20]
        
        with open('search_history.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(history))

    def sort_results(self, results, sort_by):
        def get_year(reign_period):
            try:
                if '-' in reign_period:
                    return int(reign_period.split('-')[0].replace('年', ''))
                return int(reign_period.replace('年', ''))
            except (ValueError, IndexError):
                return 0
        
        def get_dynasty_order(dynasty):
            dynasty_order = [
                "秦朝", "西汉", "新朝", "东汉", "曹魏", "蜀汉", "东吴", "西晋", "东晋",
                "刘宋", "齐", "梁", "陈", "北魏", "东魏", "西魏", "北齐", "北周",
                "隋朝", "唐朝", "后梁", "后唐", "后晋", "后汉", "后周", "北宋",
                "辽", "金", "南宋", "元朝", "明朝", "大顺", "南明", "清朝"
            ]
            try:
                return dynasty_order.index(dynasty)
            except ValueError:
                return len(dynasty_order)
        
        if sort_by == 'year':
            results.sort(key=lambda x: get_year(x.get('reign_period', '')))
        elif sort_by == 'dynasty':
            results.sort(key=lambda x: (get_dynasty_order(x.get('dynasty', '')), get_year(x.get('reign_period', ''))))
        elif sort_by == 'reign_length':
            def get_reign_length(emperor):
                if 'reign_period' not in emperor:
                    return 0
                reign_info = emperor['reign_period']
                try:
                    years = re.findall(r'(\d+)年', reign_info)
                    if len(years) >= 2:
                        start_year = int(years[0])
                        end_year = int(years[1])
                        return max(end_year - start_year, start_year - end_year)
                    return 0
                except:
                    return 0
            results.sort(key=get_reign_length, reverse=True)
        
        return results

    def resort_results(self):
        """根据选择的方式重新排序结果"""
        # 如果没有显示的皇帝，直接返回
        if not self.displayed_emperors:
            return
        
        # 获取当前文本的第一行作为标题（如果有）
        title_line = ""
        current_text = self.display_text.get("1.0", "end-1c")
        if current_text:
            first_line = current_text.split('\n', 1)[0]
            if "随机生成" in first_line or "找到" in first_line or "皇帝列表" in first_line:
                title_line = first_line
        
        # 根据选择的方式排序
        sort_type = self.sort_var.get()
        
        # 创建一个副本进行排序，避免修改原始列表
        emperors_to_sort = self.displayed_emperors.copy()
        
        if sort_type == 'year':
            def get_start_year(emp):
                reign = emp.get('reign_period', '')
                try:
                    if '-' in reign:
                        year_str = reign.split('-')[0].strip()
                        if '前' in year_str:
                            year = -int(''.join(filter(str.isdigit, year_str)))
                        else:
                            year = int(''.join(filter(str.isdigit, year_str)))
                        return year
                    return 9999
                except:
                    return 9999
            sorted_emperors = sorted(emperors_to_sort, key=get_start_year)
        
        elif sort_type == 'dynasty':
            dynasty_order = [
                "秦朝", "西汉", "新朝", "东汉", "曹魏", "蜀汉", "东吴", "西晋", "东晋",
                "刘宋", "南齐", "南梁", "陈", "北魏", "东魏", "西魏", "北齐", "北周",
                "隋朝", "唐朝", "后梁", "后唐", "后晋", "后汉", "后周", "北宋",
                "辽", "金", "南宋", "元朝", "明朝", "大顺", "南明", "清朝"
            ]
            
            def get_dynasty_order(dynasty):
                if not dynasty:
                    return len(dynasty_order)
                dynasty = dynasty.replace("政权", "").replace("朝", "").strip()
                for i, d in enumerate(dynasty_order):
                    if dynasty in d:
                        return i
                return len(dynasty_order)
            
            def get_start_year(emp):
                reign = emp.get('reign_period', '')
                try:
                    if '-' in reign:
                        year_str = reign.split('-')[0].strip()
                        if '前' in year_str:
                            year = -int(''.join(filter(str.isdigit, year_str)))
                        else:
                            year = int(''.join(filter(str.isdigit, year_str)))
                        return year
                    return 9999
                except:
                    return 9999
            
            sorted_emperors = sorted(emperors_to_sort, key=lambda x: (get_dynasty_order(x.get('dynasty', '')), get_start_year(x)))
        
        elif sort_type == 'reign_length':
            def get_reign_length(emperor):
                if 'reign_period' not in emperor:
                    return 0
                reign_info = emperor['reign_period']
                try:
                    years = re.findall(r'(\d+)年', reign_info)
                    if len(years) >= 2:
                        start_year = int(years[0])
                        end_year = int(years[1])
                        return max(end_year - start_year, start_year - end_year)
                    return 0
                except:
                    return 0
            sorted_emperors = sorted(emperors_to_sort, key=get_reign_length, reverse=True)
        else:
            # 默认不排序
            sorted_emperors = emperors_to_sort
        
        # 清空文本框并重新显示排序后的皇帝
        self.display_text.delete("1.0", "end")
        
        # 添加标题（如果有）
        if title_line:
            self.display_text.insert("end", title_line + "\n\n")
        
        # 显示排序后的皇帝
        emperor_count = len(sorted_emperors)
        for i, emperor in enumerate(sorted_emperors, 1):
            # 添加序号
            if emperor_count > 1:
                number = f"第{i}位：\n"
                if self.is_traditional:
                    number = self.convert_text(number, True)
                self.display_text.insert("end", number)
            
            # 显示皇帝信息
            self.insert_emperor_with_link(emperor)

    def analyze_emperors(self):
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
            'temple_name_stats': {},
            'posthumous_name_stats': {}
        }
        
        for emperor in self.generator.all_emperors:
            dynasty = emperor['dynasty']
            if dynasty not in stats['dynasty_stats']:
                stats['dynasty_stats'][dynasty] = {
                    'count': 0,
                    'dynasty_start': float('inf'),
                    'dynasty_end': float('-inf'),
                    'avg_reign': 0
                }
            stats['dynasty_stats'][dynasty]['count'] += 1
            
            if emperor['reign_period']:
                try:
                    period = emperor['reign_period'].strip('{}')
                    if '-' in period:
                        start_str, end_str = period.split('-')
                    else:
                        start_str = end_str = period
                    
                    def parse_year(year_str):
                        year_str = year_str.strip()
                        if year_str.startswith('前'):
                            return -int(year_str[1:-1])
                        else:
                            return int(year_str[:-1])
                    
                    start_year = parse_year(start_str)
                    end_year = parse_year(end_str)
                    
                    if start_year < stats['dynasty_stats'][dynasty]['dynasty_start']:
                        stats['dynasty_stats'][dynasty]['dynasty_start'] = start_year
                    if end_year > stats['dynasty_stats'][dynasty]['dynasty_end']:
                        stats['dynasty_stats'][dynasty]['dynasty_end'] = end_year
                    
                    reign_years = end_year - start_year + 1 if end_year >= start_year else start_year - end_year + 1
                    if reign_years > 0:
                        if not stats['reign_stats']['longest'] or reign_years > stats['reign_stats']['longest']['years']:
                            stats['reign_stats']['longest'] = {'emperor': emperor, 'years': reign_years}
                        if not stats['reign_stats']['shortest'] or reign_years < stats['reign_stats']['shortest']['years']:
                            stats['reign_stats']['shortest'] = {'emperor': emperor, 'years': reign_years}
                        if reign_years >= 60:
                            range_key = "60年以上"
                        else:
                            range_key = f"{(reign_years//10)*10}-{(reign_years//10)*10+9}年"
                        stats['reign_stats']['distribution'][range_key] = stats['reign_stats']['distribution'].get(range_key, 0) + 1
                except Exception as e:
                    print(f"解析在位时长时出错: {emperor['reign_period']}，错误信息: {e}")
            
            if emperor['name']:
                for char in emperor['name']:
                    stats['name_stats'][char] = stats['name_stats'].get(char, 0) + 1
            
            if emperor['era_names']:
                for era_name in emperor['era_names']:
                    for char in era_name:
                        stats['era_name_stats'][char] = stats['era_name_stats'].get(char, 0) + 1
            
            if emperor['temple_name']:
                for char in emperor['temple_name']:
                    stats['temple_name_stats'][char] = stats['temple_name_stats'].get(char, 0) + 1
            
            if emperor['posthumous_name']:
                for char in emperor['posthumous_name']:
                    stats['posthumous_name_stats'][char] = stats['posthumous_name_stats'].get(char, 0) + 1
        
        for dynasty in stats['dynasty_stats']:
            dynasty_start = stats['dynasty_stats'][dynasty]['dynasty_start']
            dynasty_end = stats['dynasty_stats'][dynasty]['dynasty_end']
            count = stats['dynasty_stats'][dynasty]['count']
            if dynasty_start < float('inf') and dynasty_end > float('-inf'):
                dynasty_duration = dynasty_end - dynasty_start + 1
                stats['dynasty_stats'][dynasty]['avg_reign'] = dynasty_duration / count
            else:
                stats['dynasty_stats'][dynasty]['avg_reign'] = 0
        
        self._display_analysis_results(stats)
        self._show_analysis_plots(stats)

    def _display_analysis_results(self, stats):
        plt.close('all')
        self.display_text.delete("1.0", "end")
        
        title = "皇帝数据统计分析\n" + "_" * 32 + "\n\n"
        if self.is_traditional:
            title = self.convert_text(title, True)
        self.display_text.insert("end", title)
        
        total_count = sum(data['count'] for data in stats['dynasty_stats'].values())
        total_title = f"总体统计：\n共计{total_count}位皇帝\n"
        if self.is_traditional:
            total_title = self.convert_text(total_title, True)
        self.display_text.insert("end", total_title + "\n")
        
        dynasty_title = "各朝代统计：\n"
        if self.is_traditional:
            dynasty_title = self.convert_text(dynasty_title, True)
        self.display_text.insert("end", dynasty_title)
        
        sorted_dynasties = sorted(stats['dynasty_stats'].items(), key=lambda x: x[1]['count'], reverse=True)
        for dynasty, data in sorted_dynasties:
            line = f"▪ {dynasty}: {data['count']}位皇帝"
            if data['avg_reign'] > 0:
                line += f", 平均在位{data['avg_reign']:.1f}年"
            line += "\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert("end", line)
        
        name_title = "\n名讳常用字TOP50：\n"
        if self.is_traditional:
            name_title = self.convert_text(name_title, True)
        self.display_text.insert("end", name_title)
        for i, (char, count) in enumerate(sorted(stats['name_stats'].items(), key=lambda x: x[1], reverse=True)[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert("end", line)
        
        era_title = "\n年号常用字TOP50：\n"
        if self.is_traditional:
            era_title = self.convert_text(era_title, True)
        self.display_text.insert("end", era_title)
        for i, (char, count) in enumerate(sorted(stats['era_name_stats'].items(), key=lambda x: x[1], reverse=True)[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert("end", line)
        
        temple_title = "\n庙号常用字TOP50：\n"
        if self.is_traditional:
            temple_title = self.convert_text(temple_title, True)
        self.display_text.insert("end", temple_title)
        for i, (char, count) in enumerate(sorted(stats['temple_name_stats'].items(), key=lambda x: x[1], reverse=True)[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert("end", line)
        
        posthumous_title = "\n谥号常用字TOP50：\n"
        if self.is_traditional:
            posthumous_title = self.convert_text(posthumous_title, True)
        self.display_text.insert("end", posthumous_title)
        for i, (char, count) in enumerate(sorted(stats['posthumous_name_stats'].items(), key=lambda x: x[1], reverse=True)[:50], 1):
            line = f"▪ {i}. {char}: {count}次\n"
            if self.is_traditional:
                line = self.convert_text(line, True)
            self.display_text.insert("end", line)

    def _show_analysis_plots(self, stats):
        plot_window = ctk.CTkToplevel(self.root)
        plot_window.title("统计图表")
        plot_window.geometry("1600x800")
        
        if self.has_icon:
            icon_path = self.get_icon_path()
            if icon_path:
                try:
                    plot_window.iconbitmap(icon_path)
                except Exception as e:
                    print(f"无法为统计图表窗口加载图标: {e}")
        
        tabview = ctk.CTkTabview(plot_window)
        tabview.pack(expand=True, fill="both", padx=1, pady=1)

        def add_plot_to_tabview(tabview, title, plot_func):
            tab = tabview.add(title)
            fig = plot_func()
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(expand=True, fill="both")

        def plot_dynasty_counts():
            dynasties = list(stats['dynasty_stats'].keys())
            emperor_counts = [data['count'] for data in stats['dynasty_stats'].values()]
            fig = plt.figure(figsize=(16, 8))
            plt.bar(dynasties, emperor_counts)
            plt.xlabel("朝代", fontsize=18)  # 放大x轴标签字体
            plt.ylabel('\n'.join('皇帝数量'), rotation=0, ha='right', va='center', fontsize=18)  # 放大y轴标签字体
            plt.title("各朝代皇帝数量", fontsize=20)  # 放大标题字体
            plt.xticks(rotation=45, ha='right', fontsize=16)  # 放大x轴刻度字体
            plt.yticks(fontsize=16)  # 放大y轴刻度字体
            plt.tight_layout()
            return fig

        def plot_avg_reigns():
            dynasties = list(stats['dynasty_stats'].keys())
            avg_reigns = [data['avg_reign'] for _, data in stats['dynasty_stats'].items()]
            fig = plt.figure(figsize=(16, 8))
            plt.bar(dynasties, avg_reigns)
            plt.xlabel("朝代", fontsize=18)
            plt.ylabel('\n'.join('平均在位时间'), rotation=0, ha='right', va='center', fontsize=18)
            plt.title("各朝代平均在位时间", fontsize=20)
            plt.xticks(rotation=45, ha='right', fontsize=16)
            plt.yticks(fontsize=16)
            plt.tight_layout()
            return fig

        def plot_name_stats():
            top_50_chars = sorted(stats['name_stats'].items(), key=lambda x: x[1], reverse=True)[:50]
            chars = [char for char, _ in top_50_chars]
            counts = [count for _, count in top_50_chars]
            fig = plt.figure(figsize=(16, 8))
            plt.bar(chars, counts)
            plt.xlabel("字", fontsize=18)
            plt.ylabel('\n'.join('出现次数'), rotation=0, ha='right', va='center', fontsize=18)
            plt.title("名字用字TOP50", fontsize=20)
            plt.xticks(rotation=45, ha='right', fontsize=16)
            plt.yticks(fontsize=16)
            plt.tight_layout()
            return fig

        def plot_era_name_stats():
            top_50_era_chars = sorted(stats['era_name_stats'].items(), key=lambda x: x[1], reverse=True)[:50]
            era_chars = [char for char, _ in top_50_era_chars]
            era_counts = [count for _, count in top_50_era_chars]
            fig = plt.figure(figsize=(16, 8))
            plt.bar(era_chars, era_counts)
            plt.xlabel("字", fontsize=18)
            plt.ylabel('\n'.join('出现次数'), rotation=0, ha='right', va='center', fontsize=18)
            plt.title("年号用字TOP50", fontsize=20)
            plt.xticks(rotation=45, ha='right', fontsize=16)
            plt.yticks(fontsize=16)
            plt.tight_layout()
            return fig

        def plot_temple_name_stats():
            top_50_temple_chars = sorted(stats['temple_name_stats'].items(), key=lambda x: x[1], reverse=True)[:50]
            temple_chars = [char for char, _ in top_50_temple_chars]
            temple_counts = [count for _, count in top_50_temple_chars]
            fig = plt.figure(figsize=(16, 8))
            plt.bar(temple_chars, temple_counts)
            plt.xlabel("字", fontsize=18)
            plt.ylabel('\n'.join('出现次数'), rotation=0, ha='right', va='center', fontsize=18)
            plt.title("庙号用字TOP50", fontsize=20)
            plt.xticks(rotation=45, ha='right', fontsize=16)
            plt.yticks(fontsize=16)
            plt.tight_layout()
            return fig

        def plot_posthumous_name_stats():
            top_50_posthumous_chars = sorted(stats['posthumous_name_stats'].items(), key=lambda x: x[1], reverse=True)[:50]
            posthumous_chars = [char for char, _ in top_50_posthumous_chars]
            posthumous_counts = [count for _, count in top_50_posthumous_chars]
            fig = plt.figure(figsize=(16, 8))
            plt.bar(posthumous_chars, posthumous_counts)
            plt.xlabel("字", fontsize=18)
            plt.ylabel('\n'.join('出现次数'), rotation=0, ha='right', va='center', fontsize=18)
            plt.title("谥号用字TOP50", fontsize=20)
            plt.xticks(rotation=45, ha='right', fontsize=16)
            plt.yticks(fontsize=16)
            plt.tight_layout()
            return fig

        add_plot_to_tabview(tabview, "皇帝数量", plot_dynasty_counts)
        add_plot_to_tabview(tabview, "在位时间", plot_avg_reigns)
        add_plot_to_tabview(tabview, "名字", plot_name_stats)
        add_plot_to_tabview(tabview, "年号", plot_era_name_stats)
        add_plot_to_tabview(tabview, "庙号", plot_temple_name_stats)
        add_plot_to_tabview(tabview, "谥号", plot_posthumous_name_stats)

    def _calculate_reign_length(self, reign_period):
        try:
            if '-' not in reign_period:
                return 1
            start, end = reign_period.split('-')
            if '前' in start:
                start_year = -int(''.join(filter(str.isdigit, start)))
            else:
                start_year = int(''.join(filter(str.isdigit, start)))
            if '前' in end:
                end_year = -int(''.join(filter(str.isdigit, end)))
            else:
                end_year = int(''.join(filter(str.isdigit, end)))
            reign_length = max(end_year - start_year, start_year - end_year)
            return abs(reign_length) + 1 if reign_length != 0 else 1
        except Exception as e:
            print(f"计算在位时长出错: {reign_period}, 错误: {str(e)}")
            return 0

def main():
    root = ctk.CTk()
    app = EmperorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()