"""皇帝数据生成器模块"""
import random
import re
from config import (
    DYNASTY_ORDER,
    EMPEROR_LINE_PATTERN,
    REIGN_PERIOD_PATTERN,
    ERA_NAME_PATTERN,
    ERA_SPLIT_PATTERN
)

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