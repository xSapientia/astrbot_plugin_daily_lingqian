"""
解签数据删除指令处理模块
处理删除历史记录功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.variable import get_today

class JieqianDeleteHandler:
    """解签删除处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
    
    async def handle_delete(self, event: AstrMessageEvent, confirm: bool = False):
        """处理删除除今日外的历史记录"""
        try:
            if not confirm:
                yield event.plain_result("⚠️ 删除历史记录需要确认参数，请使用: jq delete --confirm")
                return
            
            user_id = event.get_sender_id()
            
            # 加载解签历史数据
            from ...core.core_lq_group import GroupManager
            group_manager = GroupManager()
            jieqian_data = group_manager.load_jieqian_history()
            
            if user_id not in jieqian_data:
                yield event.plain_result("您还没有解签历史记录。")
                return
            
            # 保留今日数据，删除其他
            today = get_today()
            user_history = jieqian_data[user_id]
            
            if today in user_history:
                jieqian_data[user_id] = {today: user_history[today]}
            else:
                del jieqian_data[user_id]
            
            # 保存数据
            success = group_manager.save_jieqian_history(jieqian_data)
            
            if success:
                yield event.plain_result("✅ 已删除您除今日外的所有解签历史记录。")
                logger.info(f"用户 {user_id} 删除了除今日外的解签历史记录")
            else:
                yield event.plain_result("❌ 删除历史记录失败，请稍后重试。")
                
        except Exception as e:
            logger.error(f"处理解签删除指令失败: {e}")
            yield event.plain_result("删除历史记录时发生错误，请稍后重试。")
