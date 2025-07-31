"""
解签帮助指令处理模块
显示解签功能的帮助信息
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

class JieqianHelpHandler:
    """解签帮助处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
    
    async def handle_help(self, event: AstrMessageEvent):
        """处理帮助指令"""
        try:
            help_text = """
🔮 观音解签 - 使用帮助

🌟 基础指令：
• jq [内容] / jieqian [内容] / 解签 [内容]
  - 依据内容解读今日灵签
• jq list / jqlist / jieqian list / jieqianlist
  - 查看自己今日所有解签
• jq list @某人 / jqlist @某人
• jieqian list @某人 / jieqianlist @某人
  - 查看他人今日所有解签
• jq list [序号] / jqlist [序号]
• jieqian list [序号] / jieqianlist [序号]
  - 查看指定序号的解签内容

📊 排行榜：
• jq rank / jqrank
• jieqian rank / jieqianrank
  - 查看群内今日解签排行榜

📚 历史记录：
• jq history / jq hi / jqhistory / jqhi
• jieqian history / jieqian hi / jieqianhistory / jieqianhi
  - 查看自己的历史记录
• jq history @某人 / jq hi @某人
• jqhistory @某人 / jqhi @某人
• jieqian history @某人 / jieqian hi @某人
• jieqianhistory @某人 / jieqianhi @某人
  - 查看他人的历史记录

🗑️ 数据管理：
• jq delete --confirm / jq del --confirm
• jqdelete --confirm / jqdel --confirm
• jieqian delete --confirm / jieqian del --confirm
• jieqiandelete --confirm / jieqiandel --confirm
  - 删除自己除今日外的历史记录

⚙️ 管理员指令：
• jq initialize --confirm / jq init --confirm
• jqinitialize --confirm / jqinit --confirm
• jieqian initialize --confirm / jieqian init --confirm
• jieqianinitialize --confirm / jieqianinit --confirm
  - 初始化自己今日记录
• jq initialize @某人 --confirm / jq init @某人 --confirm
• jqinitialize @某人 --confirm / jqinit @某人 --confirm
• jieqian initialize @某人 --confirm / jieqian init @某人 --confirm
• jieqianinitialize @某人 --confirm / jieqianinit @某人 --confirm
  - 初始化他人今日记录
• jq reset --confirm / jq re --confirm
• jqreset --confirm / jqre --confirm
• jieqian reset --confirm / jieqian re --confirm
• jieqianreset --confirm / jieqianre --confirm
  - 重置所有数据

💡 提示：带 --confirm 的指令需要确认参数才能执行
"""
            yield event.plain_result(help_text)
            
        except Exception as e:
            logger.error(f"处理解签帮助指令失败: {e}")
            yield event.plain_result("获取帮助信息时发生错误，请稍后重试。")
