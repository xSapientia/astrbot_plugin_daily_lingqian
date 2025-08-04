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
    
    async def process_jieqian_self(self, event: AstrMessageEvent, user_id: str, lingqian_data: dict) -> str:
        """
        处理签文自身拆解请求（当用户没有提供具体问题时）
        :param event: 消息事件
        :param user_id: 用户ID
        :param lingqian_data: 灵签数据
        :return: 签文拆解结果
        """
        try:
            # 检查是否正在解签中
            if self.is_user_processing(user_id):
                return None  # 返回None表示正在处理中
            
            # 设置处理状态
            self.set_user_processing(user_id, True)
            
            try:
                # 调用LLM进行签文拆解
                jieqian_result = await self._call_llm_for_jieqian_self(event, lingqian_data)
                
                # 保存解签记录（使用特殊标记表示签文拆解）
                await self._save_jieqian_record(user_id, "[签文拆解]", jieqian_result)
                
                return jieqian_result
                
            finally:
                # 解除处理状态
                self.set_user_processing(user_id, False)
                
        except Exception as e:
            logger.error(f"处理签文拆解请求失败: {e}")
            self.set_user_processing(user_id, False)
            return "签文拆解过程中发生错误，请稍后重试。"
    
    async def _call_llm_for_jieqian(self, event: AstrMessageEvent, lingqian_data: dict, content: str) -> str:
        """调用LLM进行解签 - 参考GitHub完美方案"""
        try:
            # 获取Provider - 使用优先级:插件配置的provider_id>第三方api>默认provider
            provider = None
            provider_id = self.config.get('jieqian_config', {}).get('provider_id', '').strip()
            
            # 1. 优先使用插件配置的provider_id
            if provider_id:
                provider = self.context.get_provider_by_id(provider_id)
                if provider:
                    logger.debug(f"[LLMManager] 使用指定provider: {provider_id}")
                else:
                    logger.warning(f"[LLMManager] 指定的provider_id不存在: {provider_id}")
            
            # 2. 如果没有指定provider或指定的不存在，使用默认provider
            if not provider:
                provider = self.context.get_using_provider()
                if provider:
                    logger.debug("[LLMManager] 使用默认provider")
            
            if not provider:
                logger.warning("[LLMManager] 没有可用的LLM提供商")
                return "当前无法连接到AI服务，请稍后重试。"
            
            # 获取人格prompt - 使用优先级:插件配置的persona>默认persona
            persona_prompt = ""
            persona_name = self.config.get('jieqian_config', {}).get('persona', '').strip()
            if persona_name:
                # 使用指定的人格
                personas = self.context.provider_manager.personas
                for p in personas:
                    if p.get('name') == persona_name:
                        persona_prompt = p.get('prompt', '')
                        logger.debug(f"[LLMManager] 使用指定人格: {persona_name}")
                        break
                else:
                    logger.warning(f"[LLMManager] 未找到指定人格: {persona_name}")
            
            if not persona_prompt:
                # 使用默认人格
                default_persona = self.context.provider_manager.selected_default_persona
                if default_persona and default_persona.get("name"):
                    default_persona_name = default_persona["name"]
                    personas = self.context.provider_manager.personas
                    for p in personas:
                        if p.get('name') == default_persona_name:
                            persona_prompt = p.get('prompt', '')
                            logger.debug(f"[LLMManager] 使用默认人格: {default_persona_name}")
                            break
            
            # 获取解签提示词模板
            jieqian_prompt = self.config.get('jieqian_config', {}).get('jieqian_prompt', '')
            if not jieqian_prompt:
                jieqian_prompt = "请根据{user_id}今日抽取的灵签, 对其提出的问题进行解签, 50字以内"
            
            # 根据用户ID和灵签数据构建完整的解签提示词
            full_prompt = await self._build_detailed_jieqian_prompt(
                persona_prompt, jieqian_prompt, lingqian_data, content, event
            )
            
            # 获取配置的超时时间
            timeout_seconds = self.config.get('jieqian_config', {}).get('llm_timeout', 120)
            
            # 调用LLM - 使用人格prompt和解签提示词，不使用system_prompt避免兼容性问题
            response = await asyncio.wait_for(
                provider.text_chat(
                    prompt=full_prompt,
                    session_id=None,  # 不使用会话管理
                    contexts=[],  # 不使用历史上下文
                    image_urls=[],  # 不传递图片
                    func_tool=None,  # 不使用函数工具
                    system_prompt=""  # 不使用额外的system_prompt，人格已经在prompt中
                ),
                timeout=float(timeout_seconds)  # 使用配置的超时时间
            )
            
            if response and response.completion_text:
                content = response.completion_text.strip()
                logger.debug(f"[LLMManager] LLM解签回复: {content[:50]}...")
                return content
            else:
                logger.warning("[LLMManager] LLM返回空响应")
                return "解签过程中AI未能提供回复，请稍后重试。"
                
        except asyncio.TimeoutError:
            logger.error("[LLMManager] LLM解签超时")
            return "解签过程中AI响应超时，请稍后重试。"
        except Exception as e:
            logger.error(f"[LLMManager] LLM解签失败: {e}")
            return "解签过程中发生错误，请稍后重试。"
    
    async def _call_llm_for_jieqian_self(self, event: AstrMessageEvent, lingqian_data: dict) -> str:
        """调用LLM进行签文自身拆解"""
        try:
            # 获取Provider - 使用优先级:插件配置的provider_id>第三方api>默认provider
            provider = None
            provider_id = self.config.get('jieqian_config', {}).get('provider_id', '').strip()
            
            # 1. 优先使用插件配置的provider_id
            if provider_id:
                provider = self.context.get_provider_by_id(provider_id)
                if provider:
                    logger.debug(f"[LLMManager] 使用指定provider: {provider_id}")
                else:
                    logger.warning(f"[LLMManager] 指定的provider_id不存在: {provider_id}")
            
            # 2. 如果没有指定provider或指定的不存在，使用默认provider
            if not provider:
                provider = self.context.get_using_provider()
                if provider:
                    logger.debug("[LLMManager] 使用默认provider")
            
            if not provider:
                logger.warning("[LLMManager] 没有可用的LLM提供商")
                return "当前无法连接到AI服务，请稍后重试。"
            
            # 获取人格prompt - 使用优先级:插件配置的persona>默认persona
            persona_prompt = ""
            persona_name = self.config.get('jieqian_config', {}).get('persona', '').strip()
            if persona_name:
                # 使用指定的人格
                personas = self.context.provider_manager.personas
                for p in personas:
                    if p.get('name') == persona_name:
                        persona_prompt = p.get('prompt', '')
                        logger.debug(f"[LLMManager] 使用指定人格: {persona_name}")
                        break
                else:
                    logger.warning(f"[LLMManager] 未找到指定人格: {persona_name}")
            
            if not persona_prompt:
                # 使用默认人格
                default_persona = self.context.provider_manager.selected_default_persona
                if default_persona and default_persona.get("name"):
                    default_persona_name = default_persona["name"]
                    personas = self.context.provider_manager.personas
                    for p in personas:
                        if p.get('name') == default_persona_name:
                            persona_prompt = p.get('prompt', '')
                            logger.debug(f"[LLMManager] 使用默认人格: {default_persona_name}")
                            break
            
            # 获取签文拆解提示词模板
            jieqian_self_prompt = self.config.get('jieqian_config', {}).get('jieqian_self_prompt', '')
            if not jieqian_self_prompt:
                jieqian_self_prompt = "请对{user_id}今日抽取的灵签进行详细的翻译和拆解，包括签文含义、诗句解读、人生指导等，让用户更好地理解这支灵签的寓意，200字以内"
            
            # 根据用户ID和灵签数据构建完整的签文拆解提示词
            full_prompt = await self._build_detailed_jieqian_self_prompt(
                persona_prompt, jieqian_self_prompt, lingqian_data, event
            )
            
            # 获取配置的超时时间
            timeout_seconds = self.config.get('jieqian_config', {}).get('llm_timeout', 120)
            
            # 调用LLM - 使用人格prompt和签文拆解提示词，不使用system_prompt避免兼容性问题
            response = await asyncio.wait_for(
                provider.text_chat(
                    prompt=full_prompt,
                    session_id=None,  # 不使用会话管理
                    contexts=[],  # 不使用历史上下文
                    image_urls=[],  # 不传递图片
                    func_tool=None,  # 不使用函数工具
                    system_prompt=""  # 不使用额外的system_prompt，人格已经在prompt中
                ),
                timeout=float(timeout_seconds)  # 使用配置的超时时间
            )
            
            if response and response.completion_text:
                content = response.completion_text.strip()
                logger.debug(f"[LLMManager] LLM签文拆解回复: {content[:50]}...")
                return content
            else:
                logger.warning("[LLMManager] LLM返回空响应")
                return "签文拆解过程中AI未能提供回复，请稍后重试。"
                
        except asyncio.TimeoutError:
            logger.error("[LLMManager] LLM签文拆解超时")
            return "签文拆解过程中AI响应超时，请稍后重试。"
        except Exception as e:
            logger.error(f"[LLMManager] LLM签文拆解失败: {e}")
            return "签文拆解过程中发生错误，请稍后重试。"
    
    async def _build_detailed_jieqian_self_prompt(self, persona_prompt: str, jieqian_self_prompt: str, 
                                                lingqian_data: dict, event: AstrMessageEvent) -> str:
        """构建详细的签文拆解提示词"""
        try:
            # 获取用户信息
            from .core_lq_userinfo import UserInfoManager
            user_info = await UserInfoManager.get_user_info(event)
            user_name = user_info.get('card', user_info.get('nickname', '用户'))
            
            # 读取具体的灵签内容
            qianxu = lingqian_data.get('qianxu', 0)
            detailed_lingqian = await self._load_lingqian_json(qianxu)
            
            # 构建完整的prompt
            full_prompt = ""
            
            # 添加人格设定
            if persona_prompt:
                full_prompt += f"{persona_prompt}\n\n"
            
            # 添加签文拆解提示词，并插入用户名称
            formatted_jieqian_self_prompt = jieqian_self_prompt.replace("{user_id}", user_name)
            full_prompt += f"{formatted_jieqian_self_prompt}\n\n"
            
            # 添加具体的灵签信息
            if detailed_lingqian:
                full_prompt += f"「{user_name}」今日抽取的观音灵签信息：\n"
                full_prompt += f"签序：{detailed_lingqian.get('签序', qianxu)}\n"
                full_prompt += f"签名：{detailed_lingqian.get('签名', '')}\n"
                full_prompt += f"吉凶：{detailed_lingqian.get('吉凶', '')}\n"
                full_prompt += f"宫位：{detailed_lingqian.get('宫位', '')}\n\n"
                
                # 添加详细内容
                if '内容' in detailed_lingqian:
                    full_prompt += f"灵签内容：\n{detailed_lingqian['内容']}\n\n"
                
                # 添加诗句等其他信息
                for key in ['诗曰', '解曰', '圣意', '东坡解']:
                    if key in detailed_lingqian:
                        full_prompt += f"{key}：{detailed_lingqian[key]}\n"
                
                full_prompt += "\n"
            else:
                # 如果无法读取详细信息，使用基础信息
                full_prompt += f"「{user_name}」今日抽取的观音灵签信息：\n"
                full_prompt += f"签序：{lingqian_data.get('qianxu_chinese', qianxu)}\n"
                full_prompt += f"签名：{lingqian_data.get('qianming', '')}\n"
                full_prompt += f"吉凶：{lingqian_data.get('jixiong', '')}\n"
                full_prompt += f"宫位：{lingqian_data.get('gongwei', '')}\n"
                if '内容' in lingqian_data:
                    full_prompt += f"灵签内容：\n{lingqian_data['内容']}\n\n"
            
            # 添加结尾指导
            full_prompt += f"请为「{user_name}」详细解读这支灵签的深层含义，包括古文翻译、寓意解析、人生指导等。在回答中请称呼用户为「{user_name}」。"
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"构建详细签文拆解提示词失败: {e}")
            # 降级处理
            fallback_prompt = f"请对以下灵签进行详细的翻译和拆解：\n"
            if lingqian_data:
                fallback_prompt += f"灵签信息：{lingqian_data}\n"
                fallback_prompt += f"请包括签文含义、诗句解读、人生指导等内容。"
            return fallback_prompt
    
    async def _build_detailed_jieqian_prompt(self, persona_prompt: str, jieqian_prompt: str, 
                                           lingqian_data: dict, content: str, event: AstrMessageEvent) -> str:
        """构建详细的解签提示词 - 参考GitHub完美方案"""
        try:
            # 获取用户信息
            from .core_lq_userinfo import UserInfoManager
            user_info = await UserInfoManager.get_user_info(event)
            user_name = user_info.get('card', user_info.get('nickname', '用户'))
            
            # 读取具体的灵签内容
            qianxu = lingqian_data.get('qianxu', 0)
            detailed_lingqian = await self._load_lingqian_json(qianxu)
            
            # 构建完整的prompt
            full_prompt = ""
            
            # 添加人格设定
            if persona_prompt:
                full_prompt += f"{persona_prompt}\n\n"
            
            # 添加解签提示词，并插入用户名称
            formatted_jieqian_prompt = jieqian_prompt.replace("{user_id}", user_name)
            full_prompt += f"{formatted_jieqian_prompt}\n\n"
            
            # 添加具体的灵签信息
            if detailed_lingqian:
                full_prompt += f"今日抽取的观音灵签信息：\n"
                full_prompt += f"签序：{detailed_lingqian.get('签序', qianxu)}\n"
                full_prompt += f"签名：{detailed_lingqian.get('签名', '')}\n"
                full_prompt += f"吉凶：{detailed_lingqian.get('吉凶', '')}\n"
                full_prompt += f"宫位：{detailed_lingqian.get('宫位', '')}\n"
                
                # 添加详细内容
                if '内容' in detailed_lingqian:
                    full_prompt += f"灵签内容：\n{detailed_lingqian['内容']}\n\n"
                
                # 添加诗句等其他信息
                for key in ['诗曰', '解曰', '圣意', '东坡解']:
                    if key in detailed_lingqian:
                        full_prompt += f"{key}：{detailed_lingqian[key]}\n"
            else:
                # 如果无法读取详细信息，使用基础信息
                full_prompt += f"今日抽取的观音灵签信息：\n"
                full_prompt += f"签序：{lingqian_data.get('qianxu_chinese', qianxu)}\n"
                full_prompt += f"签名：{lingqian_data.get('qianming', '')}\n"
                full_prompt += f"吉凶：{lingqian_data.get('jixiong', '')}\n"
                full_prompt += f"宫位：{lingqian_data.get('gongwei', '')}\n"
                if '内容' in lingqian_data:
                    full_prompt += f"灵签内容：\n{lingqian_data['内容']}\n\n"
            
            # 添加用户问题
            full_prompt += f"用户「{user_name}」的问题：{content}\n\n"
            full_prompt += f"请根据上述灵签信息，结合用户「{user_name}」的问题，提供智慧的解签和人生指导。在回答中请称呼用户为「{user_name}」。"
            
            return full_prompt
            
        except Exception as e:
            logger.error(f"构建详细解签提示词失败: {e}")
            # 降级处理
            fallback_prompt = f"请根据以下信息为用户提供解签指导：\n"
            fallback_prompt += f"用户问题：{content}\n"
            if lingqian_data:
                fallback_prompt += f"灵签信息：{lingqian_data}\n"
            return fallback_prompt
    
    async def _load_lingqian_json(self, qianxu: int) -> dict:
        """加载指定签序的灵签JSON文件"""
        try:
            if not qianxu or qianxu < 1 or qianxu > 100:
                logger.warning(f"[LLMManager] 无效的签序: {qianxu}")
                return {}
            
            # 构建JSON文件路径
            plugin_dir = os.path.dirname(os.path.dirname(__file__))  # 回到插件根目录
            json_path = os.path.join(plugin_dir, "guanyin_lingqian", f"{qianxu}.json")
            
            if not os.path.exists(json_path):
                logger.warning(f"[LLMManager] 灵签JSON文件不存在: {json_path}")
                return {}
            
            with open(json_path, 'r', encoding='utf-8') as f:
                lingqian_json = json.load(f)
                logger.debug(f"[LLMManager] 成功加载灵签JSON: {qianxu}")
                return lingqian_json
                
        except Exception as e:
            logger.error(f"[LLMManager] 加载灵签JSON文件失败: {e}")
            return {}
    
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
                # 处理字典和对象两种格式
                if isinstance(persona, dict):
                    if persona.get('name') == persona_name:
                        logger.info(f"获取人格成功, {persona.get('prompt', '')[:10]}...")
                        return persona.get('prompt', '')
                else:
                    if hasattr(persona, 'name') and persona.name == persona_name:
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
