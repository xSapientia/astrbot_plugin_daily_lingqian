"""
灵签主指令处理模块
处理灵签的抽取和查询功能
"""

import os
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq import DailyLingqianManager
from ...core.core_lq_userinfo import UserInfoManager

class LingqianHandler:
    """灵签处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.lingqian_manager = plugin_instance.lingqian_manager
    
    async def handle_draw_or_query(self, event: AstrMessageEvent):
        """处理抽取或查询灵签"""
        try:
            # 获取用户信息
            at_user_id = UserInfoManager.extract_at_user_id(event)
            target_user_id = at_user_id or event.get_sender_id()
            user_info = UserInfoManager.get_user_info(event, target_user_id)
            
            # 如果是查询他人，直接查询
            if at_user_id:
                async for result in self._query_lingqian(event, target_user_id, user_info):
                    yield result
                return
            
            # 检查人品前置条件
            if not self.plugin._check_jrrp_required(target_user_id):
                template = self.plugin.config.get('lingqian_jrrptip_template', '「{card}」今日还未检测人品运势')
                variables = self.plugin._build_variables(event, user_info)
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                return
            
            # 检查是否已抽取
            today_lingqian = self.lingqian_manager.get_today_lingqian(target_user_id)
            if today_lingqian:
                # 已抽取，显示查询结果
                async for result in self._query_lingqian(event, target_user_id, user_info, today_lingqian):
                    yield result
            else:
                # 未抽取，进行抽取
                async for result in self._draw_lingqian(event, target_user_id, user_info):
                    yield result
                    
        except Exception as e:
            logger.error(f"处理灵签指令失败: {e}")
            yield event.plain_result("处理灵签时发生错误，请稍后重试。")
    
    async def _draw_lingqian(self, event: AstrMessageEvent, user_id: str, user_info: dict):
        """抽取灵签"""
        try:
            # 获取人品调整参数
            fortune_adjustment = self.plugin._get_fortune_adjustment(user_id)
            
            # 抽取灵签
            lingqian_data = self.lingqian_manager.draw_lingqian(user_id, fortune_adjustment)
            
            # 构建变量
            variables = self.plugin._build_variables(event, user_info, lingqian_data)
            
            # 发送图片
            if lingqian_data.get('qianxu'):
                pics_version = self.plugin.config.get('lq_pics_version', '100_default')
                plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                image_path = os.path.join(plugin_dir, ".resource", pics_version, f"{lingqian_data['qianxu']}.png")
                
                if os.path.exists(image_path):
                    yield event.image_result(image_path)
                else:
                    logger.warning(f"灵签图片不存在: {image_path}")
            
            # 发送文字模板（如果配置了的话）
            template = self.plugin.config.get('lingqian_config', {}).get('draw_template', '-----「{card}」今日灵签-----')
            # 如果模板中包含{lqpic}，则移除它（因为图片已经单独发送了）
            if '{lqpic}' in template:
                template = template.replace('{lqpic}', '').strip()
            
            if template:  # 只有在有文字内容时才发送
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                
        except Exception as e:
            logger.error(f"抽取灵签失败: {e}")
            yield event.plain_result("抽取灵签时发生错误，请稍后重试。")
    
    async def _query_lingqian(self, event: AstrMessageEvent, user_id: str, user_info: dict, lingqian_data: dict = None):
        """查询灵签"""
        try:
            if not lingqian_data:
                lingqian_data = self.lingqian_manager.get_today_lingqian(user_id)
            
            if not lingqian_data:
                # 未抽取灵签
                template = self.plugin.config.get('lingqian_config', {}).get('drawtip_template', '「{card}」今日还未抽取灵签')
                variables = self.plugin._build_variables(event, user_info)
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                return
            
            # 构建变量
            variables = self.plugin._build_variables(event, user_info, lingqian_data)
            
            # 发送图片
            if lingqian_data.get('qianxu'):
                pics_version = self.plugin.config.get('lq_pics_version', '100_default')
                plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                image_path = os.path.join(plugin_dir, ".resource", pics_version, f"{lingqian_data['qianxu']}.png")
                
                if os.path.exists(image_path):
                    yield event.image_result(image_path)
                else:
                    logger.warning(f"灵签图片不存在: {image_path}")
            
            # 发送文字模板（如果配置了的话）
            template = self.plugin.config.get('lingqian_config', {}).get('query_template', '-----「{card}」今日灵签-----')
            # 如果模板中包含{lqpic}，则移除它（因为图片已经单独发送了）
            if '{lqpic}' in template:
                template = template.replace('{lqpic}', '').strip()
            
            if template:  # 只有在有文字内容时才发送
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                
        except Exception as e:
            logger.error(f"查询灵签失败: {e}")
            yield event.plain_result("查询灵签时发生错误，请稍后重试。")
