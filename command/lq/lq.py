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
            user_info = await UserInfoManager.get_user_info(event, target_user_id)
            
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
            
            # 发送转发合并消息
            async for result in self._send_forward_message(event, variables, lingqian_data, 'draw'):
                yield result
                
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
            
            # 发送转发合并消息
            async for result in self._send_forward_message(event, variables, lingqian_data, 'query'):
                yield result
                
        except Exception as e:
            logger.error(f"查询灵签失败: {e}")
            yield event.plain_result("查询灵签时发生错误，请稍后重试。")
    
    async def _send_forward_message(self, event: AstrMessageEvent, variables: dict, lingqian_data: dict, message_type: str):
        """发送转发合并消息"""
        try:
            import astrbot.api.message_components as Comp
            from astrbot.api.message_components import Node, Plain, Image
            
            # 获取用户信息
            user_name = variables.get('card', '用户')
            user_id = variables.get('user_id', event.get_sender_id())
            
            # 准备消息内容列表
            message_content = []
            
            # 获取模板
            template_key = 'draw_template' if message_type == 'draw' else 'query_template'
            template = self.plugin.config.get('lingqian_config', {}).get(template_key, '-----「{card}」今日灵签-----\n{lqpic}')
            
            # 处理模板中的文字部分
            if '{lqpic}' in template:
                # 分割模板，获取图片前后的文字
                parts = template.split('{lqpic}')
                text_before = parts[0].strip()
                text_after = parts[1].strip() if len(parts) > 1 else ""
                
                # 添加图片前的文字
                if text_before:
                    formatted_text = self.plugin._format_template(text_before, variables)
                    message_content.append(Plain(formatted_text))
                
                # 添加图片
                if lingqian_data.get('qianxu'):
                    pics_version = self.plugin.config.get('lq_pics_version', '100_default')
                    plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    image_path = os.path.join(plugin_dir, ".resource", pics_version, f"{lingqian_data['qianxu']}.png")
                    
                    if os.path.exists(image_path):
                        message_content.append(Image.fromFileSystem(image_path))
                    else:
                        logger.warning(f"灵签图片不存在: {image_path}")
                        # 如果图片不存在，添加文字说明
                        message_content.append(Plain(f"[图片不存在: {pics_version}/{lingqian_data['qianxu']}.png]"))
                
                # 添加图片后的文字
                if text_after:
                    formatted_text = self.plugin._format_template(text_after, variables)
                    message_content.append(Plain(formatted_text))
            else:
                # 模板中没有{lqpic}，直接添加格式化后的文字
                formatted_text = self.plugin._format_template(template, variables)
                message_content.append(Plain(formatted_text))
                
                # 如果有灵签数据，添加图片
                if lingqian_data.get('qianxu'):
                    pics_version = self.plugin.config.get('lq_pics_version', '100_default')
                    plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    image_path = os.path.join(plugin_dir, ".resource", pics_version, f"{lingqian_data['qianxu']}.png")
                    
                    if os.path.exists(image_path):
                        message_content.append(Image.fromFileSystem(image_path))
                    else:
                        logger.warning(f"灵签图片不存在: {image_path}")
            
            # 如果没有内容，添加默认内容
            if not message_content:
                message_content.append(Plain("灵签信息"))
            
            # 创建转发消息节点
            node = Node(
                uin=int(user_id) if user_id.isdigit() else 12345,  # 用户ID，如果不是数字则使用默认值
                name=user_name,
                content=message_content
            )
            
            # 发送转发消息
            yield event.chain_result([node])
            
        except Exception as e:
            logger.error(f"发送转发合并消息失败: {e}")
            # 发送失败时，回退到普通消息
            try:
                template_key = 'draw_template' if message_type == 'draw' else 'query_template'
                template = self.plugin.config.get('lingqian_config', {}).get(template_key, '-----「{card}」今日灵签-----')
                
                # 移除{lqpic}占位符
                if '{lqpic}' in template:
                    template = template.replace('{lqpic}', '').strip()
                
                if template:
                    message = self.plugin._format_template(template, variables)
                    yield event.plain_result(message)
                
                # 单独发送图片
                if lingqian_data.get('qianxu'):
                    pics_version = self.plugin.config.get('lq_pics_version', '100_default')
                    plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    image_path = os.path.join(plugin_dir, ".resource", pics_version, f"{lingqian_data['qianxu']}.png")
                    
                    if os.path.exists(image_path):
                        yield event.image_result(image_path)
                        
            except Exception as fallback_error:
                logger.error(f"回退到普通消息也失败: {fallback_error}")
                yield event.plain_result("发送灵签信息时发生错误，请稍后重试。")
