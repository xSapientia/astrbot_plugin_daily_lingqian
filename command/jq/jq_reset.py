"""
解签重置指令处理模块
处理重置所有数据功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...permission.permission import PermissionManager

class JieqianResetHandler:
    """解签重置处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.permission_manager = PermissionManager()
    
    async def handle_reset(self, event: AstrMessageEvent, confirm: bool = False):
        """处理重置所有数据"""
        try:
            # 检查管理员权限
            if not self.permission_manager.is_admin(event):
                yield event.plain_result("❌ 重置所有数据需要管理员权限。")
                return
            
            if not confirm:
                yield event.plain_result("⚠️ 重置所有数据需要确认参数，请使用: jq reset --confirm")
                return
            
            # 重置解签数据
            from ...core.core_lq_group import GroupManager
            group_manager = GroupManager()
            
            success1 = group_manager.reset_jieqian_history()
            success2 = group_manager.reset_jieqian_content()
            
            if success1 and success2:
                yield event.plain_result("✅ 已重置所有解签数据。")
                logger.info(f"管理员 {event.get_sender_id()} 重置了所有解签数据")
            else:
                yield event.plain_result("❌ 重置数据失败，请稍后重试。")
                
        except Exception as e:
            logger.error(f"处理解签重置指令失败: {e}")
            yield event.plain_result("重置数据时发生错误，请稍后重试。")
