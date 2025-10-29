import json
import os
from emperor_generator import EmperorGenerator
from data import emperor_text

print("开始预处理皇帝数据...")

# 1. 初始化生成器
generator = EmperorGenerator()

# 2. 运行耗时的解析函数
generator.parse_emperor_data(emperor_text)

# 3. 获取解析后的数据 (这是一个大列表)
all_emperors_data = generator.all_emperors

# 4. (重要) 我们还需要朝代列表，它也是在解析时生成的
# ###################### 关键修改在这里 ######################
dynasties_data = generator.get_dynasties_list()
# ########################################################

# 5. 将这两部分数据合并到一个字典中
final_data = {
    "all_emperors": all_emperors_data,
    "dynasties": dynasties_data
}

# 6. 定义保存路径 (我们将其保存在 assets 文件夹中)
output_dir = "assets"
output_file = os.path.join(output_dir, "emperors_data.json")

# 确保 assets 文件夹存在
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 7. 将数据写入 JSON 文件
#    使用 ensure_ascii=False 来正确保存中文字符
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False)
    
    print(f"成功！数据已保存到: {output_file}")
    print("现在可以去修改 ctk_gui.py 了。")

except Exception as e:
    print(f"写入文件时出错: {e}")