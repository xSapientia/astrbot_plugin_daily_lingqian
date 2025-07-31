"""
LLM核心模块
处理解签时的LLM调用功能
"""

import json
import os
import asyncio
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from .variable import PLUGIN_DATA_PATH, JIEQIAN_HISTORY_FILE, JIEQIAN_CONTENT_FILE, JIEQIAN_STATUS, get_today

class LLMManager:
    """LLM管理器"""
    
    def __init__(self, context, config):
        self.context = context
        self.config = config
        self.jieqian_history_path = os.path.join(PLUGIN_DATA_PATH, JIEQIAN_HISTORY_FILE)
        self.jieqian_content_path = os.path.join(PLUGIN_DATA_PATH, JIEQIAN_CONTENT_FILE)
        self.jieqian_status = {}  # 解签状态缓存
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        if not os.path.exists(PLUGIN_DATA_PATH):
            os.makedirs(PLUGIN_DATA_PATH, exist_ok=True)
    
    def load_jieqian_history(self) -> dict:
        """加载解签历史数据"""
        try:
            if os.path.exists(self.jieqian_history_path):
                with open(self.jieqian_history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载解签历史数据失败: {e}")
            return {}
    
    def save_jieqian_history(self, history_data: dict):
        """保存解签历史数据"""
        try:
            with open(self.jieqian_history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存解签历史数据失败: {e}")
    
    def load_jieqian_content(self) -> dict:
        """加载解签内容数据"""
        try:
            if os.path.exists(self.jieqian_content_path):
                with open(self.jieqian_content_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载解签内容数据失败: {e}")
            return {}
    
    def save_jieqian_content(self, content_data: dict):
        """保存解签内容数据"""
        try:
            with open(self.jieqian_content_path, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存解签内容数据失败: {e}")
    
    def is_user_processing(self, user_id: str) -> bool:
        """检查用户是否正在解签中"""
        return self.jieqian_status.get(user_id) == JIEQIAN_STATUS['PROCESSING']
    
    def set_user_processing(self, user_id: str, processing: bool):
        """设置用户解签状态"""
        if processing:
            self.jieqian_status[user_id] = JIEQIAN_STATUS['PROCESSING']
        else:
            self.jieqian_status[user_id] = JIEQIAN_STATUS['IDLE']
    
    async def process_jieqian(self, event: AstrMessageEvent, user_id: str, lingqian_data: dict, content: str) -> str:
        """
        处理解签请求
        :param event: 消息事件
        :param user_id: 用户ID
        :param lingqian_data: 灵签数据
        :param content: 解签内容
        :return: 解签结果
        """
        try:
            # 检查是否正在解签中
            if self.is_user_processing(user_id):
                return None  # 返回None表示正在处理中
            
            # 设置处理状态
            self.set_user_processing(user_id, True)
            
            try:
                # 调用LLM进行解签
                jieqian_result = await self._call_llm_for_jieqian(event, lingqian_data, content)
                
                # 保存解签记录
                await self._save_jieqian_record(user_id, content, jieqian_result)
                
                return jieqian_result
                
            finally:
                # 解除处理状态
                self.set_user_processing(user_id, False)
                
        except Exception as e:
            logger.error(f"处理解签请求失败: {e}")
            self.set_user_processing(user_id, False)
            return "解签过程中发生错误，请稍后重试。"
    
    async def _call_llm_for_jieqian(self, event: AstrMessageEvent, lingqian_data: dict, content: str) -> str:
        """调用LLM进行解签"""
        try:
            # 构建提示词
            prompt = self._build_jieqian_prompt(lingqian_data, content)
            
            # 获取人格
            persona = await self._get_persona()
            
            # 尝试使用配置的供应商
            provider = await self._get_provider()
            
            if provider:
                # 使用指定的供应商
                contexts = []
                if persona:
                    contexts.append({"role": "system", "content": persona})
                
                # 添加风格提示
                style_prompt = self.config.get('jieqian_config', {}).get('style_prompt', '')
                if style_prompt:
                    contexts.append({"role": "system", "content": style_prompt})
                
                response = await provider.text_chat(
                    prompt=prompt,
                    contexts=contexts,
                    session_id=None,
                    image_urls=[],
                    func_tool=None,
                    system_prompt=""
                )
                
                if response and response.completion_text:
                    return response.completion_text.strip()
            
            # 如果指定供应商失败，尝试使用默认供应商
            default_provider = self.context.get_using_provider()
            if default_provider:
                contexts = []
                if persona:
                    contexts.append({"role": "system", "content": persona})
                
                style_prompt = self.config.get('jieqian_config', {}).get('style_prompt', '')
                if style_prompt:
                    contexts.append({"role": "system", "content": style_prompt})
                
                response = await default_provider.text_chat(
                    prompt=prompt,
                    contexts=contexts,
                    session_id=None,
                    image_urls=[],
                    func_tool=None,
                    system_prompt=""
                )
                
                if response and response.completion_text:
                    return response.completion_text.strip()
            
            # 如果都失败了，返回错误信息
            logger.error("所有LLM供应商都无法使用")
            return "当前无法连接到AI服务，请稍后重试。"
            
        except Exception as e:
            logger.error(f"LLM解签失败: {e}")
            return "解签过程中发生错误，请稍后重试。"
    
    def _build_jieqian_prompt(self, lingqian_data: dict, content: str) -> str:
        """构建解签提示词"""
        try:
            if not lingqian_data or '内容' not in lingqian_data:
                return f"请为以下问题提供指导：{content}"
            
            lingqian_content = lingqian_data['内容']
            
            prompt = f"""根据以下观音灵签内容，为用户的问题提供解读和指导：

灵签内容：
{lingqian_content}

用户问题：{content}

请结合灵签的寓意，为用户提供智慧的解读和人生指导。"""
            
            return prompt
            
        except Exception as e:
            logger.error(f"构建解签提示词失败: {e}")
            return f"请为以下问题提供指导：{content}"
    
    async def _get_persona(self) -> str:
        """获取人格设置"""
        try:
            persona_name = self.config.get('jieqian_config', {}).get('persona', '')
            if not persona_name:
                return ""
            
            # 获取所有人格
            personas = self.context.provider_manager.personas
            for persona in personas:
                if persona.name == persona_name:
                    logger.info(f"获取人格成功, {persona.prompt[:10]}...")
                    return persona.prompt
            
            logger.warning(f"未找到指定人格: {persona_name}")
            return ""
            
        except Exception as e:
            logger.error(f"人格获取失败: {e}")
            return ""
    
    async def _get_provider(self):
        """获取LLM供应商"""
        try:
            jieqian_config = self.config.get('jieqian_config', {})
            
            # 优先使用指定的供应商ID
            provider_id = jieqian_config.get('provider_id', '')
            if provider_id:
                provider = self.context.get_provider_by_id(provider_id)
                if provider:
                    # 测试连接
                    test_response = await provider.text_chat(
                        prompt="reply *PONG* only",
                        contexts=[],
                        session_id=None,
                        image_urls=[],
                        func_tool=None,
                        system_prompt=""
                    )
                    if test_response:
                        logger.info(f"成功连接{provider_id}")
                        return provider
            
            # 尝试使用第三方API
            api_key = jieqian_config.get('api_key', '')
            api_url = jieqian_config.get('api_url', '')
            model = jieqian_config.get('model', '')
            
            if api_key and api_url and model:
                # 这里可以实现第三方API调用
                # 由于需要实现完整的OpenAI兼容客户端，暂时跳过
                logger.info("第三方API配置已找到，但暂未实现")
            
            return None
            
        except Exception as e:
            logger.error(f"获取LLM供应商失败: {e}")
            return None
    
    async def _save_jieqian_record(self, user_id: str, content: str, jieqian_result: str):
        """保存解签记录"""
        try:
            today = get_today()
            
            # 保存到历史记录
            history_data = self.load_jieqian_history()
            if user_id not in history_data:
                history_data[user_id] = {}
            if today not in history_data[user_id]:
                history_data[user_id][today] = []
            
            history_data[user_id][today].append({
                'content': content,
                'result': jieqian_result,
                'timestamp': get_today()
            })
            
            self.save_jieqian_history(history_data)
            
            # 保存到内容记录
            content_data = self.load_jieqian_content()
            if user_id not in content_data:
                content_data[user_id] = []
            
            content_data[user_id].append({
                'date': today,
                'content': content,
                'result': jieqian_result,
                'timestamp': get_today()
            })
            
            self.save_jieqian_content(content_data)
            
        except Exception as e:
            logger.error(f"保存解签记录失败: {e}")
    
    def get_user_today_jieqian_list(self, user_id: str) -> list:
        """获取用户今日解签列表"""
        try:
            history_data = self.load_jieqian_history()
            today = get_today()
            
            if user_id in history_data and today in history_data[user_id]:
                return history_data[user_id][today]
            
            return []
            
        except Exception as e:
            logger.error(f"获取用户今日解签列表失败: {e}")
            return []
    
    def get_user_jieqian_history(self, user_id: str, limit: int = 10) -> list:
        """获取用户解签历史"""
        try:
            history_data = self.load_jieqian_history()
            
            if user_id not in history_data:
                return []
            
            user_history = history_data[user_id]
            
            # 按日期排序（最新的在前）
            sorted_history = []
            for date, day_data in user_history.items():
                if isinstance(day_data, list):
                    jieqian_count = len(day_data)
                    sorted_history.append({
                        'date': date,
                        'jieqian_count': jieqian_count,
                        'details': day_data
                    })
            
            # 按日期倒序排列
            sorted_history.sort(key=lambda x: x['date'], reverse=True)
            
            return sorted_history[:limit]
            
        except Exception as e:
            logger.error(f"获取用户解签历史失败: {e}")
            return []
    
    def get_user_jieqian_statistics(self, user_id: str) -> dict:
        """获取用户解签统计信息"""
        try:
            history_data = self.load_jieqian_history()
            
            if user_id not in history_data:
                return {
                    'total': 0,
                    'max': 0,
                    'avg': 0,
                    'min': 0
                }
            
            user_history = history_data[user_id]
            daily_counts = []
            total = 0
            
            for date, day_data in user_history.items():
                if isinstance(day_data, list):
                    count = len(day_data)
                    daily_counts.append(count)
                    total += count
            
            if not daily_counts:
                return {
                    'total': 0,
                    'max': 0,
                    'avg': 0,
                    'min': 0
                }
            
            max_count = max(daily_counts)
            min_count = min(daily_counts)
            avg_count = round(sum(daily_counts) / len(daily_counts), 1)
            
            return {
                'total': total,
                'max': max_count,
                'avg': avg_count,
                'min': min_count
            }
            
        except Exception as e:
            logger.error(f"获取用户解签统计信息失败: {e}")
            return {
                'total': 0,
                'max': 0,
                'avg': 0,
                'min': 0
            }
    
    def delete_user_jieqian_history_except_today(self, user_id: str) -> bool:
        """删除用户除今日外的解签历史记录"""
        try:
            history_data = self.load_jieqian_history()
            content_data = self.load_jieqian_content()
            today = get_today()
            
            # 处理历史记录
            if user_id in history_data:
                user_history = history_data[user_id]
                if today in user_history:
                    history_data[user_id] = {today: user_history[today]}
                else:
                    del history_data[user_id]
                
                self.save_jieqian_history(history_data)
            
            # 处理内容记录
            if user_id in content_data:
                user_content = content_data[user_id]
                today_content = [item for item in user_content if item.get('date') == today]
                if today_content:
                    content_data[user_id] = today_content
                else:
                    del content_data[user_id]
                
                self.save_jieqian_content(content_data)
            
            return True
            
        except Exception as e:
            logger.error(f"删除用户解签历史记录失败: {e}")
            return False
    
    def initialize_user_jieqian_today(self, user_id: str) -> bool:
        """初始化用户今日解签记录（清除今日数据）"""
        try:
            history_data = self.load_jieqian_history()
            content_data = self.load_jieqian_content()
            today = get_today()
            
            # 清除历史记录中的今日数据
            if user_id in history_data and today in history_data[user_id]:
                del history_data[user_id][today]
                if not history_data[user_id]:
                    del history_data[user_id]
                self.save_jieqian_history(history_data)
            
            # 清除内容记录中的今日数据
            if user_id in content_data:
                user_content = content_data[user_id]
                content_data[user_id] = [item for item in user_content if item.get('date') != today]
                if not content_data[user_id]:
                    del content_data[user_id]
                self.save_jieqian_content(content_data)
            
            return True
            
        except Exception as e:
            logger.error(f"初始化用户今日解签记录失败: {e}")
            return False
    
    def reset_all_jieqian_data(self) -> bool:
        """重置所有解签数据"""
        try:
            if os.path.exists(self.jieqian_history_path):
                os.remove(self.jieqian_history_path)
            if os.path.exists(self.jieqian_content_path):
                os.remove(self.jieqian_content_path)
            return True
        except Exception as e:
            logger.error(f"重置所有解签数据失败: {e}")
            return False
