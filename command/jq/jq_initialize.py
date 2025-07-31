"""
解签初始化指令处理模块
处理初始化今日记录功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.core_lq_userinfo import UserInfoManager
from ...permission.permission import PermissionManager
from ...core.variable import get_today

class JieqianInitializeHandler:
    """解签初始化处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.permission_manager = PermissionManager()
    
    async def handle_initialize(self, event: AstrMessageEvent, confirm: bool = False):
        """处理初始化今日记录"""
        try:
            if not confirm:
                yield event.plain_result("⚠️ 初始化记录需要确认参数，请使用: jq initialize --confirm")
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
            
            # 加载解签历史数据
            from ...core.core_lq_group import GroupManager
            group_manager = GroupManager()
            jieqian_data = group_manager.load_jieqian_history()
            jieqian_content = group_manager.load_jieqian_content()
            
            today = get_today()
            
            # 清除今日记录
            if target_user_id in jieqian_data and today in jieqian_data[target_user_id]:
                del jieqian_data[target_user_id][today]
                if not jieqian_data[target_user_id]:
                    del jieqian_data[target_user_id]
            
            if target_user_id in jieqian_content:
                del jieqian_content[target_user_id]
            
            # 保存数据
            success1 = group_manager.save_jieqian_history(jieqian_data)
            success2 = group_manager.save_jieqian_content(jieqian_content)
            
            if success1 and success2:
                yield event.plain_result(f"✅ 已初始化{target_name}的今日解签记录。")
                logger.info(f"用户 {event.get_sender_id()} 初始化了用户 {target_user_id} 的今日解签记录")
            else:
                yield event.plain_result(f"❌ 初始化{target_name}的今日记录失败，请稍后重试。")
                
        except Exception as e:
            logger.error(f"处理解签初始化指令失败: {e}")
            yield event.plain_result("初始化记录时发生错误，请稍后重试。")
