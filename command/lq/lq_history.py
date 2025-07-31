"""
灵签历史记录指令处理模块
处理灵签历史记录查询功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq_userinfo import UserInfoManager

class LingqianHistoryHandler:
    """灵签历史记录处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.lingqian_manager = plugin_instance.lingqian_manager
    
    async def handle_history(self, event: AstrMessageEvent):
        """处理历史记录查询"""
        try:
            # 获取用户信息
            at_user_id = UserInfoManager.extract_at_user_id(event)
            target_user_id = at_user_id or event.get_sender_id()
            user_info = await UserInfoManager.get_user_info(event, target_user_id)
            
            # 获取历史记录数量限制
            display_count = int(self.plugin.config.get('lqhi_display_count', '10'))
            
            # 获取用户历史记录
            history_data = self.lingqian_manager.get_user_history(target_user_id, display_count)
            statistics = self.lingqian_manager.get_user_statistics(target_user_id)
            
            if not history_data:
                yield event.plain_result(f"「{user_info['card']}」还没有灵签历史记录。")
                return
            
            # 构建历史内容
            history_content_template = self.plugin.config.get('lingqian_config', {}).get('history_content', 
                '{date} 第{qianxu}签{qianming}({jixiong})\n---')
            
            history_content_list = []
            for item in history_data:
                variables = {
                    'date': item['date'],
                    'qianxu': item.get('qianxu_chinese', ''),
                    'qianming': item.get('qianming', ''),
                    'jixiong': item.get('jixiong', '')
                }
                content = self.plugin._format_template(history_content_template, variables)
                history_content_list.append(content)
            
            history_content = '\n'.join(history_content_list)
            
            # 构建完整的历史模板
            variables = {
                'card': user_info['card'],
                'lqhi_display': len(history_data),
                'lqhi_total': statistics['total'],
                'lqhi_shang_total': statistics['shang_total'],
                'lqhi_zhong_total': statistics['zhong_total'],
                'lqhi_xia_total': statistics['xia_total'],
                'lingqian_history_content': history_content
            }
            
            template = self.plugin.config.get('lingqian_config', {}).get('history_template',
                '📚 {card} 的灵签历史记录\n[显示 {lqhi_display}/{lqhi_total}]\n{lingqian_history_content}\n\n📊 统计信息:\n抽取灵签总数{lqhi_total}\n上签: {lqhi_shang_total}\n中签: {lqhi_zhong_total}\n下签: {lqhi_xia_total}')
            
            message = self.plugin._format_template(template, variables)
            yield event.plain_result(message)
            
        except Exception as e:
            logger.error(f"处理灵签历史记录失败: {e}")
            yield event.plain_result("查询历史记录时发生错误，请稍后重试。")
