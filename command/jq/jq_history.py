"""
解签历史记录指令处理模块
处理解签历史记录查询功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq_userinfo import UserInfoManager

class JieqianHistoryHandler:
    """解签历史记录处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.group_manager = plugin_instance.group_manager if hasattr(plugin_instance, 'group_manager') else None
    
    async def handle_history(self, event: AstrMessageEvent):
        """处理历史记录查询"""
        try:
            # 获取用户信息
            at_user_id = UserInfoManager.extract_at_user_id(event)
            target_user_id = at_user_id or event.get_sender_id()
            user_info = await UserInfoManager.get_user_info(event, target_user_id)
            
            # 获取历史记录数量限制
            display_count = int(self.plugin.config.get('jqhi_display_count', '10'))
            
            # 加载解签历史数据
            from ...core.core_lq_group import GroupManager
            group_manager = GroupManager()
            jieqian_data = group_manager.load_jieqian_history()
            
            if target_user_id not in jieqian_data:
                yield event.plain_result(f"「{user_info['card']}」还没有解签历史记录。")
                return
            
            # 获取用户历史记录并排序
            user_history = jieqian_data[target_user_id]
            sorted_dates = sorted(user_history.keys(), reverse=True)[:display_count]
            
            if not sorted_dates:
                yield event.plain_result(f"「{user_info['card']}」还没有解签历史记录。")
                return
            
            # 构建历史内容
            history_content_template = self.plugin.config.get('jieqian_config', {}).get('history_content',
                '{date} 解签数{jieqian_count}\n---')
            
            history_content_list = []
            total_count = 0
            max_count = 0
            min_count = float('inf')
            
            for date in sorted_dates:
                count = len(user_history[date])
                total_count += count
                max_count = max(max_count, count)
                min_count = min(min_count, count)
                
                variables = {
                    'date': date,
                    'jieqian_count': count
                }
                content = self.plugin._format_template(history_content_template, variables)
                history_content_list.append(content)
            
            history_content = '\n'.join(history_content_list)
            avg_count = round(total_count / len(sorted_dates), 1) if sorted_dates else 0
            if min_count == float('inf'):
                min_count = 0
            
            # 构建完整的历史模板
            variables = {
                'card': user_info['card'],
                'jqhi_display': len(sorted_dates),
                'jqhi_total': len(user_history),
                'jqhi_max': max_count,
                'jqhi_avg': avg_count,
                'jqhi_min': min_count,
                'jieqian_history_content': history_content
            }
            
            template = self.plugin.config.get('jieqian_config', {}).get('history_template',
                '📚 {card} 的解签历史记录\n[显示 {jqhi_display}/{jqhi_total}]\n{jieqian_history_content}\n\n📊 统计信息:\n解签总数: {jqhi_total}\n最大日解签数: {jqhi_max}\n平均日解签数: {jqhi_avg}\n最小日解签数: {jqhi_min}')
            
            message = self.plugin._format_template(template, variables)
            yield event.plain_result(message)
            
        except Exception as e:
            logger.error(f"处理解签历史记录失败: {e}")
            yield event.plain_result("查询历史记录时发生错误，请稍后重试。")
