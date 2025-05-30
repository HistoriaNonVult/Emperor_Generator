"""配置文件，存储常量和配置项"""

# 窗口配置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
WINDOW_TITLE = "受命於天，既壽永昌"

# 朝代顺序
DYNASTY_ORDER = [
    "秦朝",
    "西汉", "新朝", "东汉",
    "曹魏", "蜀汉", "东吴",
    "西晋", "东晋",
    "刘宋", "齐", "梁", "陈",
    "北魏", "东魏", "西魏", "北齐", "北周",
    "隋朝",
    "唐朝",
    "后梁", "后唐", "后晋", "后汉", "后周",
    "北宋", "辽", "金", "南宋",
    "元朝",
    "明朝", "大顺", "南明",
    "清朝"
]

# 正则表达式模式
EMPEROR_LINE_PATTERN = r'\d+\.\s*([^（]+)(?:（([^）]+)）)?(?:【([^】]+)】)?(?:\[([^\]]+)\])?'
REIGN_PERIOD_PATTERN = r'\{([^}]+)\}'
ERA_NAME_PATTERN = r'年号：\[(.*?)\]|年号：(.*?)(?=\s|$)'
ERA_SPLIT_PATTERN = r'[、，,;；]'
