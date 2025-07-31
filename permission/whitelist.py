"""
白名单管理模块
处理群聊白名单功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

class WhitelistManager:
    """白名单管理器"""
    
    def __init__(self, config):
        self.config = config
        self.group_whitelist_enabled = config.get('group_whitelist', False)
        self.allowed_groups = config.get('groups', [])
    
    def is_group_allowed(self, event: AstrMessageEvent) -> bool:
        """检查群聊是否在白名单中"""
        try:
            # 如果未启用白名单功能，允许所有群聊
            if not self.group_whitelist_enabled:
                logger.debug("未启用群聊白名单功能")
                return True
            
            # 如果白名单为空，视为未启用该功能
            if not self.allowed_groups:
                logger.warning("已启用群聊白名单功能但白名单为空，视为未启用")
                return True
            
            # 获取群组ID
            group_id = event.get_group_id()
            if not group_id:
                # 私聊消息，允许通过
                return True
            
            # 检查群组是否在白名单中
            is_allowed = group_id in self.allowed_groups
            
            if is_allowed:
                logger.debug(f"群聊 {group_id} 在白名单中")
            else:
                logger.warning(f"群聊 {group_id} 未在白名单中")
            
            return is_allowed
            
        except Exception as e:
            logger.error(f"群聊白名单检查出错: {e}")
            return True  # 出错时默认允许
    
    def update_config(self, config):
        """更新配置"""
        self.config = config
        self.group_whitelist_enabled = config.get('group_whitelist', False)
        self.allowed_groups = config.get('groups', [])
        
        if self.group_whitelist_enabled:
            logger.info("已启用群聊白名单功能")
        else:
            logger.info("未启用群聊白名单功能")
