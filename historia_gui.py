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
can_access_google = None
class EmperorGenerator:
    def __init__(self):
        self.emperors_data = {}  # 存储所有朝代和皇帝信息
        self.all_emperors = []   # 存储所有皇帝对象
        global can_access_google 
        can_access_google = False
    

    def parse_emperor_data(self, text):
        """解析皇帝数据"""
        current_dynasty = ""
        sub_dynasty = ""
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 处理主朝代
            if line.endswith(':') and not line[0].isdigit():
                current_dynasty = line.rstrip(':')
                sub_dynasty = ""
                if current_dynasty not in self.emperors_data:
                    self.emperors_data[current_dynasty] = []
                continue
            
            # 处理子朝代
            if line.endswith(':') and current_dynasty:
                sub_dynasty = line.rstrip(':')
                if sub_dynasty not in self.emperors_data:
                    self.emperors_data[sub_dynasty] = []
                continue
            
            # 解析皇帝行
            if line[0].isdigit():
                # 先匹配大括号中的在位时间
                reign_match = re.search(r'\{([^}]+)\}', line)
                reign_period = reign_match.group(1) if reign_match else ""
                
                # 再匹配其他信息
                match = re.match(r'\d+\.\s*([^（]+)(?:（([^）]+)）)?(?:【([^】]+)】)?(?:\[([^\]]+)\])?', line)
                if match:
                    title = match.group(1).strip()
                    name = match.group(2).strip() if match.group(2) else ""
                    temple_name = match.group(3).strip() if match.group(3) else ""
                    posthumous_name = match.group(4).strip() if match.group(4) else ""
                    
                    # 确定当前朝代
                    dynasty = sub_dynasty if sub_dynasty else current_dynasty
                    
                    # 跳过非皇帝记录
                    if '非皇帝' in line or '篡位' in line:
                        continue
                    
                    # 修改年号匹配模式
                    era_match = re.search(r'年号：\[(.*?)\]|年号：(.*?)(?=\s|$)', line)
                    
                    emperor = {
                        'dynasty': dynasty,
                        'main_dynasty': current_dynasty,
                        'title': title,
                        'name': name,
                        'temple_name': temple_name,  # 庙号
                        'posthumous_name': posthumous_name,  # 谥号
                        'reign_period': reign_period,  # 添加在位时间
                        'era_names': []  # 添加年号列表
                    }
                    
                    # 修改年号解析逻辑
                    if era_match:
                        # 获取匹配到的年号组
                        era_text = era_match.group(1) if era_match.group(1) else era_match.group(2)
                        if era_text:
                            # 处理可能的分隔符：顿号、逗号、分号
                            era_names = re.split(r'[、，,;；]', era_text)
                            emperor['era_names'] = [name.strip() for name in era_names if name.strip()]
                    
                    if sub_dynasty:
                        self.emperors_data[sub_dynasty].append(emperor)
                    else:
                        self.emperors_data[current_dynasty].append(emperor)
                    self.all_emperors.append(emperor)
        
        # 去除重复数据
        self.all_emperors = list({v['title']+v['name']:v for v in self.all_emperors}.values())

    def generate_random_emperor(self):
        """随机生成一皇帝"""
        if not self.all_emperors:
            return None
        return random.choice(self.all_emperors)

    def generate_multiple_emperors(self, count=5):
        """生成多位随机皇帝"""
        if count > len(self.all_emperors):
            count = len(self.all_emperors)
        return random.sample(self.all_emperors, count)

    def get_emperors_by_dynasty(self, dynasty):
        """获取指定朝代的所有皇帝"""
        return self.emperors_data.get(dynasty, [])

    def format_emperor_info(self, emperor):
        """格式化皇帝信息输出"""
        info = []
        # 按照固定顺序显示信息
        display_order = [
            ('dynasty', '朝代'),
            ('title', '称号'),
            ('name', '名讳'),
            ('temple_name', '庙号'),
            ('posthumous_name', '谥号'),
            ('era_names', '年号'),  # 移到在位时间前
            ('reign_period', '在位')
        ]
        
        # 处理朝代显示
        if emperor['main_dynasty'] != emperor['dynasty']:
            info.append(f"朝代：{emperor['main_dynasty']}")
            info.append(f"政权：{emperor['dynasty']}")
        else:
            info.append(f"朝代：{emperor['dynasty']}")
        
        # 按顺序添加其他信息
        for field, label in display_order[1:]:  # 跳过朝代，因为已经处理过
            if field == 'era_names':
                if emperor.get(field):  # 如果有年号信息
                    era_text = '、'.join(emperor[field])
                    info.append(f"{label}：{era_text}")
            elif emperor.get(field):  # 其他字段
                info.append(f"{label}：{emperor[field]}")
        
        return '\n'.join(info)

    def get_dynasties_list(self):
        """获取所有朝代列表（历史顺序）"""
        # 定义朝代顺序
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
        
        # 获取实际存在的朝代
        available_dynasties = set(self.emperors_data.keys())
        
        # 按历史顺序返回实际存在的朝代
        ordered_dynasties = [d for d in dynasty_order if d in available_dynasties]
        
        # 如果有任何未在顺序列表中的朝代，将它们添加到末尾
        remaining_dynasties = sorted(list(available_dynasties - set(ordered_dynasties)))
        
        return ordered_dynasties + remaining_dynasties

    def get_main_dynasties_list(self):
        """获取主要朝代列表（不包含子朝代）"""
        return sorted(set(emp['main_dynasty'] for emp in self.all_emperors))

    def get_all_emperors(self):
        """获取所有皇帝信息，按朝代排序"""
        # 按朝代顺序整理皇帝列表
        sorted_emperors = {}
        dynasty_order = self.get_dynasties_list()
        
        for dynasty in dynasty_order:
            sorted_emperors[dynasty] = self.get_emperors_by_dynasty(dynasty)
        
        return sorted_emperors

class AIChatWindow:
    def __init__(self, parent, api_key):
        """初始化聊天窗口"""
        self.parent = parent
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("AI历史顾问（请保持网络连接)")
        self.window.geometry("380x500")  # 更小的窗口尺寸
        
        # 设置窗口背景色为暖色调
        self.window.configure(bg='#FFF8F3')  # 米白色背景
        
        # 创建界面元素
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
        self.has_icon = False
        try:
            if getattr(sys, 'frozen', False):
                # 打包后的路径
                base_path = sys._MEIPASS
            else:
                # 开发环境路径
                base_path = os.path.abspath(".")
                
            icon_path = os.path.join(base_path, "assets", "images", "seal.ico")
            self.window.iconbitmap(icon_path)
            self.has_icon = True
        except Exception as e:
            print(f"无法加载图标: {e}")
    
    def _create_widgets(self):
        """创建界面元素"""
        # 标题栏
        title_label = ttk.Label(
            self.window,
            text="AI历史顾问",
            font=('微软雅黑', 14),
            foreground='#8B4513',  # 暖棕色
            background='#FFF8F3'
        )
        title_label.pack(pady=(10,5))
        
        # 聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(
            self.window,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('微软雅黑', 9),
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
            font=('微软雅黑', 11),
            height=40,
            width=50,
            fg_color='#B38B6D',  # 暖棕色
            hover_color='#8B4513',  # 深棕色
            corner_radius=4
        )
        self.send_button.pack(side=tk.RIGHT)
    
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
        self.window.after(30000, self._check_response_timeout, send_thread)
    
    def _check_response_timeout(self, thread):
        """检查响应是否超时"""
        if thread.is_alive():
            self._update_display("错误: 响应超时，请重试\n", 'error')
            self._set_input_state(tk.NORMAL)
    
        # 修改后的 _get_ai_response 函数
    def _get_ai_response(self, message):
        """获取AI响应（流式版本）"""
        try:
            # 初始化流式消息标记
            self._update_display("AI: ", 'ai_stream')
            
            # 发起流式请求
            response_stream = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专精于中国历史的AI顾问，特别擅长解答关于历代皇帝、年号、政治制度、历史评价、同时期中西方对比等问题。请用中文回答，不要使用markdown格式，只使用普通文本。"
                    },
                    {"role": "user", "content": message}
                ],
                stream=True,  # 启用流式传输
                timeout=15
            )

            full_response = ""
            # 处理流式响应
            for chunk in response_stream:
                chunk_content = chunk.choices[0].delta.content
                if chunk_content:
                    full_response += chunk_content
                    # 实时更新显示（追加模式）
                    self._update_display(chunk_content, 'ai_stream', append=True)

            # 最终处理
            self._update_display("\n\n", 'ai_stream', append=True)
            return full_response

        except Exception as e:
            error_msg = f"错误: {str(e)}\n" if str(e) else "发送失败，请重试\n"
            self._update_display(error_msg, 'error')
        finally:
            self._set_input_state(tk.NORMAL)

    # 改进后的 _update_display 函数
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
        # 定义皇帝数据
        emperor_text = """秦朝:
1. 秦始皇（嬴政）[始皇帝] {前221年-前210年}
2. 秦二世（胡亥）[二世皇帝] {前210年-前207年}

西汉:
1. 汉高祖（刘邦）【太祖】[高皇帝] {前202年-前195年}
2. 汉惠帝（刘盈）[孝惠皇帝] {前195年-前188年}
3. 吕后临朝（吕雉，非皇帝但实际掌权）{前188年-前180年}
4. 汉文帝（刘恒）【太宗】[孝文皇帝] {前180年-前157年}
5. 汉景帝（刘启）[孝景皇帝] {前157年-前141年}
6. 汉武帝（刘彻）【世宗】[孝武皇帝] {前141年-前87年}- 年号：建元、元光、元朔、元狩、元鼎、元封、太初、天汉、太始、征和、后元
7. 汉昭帝（刘弗陵）[孝昭皇帝] {前87年-前74年}- 年号：始元、元凤、元平
8. 汉宣帝（刘询）【中宗】[孝宣皇帝] {前74年-前49年}- 年号：本始、地节、元康、神爵、五凤、甘露、黄龙
9. 汉元帝（刘奭）【高宗】[孝元皇帝] {前49年-前33年}- 年号：初元、永光、建昭、竟宁
10. 汉成帝（刘骜）【统宗】[孝成皇帝] {前33年-前7年}- 年号：建始、河平、阳朔、鸿嘉、永始、元延、绥和
11. 汉哀帝（刘欣）[孝哀皇帝] {前7年-前1年}- 年号：建平、太初元将
12. 汉平帝（刘衎）【元宗】[孝平皇帝] {前1年-6年}- 年号：元始

新朝:
1. 新太祖（王莽）【太祖】[睿皇帝] {9年-23年}- 年号：始建国、天凤、地皇

东汉:
1. 汉光武帝（刘秀）【世祖】[光武皇帝] {25年-57年}- 年号：建武、建武中元
2. 汉明帝（刘庄）【显宗】[孝明皇帝] {57年-75年}- 年号：永平
3. 汉章帝（刘炟）【肃宗】[孝章皇帝] {75年-88年}- 年号：建初、元和、章和
4. 汉和帝（刘肇）【穆宗】[孝和皇帝] {88年-106年}- 年号：永元、元兴、永初、元初、永宁、建光
5. 汉殇帝（刘隆）[孝殇皇帝] {106年}- 年号：延平
6. 汉安帝（刘祜）【恭宗】[孝安皇帝] {106年-125年}- 年号：永初、元初、永宁、建光、延光
7. 汉少帝（刘懿）{125年}- 年号：延光
8. 汉顺帝（刘保）【敬宗】[孝顺皇帝] {125年-144年}- 年号：永建、阳嘉、永和、汉安、建康
9. 汉冲帝（刘炳）[孝冲皇帝] {144年-145年}- 年号：永嘉
10. 汉质帝（刘缵）[孝质皇帝] {145年-146年}- 年号：本初
11. 汉桓帝（刘志）【威宗】[孝桓皇帝] {146年-168年}- 年号：建和、和平、元嘉、永兴、建宁
12. 汉灵帝（刘宏）[孝灵皇帝] {168年-189年}- 年号：建宁、熹平、光和、中平
13. 汉少帝（刘辩）[弘农怀王] {189年}- 年号：昭宁
14. 汉献帝（刘协）[孝献皇帝] {189年-220年}- 年号：光熹、昭宁、永汉、建安

曹魏:
1. 魏文帝（曹丕）【高祖】[文皇帝] {220年-226年}- 年号：黄初
2. 魏明帝（曹叡）【烈祖】[明皇帝] {226年-239年}- 年号：太和、青龙、景初
3. 废帝（曹芳）[齐王] {239年-254年}- 年号：正始、嘉平
4. 高贵乡公（曹髦）[高贵乡公] {254年-260年}- 年号：甘露
5. 魏元帝（曹奂）[元皇帝] {260年-265年}- 年号：景元、咸熙

蜀汉:
1. 昭烈帝（刘备）【太祖】[昭烈皇帝] {221年-223年}- 年号：章武
2. 后主（刘禅）【后主】[后主] {223年-263年}- 年号：建兴、延熙、景耀、炎兴

东吴:
1. 大帝（孙权）【太祖】[大皇帝] {229年-252年}- 年号：黄武、黄龙、嘉禾、赤乌、太元、神凤
2. 会稽王（孙亮）[会稽王] {252年-258年}- 年号：建兴、五凤、太平
3. 景帝（孙休）【景帝】[景皇帝] {258年-264年}- 年号：永安
4. 末帝（孙皓）[末皇帝] {264年-280年}- 年号：元兴、甘露、宝鼎、建衡、凤凰、天册、天玺、天纪
西晋:
1. 晋武帝（司马炎）【世祖】[武皇帝] {265年-290年}- 年号：泰始、咸宁、太康、太熙
2. 晋惠帝（司马衷）【惠宗】[惠皇帝] {290年-307年}- 年号：元康、永熙、永平、元康、永康、永宁、建始、光熙
3. 晋怀帝（司马炽）【怀宗】[怀皇帝] {307年-313年}- 年号：永嘉
4. 晋愍帝（司马邺）【愍宗】[愍皇帝] {313年-317年}- 年号：建兴

东晋:
1. 元帝（司马睿）【太祖】[元皇帝] {317年-323年}- 年号：建武、太兴、永昌
2. 明帝（司马绍）【肃祖】[明皇帝] {323年-325年}- 年号：永昌、太宁
3. 成帝（司马衍）【显宗】[成皇帝] {325年-342年}- 年号：咸和
4. 康帝（司马岳）[康皇帝] {342年-344年}- 年号：建元
5. 穆帝（司马聃）【孝宗】[穆皇帝] {344年-361年}- 年号：永和、升平
6. 哀帝（司马丕）[哀皇帝] {361年-365年}- 年号：兴宁
7. 海西公（司马奕）[海西公] {365年-371年}- 年号：太和
8. 简文帝（司马昱）【太宗】[简文皇帝] {371年-372年}- 年号：咸安
9. 孝武帝（司马曜）【烈宗】[孝武皇帝] {372年-396年}- 年号：宁康、太元
10. 安帝（司马德宗）[安皇帝] {396年-418年}- 年号：隆安、元兴、义熙
11. 恭帝（司马德文）[恭皇帝] {418年-420年}- 年号：元熙

刘宋:
1. 宋武帝（刘裕）【太祖】[武皇帝] {420年-422年}- 年号：永初
2. 宋少帝（刘义符）[少帝] {422年-424年}- 年号：景平
3. 宋文帝（刘义隆）【太祖】[文皇帝] {424年-453年}- 年号：元嘉
4. 宋孝武帝（刘骏）【世祖】[孝武皇帝] {453年-464年}- 年号：孝建、大明
5. 宋前废帝（刘子业）[废帝] {464年-465年}- 年号：永光、景和
6. 宋明帝（刘彧）【太宗】[明皇帝] {465年-472年}- 年号：泰始、泰豫、元徽
7. 宋后废帝（刘昱）[废帝] {472年-477年}- 年号：元徽
8. 宋顺帝（刘准）[顺皇帝] {477年-479年}- 年号：昇明

齐:
1. 齐高帝（萧道成）【太祖】[高皇帝] {479年-482年}- 年号：建元
2. 齐武帝（萧赜）【世祖】[武皇帝] {482年-493年}- 年号：永明
3. 齐明帝（萧鸾）【高宗】[明皇帝] {494年-498年}- 年号：建武、永泰
4. 齐东昏侯（萧宝卷）[东昏侯] {498年-501年}- 年号：永元
5. 齐和帝（萧宝融）[和皇帝] {501年-502年}- 年号：中兴

梁:
1. 梁武帝（萧衍）【高祖】[武皇帝] {502年-549年}- 年号：天监、普通、大通、中大通、大同、中大同、太清
2. 梁简文帝（萧纲）【太宗】[简文皇帝] {549年-551年}- 年号：大宝
3. 梁元帝（萧绎）【世祖】[孝元皇帝] {552年-555年}- 年号：承圣
4. 梁敬帝（萧方智）[敬皇帝] {555年-557年}- 年号：绍泰、太平

陈:
1. 陈武帝（陈霸先）【太祖】[武皇帝] {557年-559年}- 年号：永定
2. 陈文帝（陈蒨）【世祖】[文皇帝] {559年-566年}- 年号：天嘉、天康
3. 陈废帝（陈伯宗）[废帝] {566年}- 年号：光大
4. 陈宣帝（陈顼）【高祖】[孝宣皇帝] {566年-568年}- 年号：太建
5. 陈后主（陈叔宝）[后主] {568年-589年}- 年号：至德、祯明

北魏:
1. 道武帝（拓跋珪）【太祖】[道武皇帝] {386年-409年}- 年号：登国
2. 明元帝（拓跋嗣）【太宗】[明元皇帝] {409年-423年}- 年号：永兴、神瑞、泰常
3. 太武帝（拓跋焘）【世祖】[太武皇帝] {423年-452年}- 年号：始光、神麚、延和、太平真君
4. 南安王（拓跋余）[南安隐王] {452年}- 年号：正平
5. 文成帝（拓跋濬）【高宗】[文成皇帝] {452年-465年}- 年号：兴安、和平
6. 献文帝（拓跋弘）【显祖】[献文皇帝] {465年-471年}- 年号：天安、皇兴
7. 孝文帝（元宏）【高祖】[孝文皇帝] {471年-499年}- 年号：延兴、承明、太和
8. 宣武帝（元恪）【世宗】[宣武皇帝] {499年-515年}- 年号：景明、正始、永平、延昌
9. 孝明帝（元诩）【肃宗】[孝明皇帝] {515年-528年}- 年号：熙平、神龟、正光、孝昌、武泰
10. 孝庄帝（元子攸）【敬宗】[孝庄皇帝] {528年-530年}- 年号：建义、永安
11. 节闵帝（元恭）[节闵帝] {531年}- 年号：普泰
12. 孝武帝（元修）[孝武皇帝] {532年-534年}- 年号：太昌、永兴、永熙
东魏:
1. 孝静帝（元善见）[孝静皇帝] {534年-550年}- 年号：天平、元象、兴和、武定

西魏:
1. 文帝（元宝炬）[文帝] {535年-551年}- 年号：大统
2. 废帝（元钦）[废帝] {551年-554年}- 年号：大统
3. 恭帝（元廓）[恭帝] {554年-557年}- 年号：大统

北齐:
1. 文宣帝（高洋）【显祖】[文宣皇帝] {550年-559年}- 年号：天保
2. 废帝（高殷）[济南闵悼王] {559年-560年}- 年号：乾明
3. 孝昭帝（高演）【肃宗】[孝昭帝] {560年}- 年号：皇建
4. 武成帝（高湛）【世祖】[武成帝] {560年-561年}- 年号：太宁、河清
5. 后主（高纬）[后主] {561年-577年}- 年号：天统、武平、隆化

北周:
1. 明帝（宇文毓）【世宗】[明帝] {557年-560年}- 年号：武成
2. 武帝（宇文邕）【高祖】[武帝] {560年-578年}- 年号：保定、天和、建德、宣政
3. 宣帝（宇文赟）[宣帝] {578年-579年}- 年号：大成、宣政
4. 静帝（宇文衍）[静帝] {579年-581年}- 年号：大象、大定

隋朝:
1. 隋文帝（杨坚）【高祖】[文皇帝] {581年-604年}- 年号：开皇、仁寿
2. 隋炀帝（杨广）【炀帝】[炀皇帝] {604年-618年}- 年号：大业
3. 恭帝（杨侑）[恭皇帝] {618年}- 年号：义宁

唐朝:
1. 唐高祖（李渊）【高祖】[神尧大圣大光孝皇帝] {618年-626年}- 年号：武德
2. 唐太宗（李世民）【太宗】[文武大圣大广孝皇帝] {626年-649年}- 年号：贞观
3. 唐高宗（李治）【高宗】[天皇大圣大弘孝皇帝] {649年-683年}- 年号：永徽、显庆、龙朔、麟德、乾封、总章、咸亨、上元、仪凤、调露、永隆、开耀、永淳、弘道
4. 唐中宗（李显）【中宗】[大和大圣大昭孝皇帝] {684年、705年-710年}- 年号：嗣圣、神龙、景龙
5. 武则天（武曌）[则天顺圣皇后] {690年-705年}- 年号：天授、如意、长寿、延载、证圣、天册万岁、万岁登封、万岁通天、神功
6. 唐睿宗（李旦）【睿宗】[玄真大圣大兴孝皇帝] {684年-690年、710年-712年}- 年号：文明、大足、延和、景云、太极、延和
7. 唐玄宗（李隆基）【玄宗】[至道大圣大明孝皇帝] {712年-756年}- 年号：先天、开元、天宝
8. 唐肃宗（李亨）【肃宗】[文明武德大圣大宣孝皇帝] {756年-762年}- 年号：至德、乾元
9. 唐代宗（李豫）【代宗】[睿文孝武皇帝] {762年-779年}- 年号：宝应、广德、大历
10. 唐德宗（李适）【德宗】[神武孝文皇帝] {779年-805年}- 年号：建中、兴元、贞元
11. 唐顺宗（李诵）【顺宗】[至德大圣大安孝皇帝] {805年}- 年号：永贞
12. 唐宪宗（李纯）【宪宗】[圣神章武孝皇帝] {805年-820年}- 年号：元和
13. 唐穆宗（李恒）【穆宗】[睿圣文惠孝皇帝] {820年-824年}- 年号：长庆
14. 唐敬宗（李湛）【敬宗】[睿武昭愍孝皇帝] {824年-826年}- 年号：宝历
15. 唐文宗（李昂）【文宗】[元圣昭献孝皇帝] {826年-840年}- 年号：大和、开成
16. 唐武宗（李炎）【武宗】[至道昭肃孝皇帝] {840年-846年}- 年号：会昌
17. 唐宣宗（李忱）【宣宗】[圣武献文孝皇帝] {846年-859年}- 年号：大中
18. 唐懿宗（李漼）【懿宗】[昭圣恭惠孝皇帝] {859年-873年}- 年号：咸通
19. 唐僖宗（李儇）【僖宗】[惠圣恭定孝皇帝] {873年-888年}- 年号：乾符、广明、中和
20. 唐昭宗（李晔）【昭宗】[圣穆景文孝皇帝] {888年-904年}- 年号：光启、文德、龙纪、大顺、景福、乾宁、光化、天复、天佑
21. 唐哀帝（李祝）【哀帝】[昭宣光烈孝皇帝] {904年-907年}- 年号：天祐
后梁:
1. 后梁太祖（朱温）【太祖】[神武元圣孝皇帝] {907年-912年}- 年号：开平、乾化
2. 后梁末帝（朱友珪）[郢王] {912年-913年}- 年号：乾化
3. 后梁末帝（朱友贞）[末帝] {913年-923年}- 年号：贞明、龙德

后唐:
1. 后唐庄宗（李存勗）【庄宗】[光圣神闵孝皇帝] {923年-926年}- 年号：同光
2. 后唐明宗（李嗣源）【明宗】[圣德和武钦孝皇帝] {926年-933年}- 年号：天成、长兴、应顺
3. 后唐闵帝（李从厚）[闵皇帝] {933年-934年}- 年号：应顺
5. 后唐末帝（李从珂）[末帝] {934年-936年}- 年号：清泰

后晋:
1. 后晋高祖（石敬瑭）【高祖】[圣文章武明德孝皇帝] {936年-942年}- 年号：天福
2. 后晋出帝（石重贵）[出帝] {942年-947年}- 年号：天福、开运

后汉:
1. 后汉高祖（刘知远）【高祖】[睿文圣武昭肃孝皇帝] {947年-948年}- 年号：天福、乾祐
2. 后汉隐帝（刘承祐）[隐皇帝] {948年-951年}- 年号：乾祐

后周:
1. 后周太祖（郭威）【太祖】[圣神恭肃文武孝皇帝] {951年-954年}- 年号：广顺
2. 后周世宗（柴荣）【世宗】[睿武孝文皇帝] {954年-959年}- 年号：广顺、显德
3. 后周恭帝（柴宗训）[恭皇帝] {959年-960年}- 年号：显德

北宋:
1. 宋太祖（赵匡胤）【太祖】[启运立极英武睿文神德圣功至明大孝皇帝] {960年-976年}- 年号：建隆、乾德、开宝
2. 宋太宗（赵光义）【太宗】[至仁应道神功圣德文武睿烈大明广孝皇帝] {976年-997年}- 年号：太平兴国、雍熙、端拱、淳化、至道
3. 宋真宗（赵恒）【真宗】[应符稽古神功让德文明武定章圣元孝皇帝] {997年-1022年}- 年号：咸平、景德、大中祥符、天禧、乾兴
4. 宋仁宗（赵祯）【仁宗】[体天法道极功全德神文圣武睿哲明孝皇帝] {1022年-1063年}- 年号：天圣、明道、景祐、宝元、康定、庆历、皇祐、至和、嘉祐
5. 宋英宗（赵曙）【英宗】[体干应历隆功盛德宪文肃武睿圣宣孝皇帝] {1063年-1067年}- 年号：治平
6. 宋神宗（赵顼）【神宗】[绍天法古运德建功英文烈武钦仁圣孝皇帝] {1067年-1085年}- 年号：熙宁、元丰
7. 宋哲宗（赵煦）【哲宗】[宪元继道显德定功钦文睿武齐圣昭孝皇帝] {1085年-1100年}- 年号：元祐、绍圣、元符
8. 宋徽宗（赵佶）【徽宗】[体神合道骏烈逊功圣文仁德宪慈显孝皇帝] {1100年-1125年}- 年号：建中靖国、崇宁、大观、政和、重和、宣和
9. 宋钦宗（赵桓）【钦宗】[恭文顺德仁孝皇帝] {1125年-1127年}- 年号：靖康

南宋:
1. 宋高宗（赵构）【高宗】[受命中兴全功至德圣神武文昭仁宪孝皇帝] {1127年-1162年}- 年号：建炎、绍兴
2. 宋孝宗（赵昚）【孝宗】[绍统同道冠德昭功哲文神武明圣成孝皇帝] {1162年-1189年}- 年号：隆兴、乾道、淳熙
3. 宋光宗（赵惇）【光宗】[循道宪仁明功茂德温文顺武圣哲慈孝皇帝] {1189年-1194年}- 年号：绍熙
4. 宋宁宗（赵扩）【宁宗】[法天备道纯德茂功仁文哲武圣睿恭孝皇帝] {1194年-1224年}- 年号：庆元、嘉泰、开禧、嘉定
5. 宋理宗（赵昀）【理宗】[建道备德大功复兴烈文仁武圣明安孝皇帝] {1224年-1264年}- 年号：宝庆、绍定、端平、嘉熙、淳祐、宝祐、开庆、景定
6. 宋度宗（赵禥）【度宗】[端文明武景孝皇帝] {1264年-1274年}- 年号：咸淳
7. 宋恭帝（赵显）【恭帝】[孝恭懿圣皇帝] {1274年-1276年}- 年号：德祐
8. 宋端宗（赵昰）【端宗】[裕文昭武愍孝皇帝] {1276年-1278年}
9. 宋帝昺（赵昺）【昺帝】[悲皇帝] {1278年-1279年}- 年号：祥兴

辽:
1. 辽太祖（耶律阿保机）【太祖】[神册皇帝] {907年-926年}- 年号：神册、天赞
2. 辽太宗（耶律德光）【太宗】[文德皇帝] {926年-947年}- 年号：天显
3. 辽世宗（耶律阮）【世宗】[显德皇帝] {947年-951年}- 年号：天禄
4. 辽穆宗（耶律璟）【穆宗】[礼义皇帝] {951年-969年}- 年号：应历
5. 辽景宗（耶律贤）【景宗】[明德皇帝] {969年-982年}- 年号：保宁、乾亨
6. 辽圣宗（耶律隆绪）【圣宗】[文武大孝宣皇帝] {982年-1031年}- 年号：统和、开泰、太平
7. 辽兴宗（耶律宗真）【兴宗】[神圣孝章皇帝] {1031年-1055年}- 年号：重熙
8. 辽道宗（耶律洪基）【道宗】[仁圣大孝文皇帝] {1055年-1101年}- 年号：清宁、咸雍、大康、大安、寿昌
9. 辽天祚帝（耶律延禧）[天祚皇帝] {1101年-1125年}- 年号：乾统、天庆、保大
金:
1. 金太祖（完颜阿骨打）【太祖】[应乾兴运昭德定功仁明庄孝大圣武元皇帝] {1115年-1123年}- 年号：收国、天辅
2. 金太宗（完颜晟）【太宗】[体元应运世德昭功哲惠仁圣文烈皇帝] {1123年-1135年}- 年号：天会
3. 金熙宗（完颜亶）【熙宗】[弘基缵武庄靖孝成皇帝] {1135年-1149年}- 年号：天眷、皇统
4. 金海陵王（完颜亮）[海陵王] {1149年-1161年}- 年号：贞元、正隆
5. 金世宗（完颜雍）【世宗】[光天兴运文德武功圣明仁孝皇帝] {1161年-1189年}- 年号：大定
6. 金章宗（完颜璟）【章宗】[宪天光运仁文义武神圣英孝皇帝] {1189年-1208年}- 年号：明昌、承安、泰和
7. 金卫绍王（完颜永济）[卫绍王] {1208年-1213年}- 年号：大安、崇庆
8. 金宣宗（完颜珣）【宣宗】[继天兴统述道勤仁英武圣孝皇帝] {1213年-1224年}- 年号：贞祐、兴定
9. 金哀宗（完颜守绪）【哀宗】[敬天德运忠文靖武天圣烈孝庄皇帝] {1224年-1234年}- 年号：元光、正大、开兴、天兴
10. 金末帝（完颜承麟）[末帝] {1234年}- 年号：天兴

元朝:
1. 元太祖（铁木真）【太祖】[圣武皇帝] {1206年-1227年}
2. 元太宗（窝阔台）【太宗】[英文皇帝] {1229年-1241年}
3. 元定宗（贵由）【定宗】[简平皇帝] {1246年-1248年}
4. 元宪宗（蒙哥）【宪宗】[桓肃皇帝] {1251年-1259年}
5. 元世祖（忽必烈）【世祖】[圣德神功文武皇帝] {1260年-1294年}- 年号：中统、至元
6. 元成宗（铁穆耳）【成宗】[钦明广孝皇帝] {1294年-1307年}- 年号：元贞、大德
7. 元武宗（海山）【武宗】[仁惠宣孝皇帝] {1307年-1311年}- 年号：至大
8. 元仁宗（爱育黎拔力八达）【仁宗】[圣文钦孝皇帝] {1311年-1320年}- 年号：皇庆、延祐
9. 元英宗（硕德八剌）【英宗】[睿宗文孝皇帝] {1320年-1323年}- 年号：至治
10. 元泰定帝（也孙铁木儿）【泰定帝】[昭肃皇帝] {1323年-1328年}- 年号：泰定、致和
11. 元天顺帝（阿速吉八）【天顺帝】[文惠皇帝] {1328年}- 年号：天顺
12. 元文宗（图帖睦尔）【文宗】[圣明元孝皇帝] {1328年-1332年}- 年号：天历、至顺
13. 元明宗（和世瓊）【明宗】[简文皇帝] {1329年}- 年号：天历
14. 元宁宗（懿璘质班）【宁宗】[昭文皇帝] {1332年}- 年号：至顺
13. 元顺帝（妥欢帖睦尔）【顺帝】[顺皇帝] {1332年-1368年}- 年号：至顺、元统、至元、至正

明朝:
1. 明太祖（朱元璋）【太祖】[开天行道肇纪立极大圣至神仁文义武俊德成功高皇帝] {1368年-1398年}- 年号：洪武
2. 明惠帝（朱允炆）【惠宗】[嗣天章道诚懿渊功观文扬武克仁笃孝让皇帝] {1398年-1402年}- 年号：建文
3. 明成祖（朱棣）【太宗】[启天弘道高明肇运圣武神功纯仁至孝文皇帝] {1402年-1424年}- 年号：永乐
4. 明仁宗（朱高炽）【仁宗】[敬天体道纯诚至德弘文钦武章圣达孝昭皇帝] {1424年-1425年}- 年号：洪熙
5. 明宣宗（朱瞻基）【宣宗】[宪天崇道英明神圣钦文昭武宽仁纯孝章皇帝] {1425年-1435年}- 年号：宣德
6. 明英宗（朱祁镇）【英宗】[法天立道仁明诚敬昭文宪武至德广孝睿皇帝] {1435年-1449年、1457年-1464年}- 年号：正统、天顺
7. 明代宗（朱祁钰）【代宗】[符天建道恭仁康定隆文布武显德崇孝景皇帝] {1449年-1457年}- 年号：景泰
8. 明宪宗（朱见深）【宪宗】[继天凝道诚明仁敬崇文肃武宏德圣孝纯皇帝] {1464年-1487年}- 年号：成化
9. 明孝宗（朱祐樘）【孝宗】[建天明道诚纯中正圣文神武至仁大德敬皇帝] {1487年-1505年}- 年号：弘治
10. 明武宗（朱厚照）【武宗】[承天达道英肃睿哲昭德显功弘文思孝毅皇帝] {1505年-1521年}- 年号：正德
11. 明世宗（朱厚熜）【世宗】[钦天履道英毅神圣宣文广武洪仁大孝肃皇帝] {1521年-1567年}- 年号：嘉靖
12. 明穆宗（朱载垕）【穆宗】[契天隆道渊懿宽仁显文光武纯德弘孝庄皇帝] {1567年-1572年}- 年号：隆庆
13. 明神宗（朱翊钧）【神宗】[范天合道哲肃敦简光文章武安仁止孝显皇帝] {1572年-1620年}- 年号：万历
14. 明光宗（朱常洛）【光宗】[崇天契道英睿恭纯宪文景武渊仁懿孝贞皇帝] {1620年}- 年号：泰昌
15. 明熹宗（朱由校）【熹宗】[达天阐道敦孝笃友章文襄武靖穆庄勤哲皇帝] {1620年-1627年}- 年号：天启
16. 明思宗（朱由检）【思宗】[庄烈愍皇帝] {1627年-1644年}- 年号：崇祯

大顺:
1. 大顺皇帝（李自成）【太祖】[大顺皇帝] {1644年}- 年号：永昌

南明:
1. 弘光帝（朱由崧）【安宗】[奉天遵道宽和静穆修文布武温恭仁孝简皇帝] {1644年-1645年}- 年号：弘光
2. 隆武帝（朱聿键）【绍宗】[配天至道弘毅肃穆思文烈武敏仁广孝襄皇帝] {1645年-1646年}- 年号：隆武
3. 绍武帝（朱聿𨮁） {1646年-1647年}- 年号：绍武
4. 永历帝（朱由榔）【昭宗】[应天推道敏毅恭俭经文纬武礼仁克孝匡皇帝] {1647年-1662年}- 年号：永历

清朝:
1. 清太祖（努尔哈赤）【太祖】[承天广运圣德神功肇纪立极仁孝睿武端毅钦安弘文定业高皇帝] {1616年-1626年}- 年号：天命
2. 清太宗（皇太极）【太宗】[应天兴国弘德彰武宽温仁圣睿孝敬敏昭定隆道显功文皇帝] {1626年-1643年}- 年号：天聪、崇德
3. 世祖顺治帝（福临）【世祖】[体天隆运定统建极英睿钦文显武大德弘功至仁纯孝章皇帝] {1643年-1661年}- 年号：顺治
4. 圣祖康熙帝（玄烨）【圣祖】[合天弘运文武睿哲恭俭宽裕孝敬诚信中和功德大成仁皇帝] {1661年-1722年}- 年号：康熙
5. 世宗雍正帝（胤禛）【世宗】[敬天昌运建中表正文武英明宽仁信毅睿圣大孝至诚宪皇帝] {1722年-1735年}- 年号：雍正 
6. 高宗乾隆帝（弘历）【高宗】[法天隆运至诚先觉体元立极敷文奋武钦明孝慈神圣纯皇帝] {1735年-1796年}- 年号：乾隆
7. 仁宗嘉庆帝（颙琰）【仁宗】[受天兴运敷化绥猷崇文经武光裕孝恭勤俭端敏英哲睿皇帝] {1796年-1820年}- 年号：嘉庆
8. 宣宗道光帝（旻宁）【宣宗】[效天符运立中体正至文圣武智勇仁慈俭勤孝敏宽定成皇帝] {1820年-1850年}- 年号：道光
9. 文宗咸丰帝（奕詝）【文宗】[协天翊运执中垂谟懋德振武圣孝渊恭端仁宽敏庄俭显皇帝] {1850年-1861年}- 年号：咸丰
10. 穆宗同治帝（载淳）【穆宗】[继天开运受中居正保大定功圣智诚孝信敏恭宽明肃毅皇帝] {1861年-1875年}- 年号：同治
11. 德宗光绪帝（载湉）【德宗】[同天崇运大中至正经文纬武仁孝睿智端俭宽勤景皇帝] {1875年-1908年}- 年号：光绪
12. 宣统帝（溥仪）[尊号：宣统] {1908年-1912年}- 年号：宣统

五代十国、南北朝等仍有较多细分皇帝，可以另行深挖。
"""

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
        title += "=" * 30 + "\n\n"
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