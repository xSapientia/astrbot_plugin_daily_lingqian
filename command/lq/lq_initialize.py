"""
灵签初始化指令处理模块
处理初始化今日记录功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq_userinfo import UserInfoManager
from ...permission.permission import PermissionManager

class LingqianInitializeHandler:
    """灵签初始化处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.lingqian_manager = plugin_instance.lingqian_manager
        self.permission_manager = PermissionManager()
    
    async def handle_initialize(self, event: AstrMessageEvent, confirm: bool = False):
        """处理初始化今日记录"""
        try:
            if not confirm:
                yield event.plain_result("⚠️ 初始化记录需要确认参数，请使用: lq initialize --confirm")
                return
            
            # 获取目标用户
            at_user_id = UserInfoManager.extract_at_user_id(event)
            
            # 如果是初始化他人记录，需要管理员权限
            if at_user_id:
                if not self.permission_manager.is_admin(event):
                    yield event.plain_result("❌ 初始化他人记录需要管理员权限。")
                    return
                target_user_id = at_user_id
                user_info = await UserInfoManager.get_user_info(event, target_user_id)
                target_name = user_info['card']
            else:
                target_user_id = event.get_sender_id()
                target_name = "您"
            
            # 执行初始化操作
            success = self.lingqian_manager.initialize_user_today(target_user_id)
            
            if success:
                yield event.plain_result(f"✅ 已初始化{target_name}的今日灵签记录。")
                logger.info(f"用户 {event.get_sender_id()} 初始化了用户 {target_user_id} 的今日灵签记录")
            else:
                yield event.plain_result(f"❌ 初始化{target_name}的今日记录失败，请稍后重试。")
                
        except Exception as e:
            logger.error(f"处理灵签初始化指令失败: {e}")
            yield event.plain_result("初始化记录时发生错误，请稍后重试。")
