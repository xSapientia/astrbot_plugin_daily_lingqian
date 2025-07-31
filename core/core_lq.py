"""
每日灵签核心模块
处理灵签的抽取、查询、历史记录等核心功能
"""

import json
import os
import random
import hashlib
from datetime import datetime
from astrbot.api import logger
from .variable import (
    PLUGIN_DATA_PATH, LINGQIAN_HISTORY_FILE, NUMBER_TO_CHINESE, 
    LINGQIAN_TOTAL_COUNT, get_date, get_today, get_time
)

class DailyLingqianManager:
    """每日灵签管理器"""
    
    def __init__(self):
        self.ensure_data_directory()
        self.lingqian_history_path = os.path.join(PLUGIN_DATA_PATH, LINGQIAN_HISTORY_FILE)
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        if not os.path.exists(PLUGIN_DATA_PATH):
            os.makedirs(PLUGIN_DATA_PATH, exist_ok=True)
    
    def load_lingqian_history(self) -> dict:
        """加载灵签历史数据"""
        try:
            if os.path.exists(self.lingqian_history_path):
                with open(self.lingqian_history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载灵签历史数据失败: {e}")
            return {}
    
    def save_lingqian_history(self, history_data: dict):
        """保存灵签历史数据"""
        try:
            with open(self.lingqian_history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存灵签历史数据失败: {e}")
    
    def generate_random_seed(self, user_id: str) -> str:
        """生成随机种子"""
        try:
            today = get_today()
            time_str = get_time()
            seed_string = f"{user_id}{today}{time_str}"
            return hashlib.md5(seed_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"生成随机种子失败: {e}")
            return f"{user_id}{get_today()}"
    
    def draw_lingqian(self, user_id: str, fortune_adjustment: dict = None) -> dict:
        """
        抽取灵签
        :param user_id: 用户ID
        :param fortune_adjustment: 人品调整参数
        :return: 包含签序、签名等信息的字典
        """
        try:
            # 检查今日是否已抽取
            history_data = self.load_lingqian_history()
            today = get_today()
            
            if user_id in history_data and today in history_data[user_id]:
                # 已抽取，返回今日的签
                today_data = history_data[user_id][today]
                if isinstance(today_data, dict):
                    return today_data
                else:
                    # 兼容旧格式
                    qianxu = int(today_data)
                    return self._build_lingqian_result(qianxu)
            
            # 生成随机数
            seed = self.generate_random_seed(user_id)
            random.seed(seed)
            
            # 根据人品调整概率（如果启用）
            qianxu = self._draw_with_fortune_adjustment(fortune_adjustment)
            
            # 获取灵签详细信息
            result = self._build_lingqian_result(qianxu)
            
            # 保存到历史记录
            if user_id not in history_data:
                history_data[user_id] = {}
            history_data[user_id][today] = result
            
            self.save_lingqian_history(history_data)
            
            return result
            
        except Exception as e:
            logger.error(f"抽取灵签失败: {e}")
            # 返回默认结果
            return self._build_lingqian_result(1)
    
    def _draw_with_fortune_adjustment(self, fortune_adjustment: dict = None) -> int:
        """根据人品值调整概率抽取签序"""
        try:
            if not fortune_adjustment:
                # 无调整，纯随机
                return random.randint(1, LINGQIAN_TOTAL_COUNT)
            
            # 读取排序数据
            sort_data = self._load_sort_data()
            if not sort_data:
                return random.randint(1, LINGQIAN_TOTAL_COUNT)
            
            # 分类签序
            shang_qian = [item['签序'] for item in sort_data if item['吉凶'] == '上签']
            zhong_qian = [item['签序'] for item in sort_data if item['吉凶'] == '中签']
            xia_qian = [item['签序'] for item in sort_data if item['吉凶'] == '下签']
            
            # 获取调整参数
            shang_adjustment = fortune_adjustment.get('shang_rate', 0)
            zhong_adjustment = fortune_adjustment.get('zhong_rate', 0)
            
            # 计算基础概率
            base_shang_prob = len(shang_qian) / LINGQIAN_TOTAL_COUNT
            base_zhong_prob = len(zhong_qian) / LINGQIAN_TOTAL_COUNT
            base_xia_prob = len(xia_qian) / LINGQIAN_TOTAL_COUNT
            
            # 应用调整
            adjusted_shang_prob = max(0, min(1, base_shang_prob + shang_adjustment / 100))
            adjusted_zhong_prob = max(0, min(1, base_zhong_prob + zhong_adjustment / 100))
            adjusted_xia_prob = max(0, 1 - adjusted_shang_prob - adjusted_zhong_prob)
            
            # 归一化概率
            total_prob = adjusted_shang_prob + adjusted_zhong_prob + adjusted_xia_prob
            if total_prob > 0:
                adjusted_shang_prob /= total_prob
                adjusted_zhong_prob /= total_prob
                adjusted_xia_prob /= total_prob
            
            # 根据概率抽取
            rand_val = random.random()
            if rand_val < adjusted_shang_prob:
                return random.choice(shang_qian)
            elif rand_val < adjusted_shang_prob + adjusted_zhong_prob:
                return random.choice(zhong_qian)
            else:
                return random.choice(xia_qian)
                
        except Exception as e:
            logger.error(f"按人品调整抽签失败: {e}")
            return random.randint(1, LINGQIAN_TOTAL_COUNT)
    
    def _load_sort_data(self) -> list:
        """加载排序数据"""
        try:
            sort_path = os.path.join(os.path.dirname(__file__), '..', 'sort', 'sort.json')
            if os.path.exists(sort_path):
                with open(sort_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"加载排序数据失败: {e}")
            return []
    
    def _build_lingqian_result(self, qianxu: int) -> dict:
        """构建灵签结果"""
        try:
            # 获取灵签详细信息
            lingqian_data = self._load_lingqian_data(qianxu)
            
            # 获取吉凶信息
            sort_data = self._load_sort_data()
            jixiong = "未知"
            for item in sort_data:
                if item.get('签序') == qianxu:
                    jixiong = item.get('吉凶', '未知')
                    break
            
            # 解析签名和宫位
            qianming = "未知"
            gongwei = "未知"
            
            if lingqian_data and '内容' in lingqian_data:
                content = lingqian_data['内容']
                # 提取签名（第一行包含签名）
                lines = content.split('\n')
                for line in lines:
                    if '签: ' in line or '第' in line and '签' in line:
                        # 提取签名部分
                        if ':' in line:
                            qianming = line.split(':', 1)[1].strip()
                        break
                
                # 提取宫位信息
                for line in lines:
                    if '宫位' in line:
                        if '：' in line:
                            gongwei = line.split('：', 1)[1].strip()
                        elif ':' in line:
                            gongwei = line.split(':', 1)[1].strip()
                        break
            
            return {
                'qianxu': qianxu,
                'qianxu_chinese': NUMBER_TO_CHINESE.get(qianxu, str(qianxu)),
                'qianming': qianming,
                'jixiong': jixiong,
                'gongwei': gongwei,
                'lingqian_data': lingqian_data
            }
            
        except Exception as e:
            logger.error(f"构建灵签结果失败: {e}")
            return {
                'qianxu': qianxu,
                'qianxu_chinese': NUMBER_TO_CHINESE.get(qianxu, str(qianxu)),
                'qianming': "未知",
                'jixiong': "未知",
                'gongwei': "未知",
                'lingqian_data': None
            }
    
    def _load_lingqian_data(self, qianxu: int) -> dict:
        """加载指定签序的灵签数据"""
        try:
            lingqian_path = os.path.join(os.path.dirname(__file__), '..', 'guanyin_lingqian', f'{qianxu}.json')
            if os.path.exists(lingqian_path):
                with open(lingqian_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"加载灵签数据失败 (签序: {qianxu}): {e}")
            return None
    
    def get_today_lingqian(self, user_id: str) -> dict:
        """获取用户今日的灵签"""
        try:
            history_data = self.load_lingqian_history()
            today = get_today()
            
            if user_id in history_data and today in history_data[user_id]:
                today_data = history_data[user_id][today]
                if isinstance(today_data, dict):
                    return today_data
                else:
                    # 兼容旧格式，重新构建
                    qianxu = int(today_data)
                    result = self._build_lingqian_result(qianxu)
                    # 更新存储格式
                    history_data[user_id][today] = result
                    self.save_lingqian_history(history_data)
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"获取今日灵签失败: {e}")
            return None
    
    def get_user_history(self, user_id: str, limit: int = 10) -> list:
        """获取用户的历史记录"""
        try:
            history_data = self.load_lingqian_history()
            
            if user_id not in history_data:
                return []
            
            user_history = history_data[user_id]
            
            # 按日期排序（最新的在前）
            sorted_history = []
            for date, data in user_history.items():
                if isinstance(data, dict):
                    history_item = data.copy()
                    history_item['date'] = date
                    sorted_history.append(history_item)
                else:
                    # 兼容旧格式
                    qianxu = int(data)
                    result = self._build_lingqian_result(qianxu)
                    result['date'] = date
                    sorted_history.append(result)
            
            # 按日期倒序排列
            sorted_history.sort(key=lambda x: x['date'], reverse=True)
            
            return sorted_history[:limit]
            
        except Exception as e:
            logger.error(f"获取用户历史记录失败: {e}")
            return []
    
    def get_user_statistics(self, user_id: str) -> dict:
        """获取用户的统计信息"""
        try:
            history_data = self.load_lingqian_history()
            
            if user_id not in history_data:
                return {
                    'total': 0,
                    'shang_total': 0,
                    'zhong_total': 0,
                    'xia_total': 0
                }
            
            user_history = history_data[user_id]
            sort_data = self._load_sort_data()
            
            total = len(user_history)
            shang_total = 0
            zhong_total = 0
            xia_total = 0
            
            for date, data in user_history.items():
                if isinstance(data, dict):
                    qianxu = data.get('qianxu', 0)
                else:
                    qianxu = int(data)
                
                # 查找对应的吉凶
                for item in sort_data:
                    if item.get('签序') == qianxu:
                        jixiong = item.get('吉凶', '')
                        if jixiong == '上签':
                            shang_total += 1
                        elif jixiong == '中签':
                            zhong_total += 1
                        elif jixiong == '下签':
                            xia_total += 1
                        break
            
            return {
                'total': total,
                'shang_total': shang_total,
                'zhong_total': zhong_total,
                'xia_total': xia_total
            }
            
        except Exception as e:
            logger.error(f"获取用户统计信息失败: {e}")
            return {
                'total': 0,
                'shang_total': 0,
                'zhong_total': 0,
                'xia_total': 0
            }
    
    def delete_user_history_except_today(self, user_id: str) -> bool:
        """删除用户除今日外的历史记录"""
        try:
            history_data = self.load_lingqian_history()
            
            if user_id not in history_data:
                return True
            
            today = get_today()
            user_history = history_data[user_id]
            
            # 保留今日数据
            if today in user_history:
                history_data[user_id] = {today: user_history[today]}
            else:
                del history_data[user_id]
            
            self.save_lingqian_history(history_data)
            return True
            
        except Exception as e:
            logger.error(f"删除用户历史记录失败: {e}")
            return False
    
    def initialize_user_today(self, user_id: str) -> bool:
        """初始化用户今日记录（清除今日数据）"""
        try:
            history_data = self.load_lingqian_history()
            today = get_today()
            
            if user_id in history_data and today in history_data[user_id]:
                del history_data[user_id][today]
                
                # 如果用户没有其他记录，删除用户条目
                if not history_data[user_id]:
                    del history_data[user_id]
                
                self.save_lingqian_history(history_data)
            
            return True
            
        except Exception as e:
            logger.error(f"初始化用户今日记录失败: {e}")
            return False
    
    def reset_all_data(self) -> bool:
        """重置所有数据"""
        try:
            if os.path.exists(self.lingqian_history_path):
                os.remove(self.lingqian_history_path)
            return True
        except Exception as e:
            logger.error(f"重置所有数据失败: {e}")
            return False
    
    def get_image_path(self, qianxu: int, pics_version: str) -> str:
        """获取灵签图片路径"""
        try:
            # 构建图片路径
            resource_path = os.path.join(os.path.dirname(__file__), '..', 'resource', pics_version)
            
            # 支持的图片格式
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            
            for ext in image_extensions:
                image_path = os.path.join(resource_path, f'{qianxu}{ext}')
                if os.path.exists(image_path):
                    return image_path
            
            # 如果找不到对应图片，返回占位符路径
            return f"resource/{pics_version}/{qianxu}.jpg"
            
        except Exception as e:
            logger.error(f"获取灵签图片路径失败: {e}")
            return f"resource/{pics_version}/{qianxu}.jpg"
