"""
解签主指令处理模块
处理解签的核心功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq_userinfo import UserInfoManager
from ...core.core_lq_group import GroupManager
from ...core.variable import get_today

# 存储正在处理的用户
processing_users = set()

class JieqianHandler:
    """解签处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.lingqian_manager = plugin_instance.lingqian_manager
        self.llm_manager = plugin_instance.llm_manager
        self.group_manager = GroupManager()
    
    async def handle_jieqian(self, event: AstrMessageEvent, content: str):
        """处理解签请求"""
        try:
            # 获取用户信息
            user_id = event.get_sender_id()
            user_info = await UserInfoManager.get_user_info(event)
            
            # 检查人品前置条件
            if not self.plugin._check_jrrp_required(user_id):
                template = self.plugin.config.get('lingqian_jrrptip_template', '「{card}」今日还未检测人品运势')
                variables = self.plugin._build_variables(event, user_info)
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                return
            
            # 检查是否有今日灵签
            today_lingqian = self.lingqian_manager.get_today_lingqian(user_id)
            if not today_lingqian:
                template = self.plugin.config.get('lingqian_config', {}).get('drawtip_template', '「{card}」今日还未抽取灵签')
                variables = self.plugin._build_variables(event, user_info)
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                return
            
            # 检查是否正在解签中
            if user_id in processing_users:
                template = self.plugin.config.get('jieqian_config', {}).get('ing_template', '已经在努力为「 {card} 」解签了哦~')
                variables = self.plugin._build_variables(event, user_info)
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                return
            
            # 发送开始解签提示
            begin_template = self.plugin.config.get('jieqian_config', {}).get('begin_template', '命运的丝线汇聚, {card}, 你的困惑即将解开, 正在窥视中...')
            variables = self.plugin._build_variables(event, user_info)
            begin_message = self.plugin._format_template(begin_template, variables)
            yield event.plain_result(begin_message)
            
            # 标记用户为处理中
            processing_users.add(user_id)
            
            try:
                # 调用LLM进行解签
                jieqian_result = await self.llm_manager.process_jieqian(event, user_id, today_lingqian, content)
                
                if jieqian_result is None:
                    # 正在处理中
                    template = self.plugin.config.get('jieqian_config', {}).get('ing_template', '已经在努力为「 {card} 」解签了哦~')
                    variables = self.plugin._build_variables(event, user_info)
                    message = self.plugin._format_template(template, variables)
                    yield event.plain_result(message)
                    return
                
                # 保存解签记录到群组管理器
                self.group_manager.add_jieqian_record(user_id, content, jieqian_result)
                
                # 构建解签结果消息
                variables = self.plugin._build_variables(event, user_info, today_lingqian)
                variables.update({
                    'content': content,
                    'jieqian': jieqian_result
                })
                
                template = self.plugin.config.get('jieqian_config', {}).get('template', 
                    '-----「{card}」解签-----\n第 {qianxu} 签 {qianming}\n吉凶: {jixiong}\n宫位: {gongwei}\n---\n问: {content}\n---\n解:\n{jieqian}')
                message = self.plugin._format_template(template, variables)
                
                yield event.plain_result(message)
                
            finally:
                # 移除处理标记
                processing_users.discard(user_id)
            
        except Exception as e:
            logger.error(f"处理解签失败: {e}")
            processing_users.discard(user_id)
            yield event.plain_result("解签时发生错误，请稍后重试。")
    
    async def handle_list(self, event: AstrMessageEvent, param: str = ""):
        """处理解签列表查询"""
        try:
            # 获取用户信息
            at_user_id = UserInfoManager.extract_at_user_id(event)
            target_user_id = at_user_id or event.get_sender_id()
            user_info = await UserInfoManager.get_user_info(event, target_user_id)
            
            # 检查是否有今日灵签
            today_lingqian = self.lingqian_manager.get_today_lingqian(target_user_id)
            if not today_lingqian:
                template = self.plugin.config.get('lingqian_config', {}).get('drawtip_template', '「{card}」今日还未抽取灵签')
                variables = self.plugin._build_variables(event, user_info)
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                return
            
            # 获取今日解签列表
            jieqian_list = self.llm_manager.get_user_today_jieqian_list(target_user_id)
            
            if not jieqian_list:
                template = self.plugin.config.get('jieqian_config', {}).get('tip_template', '「{card}」今日还未解签')
                variables = self.plugin._build_variables(event, user_info)
                message = self.plugin._format_template(template, variables)
                yield event.plain_result(message)
                return
            
            # 如果指定了序号，显示具体解签内容
            if param.isdigit():
                index = int(param) - 1
                if 0 <= index < len(jieqian_list):
                    item = jieqian_list[index]
                    variables = self.plugin._build_variables(event, user_info, today_lingqian)
                    variables.update({
                        'content': item.get('content', ''),
                        'jieqian': item.get('result', item.get('jieqian', ''))
                    })
                    
                    template = self.plugin.config.get('jieqian_config', {}).get('template', 
                        '-----「{card}」解签-----\n第 {qianxu} 签 {qianming}\n吉凶: {jixiong}\n宫位: {gongwei}\n---\n问: {content}\n---\n解:\n{jieqian}')
                    message = self.plugin._format_template(template, variables)
                    yield event.plain_result(message)
                else:
                    yield event.plain_result(f"❌ 序号超出范围，今日共有 {len(jieqian_list)} 条解签记录。")
                return
            
            # 构建解签列表
            list_items = []
            for i, item in enumerate(jieqian_list, 1):
                content_preview = item['content'][:10] + ('...' if len(item['content']) > 10 else '')
                list_items.append(f"{i}.问: {content_preview}")
            
            variables = self.plugin._build_variables(event, user_info, today_lingqian)
            
            # 构建列表模板（这里简化处理）
            list_content = '\n'.join(list_items)
            message = f"-----「{user_info['card']}」今日解签列表-----\n第 {today_lingqian.get('qianxu_chinese', '')} 签 {today_lingqian.get('qianming', '')}\n吉凶: {today_lingqian.get('jixiong', '')}\n宫位: {today_lingqian.get('gongwei', '')}\n---\n{list_content}"
            
            yield event.plain_result(message)
            
        except Exception as e:
            logger.error(f"处理解签列表失败: {e}")
            yield event.plain_result("查询解签列表时发生错误，请稍后重试。")
