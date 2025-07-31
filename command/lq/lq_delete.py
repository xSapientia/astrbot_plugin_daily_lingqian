"""
灵签数据删除指令处理模块
处理删除历史记录功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

class LingqianDeleteHandler:
    """灵签删除处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.lingqian_manager = plugin_instance.lingqian_manager
    
    async def handle_delete(self, event: AstrMessageEvent, confirm: bool = False):
        """处理删除除今日外的历史记录"""
        try:
            if not confirm:
                yield event.plain_result("⚠️ 删除历史记录需要确认参数，请使用: lq delete --confirm")
                return
            
            user_id = event.get_sender_id()
            
            # 执行删除操作
            success = self.lingqian_manager.delete_user_history_except_today(user_id)
            
            if success:
                yield event.plain_result("✅ 已删除您除今日外的所有灵签历史记录。")
                logger.info(f"用户 {user_id} 删除了除今日外的灵签历史记录")
            else:
                yield event.plain_result("❌ 删除历史记录失败，请稍后重试。")
                
        except Exception as e:
            logger.error(f"处理灵签删除指令失败: {e}")
            yield event.plain_result("删除历史记录时发生错误，请稍后重试。")
