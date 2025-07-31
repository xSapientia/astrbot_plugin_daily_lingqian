"""
解签排行榜指令处理模块
处理解签排行榜查询功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq_group import GroupManager
from ...core.variable import get_date

class JieqianRankHandler:
    """解签排行榜处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.group_manager = GroupManager()
    
    async def handle_rank(self, event: AstrMessageEvent):
        """处理解签排行榜查询"""
        try:
            # 只在群聊中使用
            if not event.get_group_id():
                yield event.plain_result("❌ 排行榜功能仅在群聊中可用。")
                return
            
            # 获取群内成员的解签数据
            group_members = self.group_manager.get_group_members(event)
            if not group_members:
                yield event.plain_result("❌ 无法获取群成员信息。")
                return
            
            # 加载解签历史数据
            jieqian_data = self.group_manager.load_jieqian_history()
            today = get_date()
            
            # 收集今日有解签记录的群成员
            rank_data = []
            for member in group_members:
                user_id = str(member.get('user_id', ''))
                if user_id in jieqian_data and today in jieqian_data[user_id]:
                    count = len(jieqian_data[user_id][today])
                    if count > 0:
                        rank_data.append({
                            'user_id': user_id,
                            'card': member.get('card', user_id),
                            'count': count
                        })
            
            if not rank_data:
                yield event.plain_result("📊 今日群内还没有人解签哦～")
                return
            
            # 按解签数量排序
            rank_data.sort(key=lambda x: x['count'], reverse=True)
            
            # 构建排行内容
            rank_content_template = self.plugin.config.get('jieqian_config', {}).get('ranks_content',
                '{card} 今日解签{jieqian_count}\n---')
            
            rank_content_list = []
            for i, item in enumerate(rank_data[:10], 1):  # 只显示前10名
                variables = {
                    'card': item['card'],
                    'jieqian_count': item['count']
                }
                content = f"{i}. " + self.plugin._format_template(rank_content_template, variables)
                rank_content_list.append(content)
            
            rank_content = '\n'.join(rank_content_list)
            
            # 构建完整的排行模板
            variables = {
                'date': get_date(),
                'jieqian_ranks': rank_content
            }
            
            template = self.plugin.config.get('jieqian_config', {}).get('ranks_template',
                '📊【本群今日解签榜】{date}\n━━━━━━━━━━━━━━━\n{jieqian_ranks}')
            
            message = self.plugin._format_template(template, variables)
            yield event.plain_result(message)
            
        except Exception as e:
            logger.error(f"处理解签排行榜失败: {e}")
            yield event.plain_result("查询排行榜时发生错误，请稍后重试。")
