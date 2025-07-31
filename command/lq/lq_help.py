"""
灵签帮助指令处理模块
显示灵签功能的帮助信息
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

class LingqianHelpHandler:
    """灵签帮助处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
    
    async def handle_help(self, event: AstrMessageEvent):
        """处理帮助指令"""
        try:
            help_text = """
🎲 观音灵签 - 使用帮助

🌟 基础指令：
• lq / lingqian / 抽灵签 / 灵签
  - 抽取或查询今日灵签
• lq @某人 / lingqian @某人
  - 查询他人的今日灵签

📊 排行榜：
• lq rank / lqrank
• lingqian rank / lingqianrank
  - 查看群内今日灵签排行榜

📚 历史记录：
• lq history / lq hi / lqhistory / lqhi
• lingqian history / lingqian hi / lingqianhistory / lingqianhi
  - 查看自己的历史记录
• lq history @某人 / lq hi @某人
• lqhistory @某人 / lqhi @某人
• lingqian history @某人 / lingqian hi @某人
• lingqianhistory @某人 / lingqianhi @某人
  - 查看他人的历史记录

🗑️ 数据管理：
• lq delete --confirm / lq del --confirm
• lqdelete --confirm / lqdel --confirm
• lingqian delete --confirm / lingqian del --confirm
• lingqiandelete --confirm / lingqiandel --confirm
  - 删除自己除今日外的历史记录

⚙️ 管理员指令：
• lq initialize --confirm / lq init --confirm
• lqinitialize --confirm / lqinit --confirm
• lingqian initialize --confirm / lingqian init --confirm
• lingqianinitialize --confirm / lingqianinit --confirm
  - 初始化自己今日记录
• lq initialize @某人 --confirm / lq init @某人 --confirm
• lqinitialize @某人 --confirm / lqinit @某人 --confirm
• lingqian initialize @某人 --confirm / lingqian init @某人 --confirm
• lingqianinitialize @某人 --confirm / lingqianinit @某人 --confirm
  - 初始化他人今日记录
• lq reset --confirm / lq re --confirm
• lqreset --confirm / lqre --confirm
• lingqian reset --confirm / lingqian re --confirm
• lingqianreset --confirm / lingqianre --confirm
  - 重置所有数据

💡 提示：带 --confirm 的指令需要确认参数才能执行
"""
            yield event.plain_result(help_text)
            
        except Exception as e:
            logger.error(f"处理灵签帮助指令失败: {e}")
            yield event.plain_result("获取帮助信息时发生错误，请稍后重试。")
