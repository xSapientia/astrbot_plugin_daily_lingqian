"""
核心变量定义模块
定义插件所需的各种变量和常量
"""

from datetime import datetime

# 数据路径常量
PLUGIN_DATA_PATH = "data/plugin_data/astrbot_plugin_daily_lingqian"
CONFIG_PATH = "data/config/astrbot_plugin_daily_fortune_config.json"
FORTUNE_DATA_PATH = "data/plugin_data/astrbot_plugin_daily_fortune/fortune_history.json"

# 缓存文件名
LINGQIAN_HISTORY_FILE = "lingqian_history.json"
JIEQIAN_HISTORY_FILE = "jieqian_history.json"
JIEQIAN_CONTENT_FILE = "jieqian_content.json"

# 数字转中文映射表
NUMBER_TO_CHINESE = {
    1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
    6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
    11: "十一", 12: "十二", 13: "十三", 14: "十四", 15: "十五",
    16: "十六", 17: "十七", 18: "十八", 19: "十九", 20: "二十",
    21: "二十一", 22: "二十二", 23: "二十三", 24: "二十四", 25: "二十五",
    26: "二十六", 27: "二十七", 28: "二十八", 29: "二十九", 30: "三十",
    31: "三十一", 32: "三十二", 33: "三十三", 34: "三十四", 35: "三十五",
    36: "三十六", 37: "三十七", 38: "三十八", 39: "三十九", 40: "四十",
    41: "四十一", 42: "四十二", 43: "四十三", 44: "四十四", 45: "四十五",
    46: "四十六", 47: "四十七", 48: "四十八", 49: "四十九", 50: "五十",
    51: "五十一", 52: "五十二", 53: "五十三", 54: "五十四", 55: "五十五",
    56: "五十六", 57: "五十七", 58: "五十八", 59: "五十九", 60: "六十",
    61: "六十一", 62: "六十二", 63: "六十三", 64: "六十四", 65: "六十五",
    66: "六十六", 67: "六十七", 68: "六十八", 69: "六十九", 70: "七十",
    71: "七十一", 72: "七十二", 73: "七十三", 74: "七十四", 75: "七十五",
    76: "七十六", 77: "七十七", 78: "七十八", 79: "七十九", 80: "八十",
    81: "八十一", 82: "八十二", 83: "八十三", 84: "八十四", 85: "八十五",
    86: "八十六", 87: "八十七", 88: "八十八", 89: "八十九", 90: "九十",
    91: "九十一", 92: "九十二", 93: "九十三", 94: "九十四", 95: "九十五",
    96: "九十六", 97: "九十七", 98: "九十八", 99: "九十九", 100: "一百"
}

# 日期和时间变量
def get_date():
    """获取当前日期 YYYY-MM-DD"""
    return datetime.now().strftime('%Y-%m-%d')

def get_today():
    """获取今日日期 YYYY-MM-DD"""
    return datetime.now().strftime('%Y-%m-%d')

def get_time():
    """获取当前时间 HH:MM:SS"""
    return datetime.now().strftime('%H:%M:%S')

# 支持插件配置使用的变量
TEMPLATE_VARIABLES = [
    '{date}',      # 日期
    '{today}',     # 今日日期
    '{user_id}',   # 用户ID
    '{nickname}',  # 用户昵称
    '{card}',      # 用户群名片
    '{title}',     # 用户群头衔
    '{qianxu}',    # 签序（中文数字）
    '{qianming}',  # 签名
    '{jixiong}',   # 吉凶
    '{gongwei}',   # 宫位
    '{lqpic}',     # 灵签图片占位符
    '{jqxh}',      # 解签序号
    '{content}',   # 解签内容
    '{jieqian}',   # 解签结果
    '{lingqian_ranks}',          # 灵签排行显示
    '{lingqian_history_content}', # 灵签历史内容
    '{lqhi_display}',    # 灵签历史展示数量
    '{lqhi_total}',      # 灵签历史总数
    '{lqhi_shang_total}', # 上签总数
    '{lqhi_zhong_total}', # 中签总数
    '{lqhi_xia_total}',   # 下签总数
    '{jieqian_ranks}',           # 解签排行显示
    '{jieqian_history_content}', # 解签历史内容
    '{jieqian_count}',   # 当日解签数
    '{jqhi_display}',    # 解签历史展示数量
    '{jqhi_total}',      # 解签历史总数
    '{jqhi_total_today}', # 今日解签总数  
    '{jqhi_max}',        # 最大日解签数
    '{jqhi_avg}',        # 平均日解签数
    '{jqhi_min}',        # 最小日解签数
]

# 不支持插件配置使用的变量（仅内部使用）
INTERNAL_VARIABLES = [
    '{time}',      # 当前时间（用于随机种子）
]

# 默认配置值
DEFAULT_DISPLAY_COUNT = 10
DEFAULT_SHANG_RATE = "-20, -10, -5, -1, 0, 1, 3, 5, 10"
DEFAULT_ZHONG_RATE = "-1, -3, -5, -10, 0, 1, 5, 10, 20"

# 灵签数量
LINGQIAN_TOTAL_COUNT = 100

# 解签状态
JIEQIAN_STATUS = {
    'IDLE': 'idle',         # 空闲状态
    'PROCESSING': 'processing'  # 解签中
}

# 统计函数
def get_jieqian_statistics() -> dict:
    """获取全局解签统计信息（所有用户）"""
    import json
    import os
    
    try:
        jieqian_history_path = os.path.join(PLUGIN_DATA_PATH, JIEQIAN_HISTORY_FILE)
        today = get_today()
        
        # 统计所有用户的解签数据
        total_count = 0      # 历史解签总数
        today_count = 0      # 今日解签总数
        user_count = 0       # 参与用户数
        
        if os.path.exists(jieqian_history_path):
            with open(jieqian_history_path, 'r', encoding='utf-8') as f:
                jieqian_data = json.load(f)
            
            for user_id, user_data in jieqian_data.items():
                if user_data:  # 用户有数据
                    user_count += 1
                    
                    for date, records in user_data.items():
                        if isinstance(records, list):
                            total_count += len(records)
                            
                            # 统计今日解签数
                            if date == today:
                                today_count += len(records)
        
        return {
            "jqhi_total": total_count,           # 历史解签总数
            "jqhi_total_today": today_count,     # 今日解签总数
            "user_count": user_count,
            # 保持向后兼容
            "total_count": total_count,
            "today_count": today_count
        }
        
    except Exception as e:
        # 这里不能使用logger，因为可能会导致循环导入
        print(f"获取全局解签统计信息失败: {e}")
        return {
            "jqhi_total": 0,
            "jqhi_total_today": 0,
            "user_count": 0,
            "total_count": 0,
            "today_count": 0
        }
