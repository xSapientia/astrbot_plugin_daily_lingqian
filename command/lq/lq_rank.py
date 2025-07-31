"""
灵签排行榜处理模块
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq_group import GroupManager
from ...core.variable import NUMBER_TO_CHINESE, get_date

class LingqianRankHandler:
    """灵签排行榜处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.lingqian_manager = plugin_instance.lingqian_manager
    
    async def handle_rank(self, event: AstrMessageEvent):
        """处理群内今日灵签排行榜"""
        try:
            if not event.get_group_id():
                yield event.plain_result("此指令仅支持在群聊中使用")
                return
            
            # 加载数据
            history_data = self.lingqian_manager.load_lingqian_history()
            sort_data = self.lingqian_manager._load_sort_data()
            
            # 筛选群内排行数据
            ranking_data = GroupManager.filter_group_ranking_data(event, history_data, sort_data)
            
            if not ranking_data:
                yield event.plain_result("今日群内还没有人抽取灵签")
                return
            
            # 构建排行内容
            ranks_content = ""
            ranks_template = self.plugin.config.get('lingqian_config', {}).get('ranks_content', '{card} 第{qianxu}签{qianming}({jixiong})\n---')
            
            for item in ranking_data:
                variables = {
                    'card': item['card'],
                    'qianxu': NUMBER_TO_CHINESE.get(item['qianxu'], str(item['qianxu'])),
                    'qianming': item['qianming'],
                    'jixiong': item['jixiong']
                }
                ranks_content += self.plugin._format_template(ranks_template, variables) + "\n"
            
            # 构建最终消息
            variables = {
                'date': get_date(),
                'lingqian_ranks': ranks_content.rstrip()
            }
            
            template = self.plugin.config.get('lingqian_config', {}).get('ranks_template', '📊【本群今日灵签榜】{date}\n━━━━━━━━━━━━━━━\n{lingqian_ranks}')
            message = self.plugin._format_template(template, variables)
            
            yield event.plain_result(message)
            
        except Exception as e:
            logger.error(f"获取灵签排行失败: {e}")
            yield event.plain_result("获取排行榜时发生错误，请稍后重试。")
