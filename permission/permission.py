"""
权限管理模块
处理插件的权限控制，包括管理员权限验证
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def is_admin(event: AstrMessageEvent) -> bool:
        """检查用户是否为管理员"""
        try:
            return event.is_admin()
        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return False
    
    @staticmethod
    def check_admin_permission(event: AstrMessageEvent) -> bool:
        """检查管理员权限，并记录日志"""
        is_admin = PermissionManager.is_admin(event)
        if not is_admin:
            logger.warning(f"用户 {event.get_sender_id()} 尝试执行管理员指令但权限不足")
        return is_admin
    
    @staticmethod
    def require_admin(func):
        """装饰器：要求管理员权限"""
        async def wrapper(self, event: AstrMessageEvent, *args, **kwargs):
            if not PermissionManager.check_admin_permission(event):
                yield event.plain_result("❌ 此指令仅限管理员使用")
            else:
                async for result in func(self, event, *args, **kwargs):
                    yield result
        return wrapper
