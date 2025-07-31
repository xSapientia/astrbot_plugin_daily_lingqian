"""
灵签插件指令处理核心模块
"""

from typing import Optional, TYPE_CHECKING
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

if TYPE_CHECKING:
    from ..main import DailyLingqianPlugin


class CommandHandler:
    """指令处理器"""
    
    def __init__(self, plugin: 'DailyLingqianPlugin'):
        """
        初始化指令处理器
        
        Args:
            plugin: 插件实例
        """
        self.plugin = plugin
        self.config = plugin.config
        self.context = plugin.context
        
        # 获取各个处理器
        self.lq_handler = plugin.lq_handler
        self.lq_help_handler = plugin.lq_help_handler
        self.lq_rank_handler = plugin.lq_rank_handler
        self.lq_history_handler = plugin.lq_history_handler
        self.lq_delete_handler = plugin.lq_delete_handler
        self.lq_initialize_handler = plugin.lq_initialize_handler
        self.lq_reset_handler = plugin.lq_reset_handler
        
        self.jq_handler = plugin.jq_handler
        self.jq_help_handler = plugin.jq_help_handler
        self.jq_rank_handler = plugin.jq_rank_handler
        self.jq_history_handler = plugin.jq_history_handler
        self.jq_delete_handler = plugin.jq_delete_handler
        self.jq_initialize_handler = plugin.jq_initialize_handler
        self.jq_reset_handler = plugin.jq_reset_handler
    
    def _has_confirm_param(self, event: AstrMessageEvent) -> bool:
        """检查消息中是否包含 --confirm 参数"""
        return "--confirm" in event.message_str.lower()
    
    async def handle_lq(self, event: AstrMessageEvent, subcommand: str = ""):
        """处理 /lq 指令及其子指令"""
        
        # 检查白名单权限
        if not self.plugin._check_whitelist(event):
            return
        
        # 处理子指令
        if subcommand.lower() == "help":
            # 显示帮助信息
            async for result in self.lq_help_handler.handle_help(event):
                yield result
            return
        elif subcommand.lower() == "rank":
            # 显示排行榜
            async for result in self.lq_rank_handler.handle_rank(event):
                yield result
            return
        elif subcommand.lower() in ["history", "hi"]:
            # 显示历史记录
            async for result in self.lq_history_handler.handle_history(event):
                yield result
            return
        elif subcommand.lower() in ["delete", "del"]:
            # 删除历史记录
            is_confirm = self._has_confirm_param(event)
            async for result in self.lq_delete_handler.handle_delete(event, is_confirm):
                yield result
            return
        elif subcommand.lower() in ["initialize", "init"]:
            # 初始化记录
            is_confirm = self._has_confirm_param(event)
            async for result in self.lq_initialize_handler.handle_initialize(event, is_confirm):
                yield result
            return
        elif subcommand.lower() in ["reset", "re"]:
            # 重置所有数据
            if not event.is_admin():
                yield event.plain_result("❌ 此操作需要管理员权限")
                return
            is_confirm = self._has_confirm_param(event)
            async for result in self.lq_reset_handler.handle_reset(event, is_confirm):
                yield result
            return
        
        # 默认处理：抽取或查询今日灵签
        async for result in self.lq_handler.handle_draw_or_query(event):
            yield result
    
    async def handle_jq(self, event: AstrMessageEvent, subcommand: str = "", content: str = ""):
        """处理 /jq 指令及其子指令"""
        
        # 检查白名单权限
        if not self.plugin._check_whitelist(event):
            return
        
        # 处理子指令
        if subcommand.lower() == "help":
            # 显示帮助信息
            async for result in self.jq_help_handler.handle_help(event):
                yield result
            return
        elif subcommand.lower() == "rank":
            # 显示排行榜
            async for result in self.jq_rank_handler.handle_rank(event):
                yield result
            return
        elif subcommand.lower() == "list":
            # 显示解签列表
            async for result in self.jq_handler.handle_list(event, content):
                yield result
            return
        elif subcommand.lower() in ["history", "hi"]:
            # 显示历史记录
            async for result in self.jq_history_handler.handle_history(event):
                yield result
            return
        elif subcommand.lower() in ["delete", "del"]:
            # 删除历史记录
            # 如果content是数字，传递给删除处理器
            if content and content.isdigit():
                async for result in self.jq_delete_handler.handle_delete(event, content):
                    yield result
            elif self._has_confirm_param(event):
                async for result in self.jq_delete_handler.handle_delete(event, "--confirm"):
                    yield result
            else:
                async for result in self.jq_delete_handler.handle_delete(event, ""):
                    yield result
            return
        elif subcommand.lower() in ["initialize", "init"]:
            # 初始化记录
            is_confirm = self._has_confirm_param(event)
            async for result in self.jq_initialize_handler.handle_initialize(event, is_confirm):
                yield result
            return
        elif subcommand.lower() in ["reset", "re"]:
            # 重置所有数据
            if not event.is_admin():
                yield event.plain_result("❌ 此操作需要管理员权限")
                return
            is_confirm = self._has_confirm_param(event)
            async for result in self.jq_reset_handler.handle_reset(event, is_confirm):
                yield result
            return
        
        # 默认处理：解签功能
        # 如果有子指令但不匹配上述情况，将子指令作为解签内容
        if subcommand:
            content = subcommand + (" " + content if content else "")
        
        if not content:
            yield event.plain_result("❌ 请提供要解签的内容，例如：jq 我想知道工作运势")
            return
        
        async for result in self.jq_handler.handle_jieqian(event, content):
            yield result
