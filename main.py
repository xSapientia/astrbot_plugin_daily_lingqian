"""
AstrBot 每日灵签插件
支持观音100灵签的抽取、查询、解签等功能
"""

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp
import json
import os
import asyncio

# 导入核心模块
from .core.variable import get_date, get_today, NUMBER_TO_CHINESE, get_jieqian_statistics
from .core.core_lq import DailyLingqianManager
from .core.core_lq_llm import LLMManager
from .core.core_lq_userinfo import UserInfoManager
from .core.core_lq_group import GroupManager
from .permission.permission import PermissionManager
from .permission.whitelist import WhitelistManager

# 导入指令处理模块
from .command.lq.lq import LingqianHandler
from .command.lq.lq_help import LingqianHelpHandler
from .command.lq.lq_rank import LingqianRankHandler
from .command.lq.lq_history import LingqianHistoryHandler
from .command.lq.lq_delete import LingqianDeleteHandler
from .command.lq.lq_initialize import LingqianInitializeHandler
from .command.lq.lq_reset import LingqianResetHandler

from .command.jq.jq import JieqianHandler
from .command.jq.jq_help import JieqianHelpHandler
from .command.jq.jq_rank import JieqianRankHandler
from .command.jq.jq_history import JieqianHistoryHandler
from .command.jq.jq_delete import JieqianDeleteHandler
from .command.jq.jq_initialize import JieqianInitializeHandler
from .command.jq.jq_reset import JieqianResetHandler

from .command.handler import CommandHandler

@register(
    "astrbot_plugin_daily_lingqian",
    "xSapientia", 
    "一个模拟每日抽取观音灵签的插件",
    "0.0.1", 
    "https://github.com/xSapientia/astrbot_plugin_daily_lingqian",
)
class DailyLingqianPlugin(Star):
    """每日灵签插件主类"""
    
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        # 动态更新图片版本选项
        self._update_pics_version_options()
        
        # 初始化管理器
        self.lingqian_manager = DailyLingqianManager()
        self.llm_manager = LLMManager(context, config)
        self.whitelist_manager = WhitelistManager(config)
        self.group_manager = GroupManager()
        
        # 初始化指令处理器
        self.lq_handler = LingqianHandler(self)
        self.lq_help_handler = LingqianHelpHandler(self)
        self.lq_rank_handler = LingqianRankHandler(self)
        self.lq_history_handler = LingqianHistoryHandler(self)
        self.lq_delete_handler = LingqianDeleteHandler(self)
        self.lq_initialize_handler = LingqianInitializeHandler(self)
        self.lq_reset_handler = LingqianResetHandler(self)
        
        self.jq_handler = JieqianHandler(self)
        self.jq_help_handler = JieqianHelpHandler(self)
        self.jq_rank_handler = JieqianRankHandler(self)
        self.jq_history_handler = JieqianHistoryHandler(self)
        self.jq_delete_handler = JieqianDeleteHandler(self)
        self.jq_initialize_handler = JieqianInitializeHandler(self)
        self.jq_reset_handler = JieqianResetHandler(self)
        
        # 初始化统一指令处理器
        self.command_handler = CommandHandler(self)
        
        logger.info("每日灵签插件初始化完成")
    
    async def initialize(self):
        """异步初始化方法"""
        pass
    
    def _update_pics_version_options(self):
        """动态更新图片版本选项"""
        try:
            resource_path = os.path.join(os.path.dirname(__file__), ".resource")
            if not os.path.exists(resource_path):
                logger.warning("资源目录不存在，创建默认目录")
                os.makedirs(resource_path, exist_ok=True)
                return
            
            # 读取resource目录下的所有文件夹
            folders = []
            for item in os.listdir(resource_path):
                item_path = os.path.join(resource_path, item)
                if os.path.isdir(item_path):
                    folders.append(item)
            
            if not folders:
                folders = ["100_default"]  # 默认选项
                logger.warning("资源目录为空，使用默认选项")
            
            # 读取现有的配置模式
            schema_path = os.path.join(os.path.dirname(__file__), "_conf_schema.json")
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                # 更新选项
                if "lq_pics_version" in schema:
                    schema["lq_pics_version"]["options"] = sorted(folders)
                    
                    # 写回文件
                    with open(schema_path, 'w', encoding='utf-8') as f:
                        json.dump(schema, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"已更新图片版本选项: {folders}")
                else:
                    logger.warning("配置模式中未找到 lq_pics_version 选项")
            else:
                logger.warning("配置模式文件不存在")
                
        except Exception as e:
            logger.error(f"更新图片版本选项失败: {e}")
    
    def _check_whitelist(self, event: AstrMessageEvent) -> bool:
        """检查白名单权限"""
        return self.whitelist_manager.is_group_allowed(event)
    
    def _get_fortune_adjustment(self, user_id: str) -> dict:
        """获取人品值调整参数"""
        try:
            if not self.config.get('lingqian_daily_fortune_support', False):
                return None
            
            if not self.config.get('lingqian_ratefix', False):
                return None
            
            # 读取人品数据
            fortune_data = self._load_fortune_data()
            if not fortune_data or user_id not in fortune_data:
                return None
            
            today = get_today()
            if today not in fortune_data[user_id]:
                return None
            
            user_fortune = fortune_data[user_id][today]
            jrrp = user_fortune.get('jrrp', 0)
            
            # 读取ranges配置
            ranges_jrrp, ranges_fortune = self._load_fortune_ranges()
            if not ranges_jrrp:
                return None
            
            # 确定用户属于哪个range
            range_index = self._get_jrrp_range_index(jrrp, ranges_jrrp)
            if range_index == -1:
                return None
            
            # 获取调整参数
            shang_rates = self._parse_rate_string(self.config.get('lingqian_shang_rate', ''))
            zhong_rates = self._parse_rate_string(self.config.get('lingqian_zhong_rate', ''))
            
            if range_index < len(shang_rates) and range_index < len(zhong_rates):
                return {
                    'shang_rate': shang_rates[range_index],
                    'zhong_rate': zhong_rates[range_index]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取人品调整参数失败: {e}")
            return None
    
    def _load_fortune_data(self) -> dict:
        """加载人品数据"""
        try:
            fortune_path = "data/plugin_data/astrbot_plugin_daily_fortune/fortune_history.json"
            if os.path.exists(fortune_path):
                with open(fortune_path, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"无法读取fortune_history.json内容: {e}")
            return {}
    
    def _load_fortune_ranges(self) -> tuple:
        """加载人品范围配置"""
        try:
            config_path = "data/config/astrbot_plugin_daily_fortune_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8-sig') as f:
                    fortune_config = json.load(f)
                    ranges_jrrp = fortune_config.get('ranges_jrrp', '')
                    ranges_fortune = fortune_config.get('ranges_fortune', '')
                    return ranges_jrrp, ranges_fortune
            return None, None
        except Exception as e:
            logger.error(f"无法读取ranges_jrrp内容: {e}")
            return None, None
    
    def _get_jrrp_range_index(self, jrrp: int, ranges_jrrp: str) -> int:
        """获取jrrp所属的范围索引"""
        try:
            ranges = [r.strip() for r in ranges_jrrp.split(',')]
            for i, range_str in enumerate(ranges):
                if '-' in range_str:
                    start, end = map(int, range_str.split('-'))
                    if start <= jrrp <= end:
                        return i
                else:
                    if jrrp == int(range_str):
                        return i
            return -1
        except Exception as e:
            logger.error(f"解析jrrp范围失败: {e}")
            return -1
    
    def _parse_rate_string(self, rate_str: str) -> list:
        """解析概率调整字符串"""
        try:
            if not rate_str:
                return []
            rates = []
            for rate in rate_str.split(','):
                rates.append(float(rate.strip()))
            return rates
        except Exception as e:
            logger.error(f"解析概率字符串失败: {e}")
            return []
    
    def _check_jrrp_required(self, user_id: str) -> bool:
        """检查是否满足人品前置条件"""
        try:
            if not self.config.get('lingqian_daily_fortune_support', False):
                return True  # 未启用support，无需检查
            
            if not self.config.get('lingqian_jrrp_required', False):
                return True  # 未启用required，无需检查
                
            # 检查是否有今日人品数据
            fortune_data = self._load_fortune_data()
            if not fortune_data or user_id not in fortune_data:
                return False
            
            today = get_today()
            return today in fortune_data[user_id]
            
        except Exception as e:
            logger.error(f"检查人品前置条件失败: {e}")
            return True  # 出错时默认允许
    
    def _format_template(self, template: str, variables: dict) -> str:
        """格式化模板字符串"""
        try:
            return template.format(**variables)
        except Exception as e:
            logger.debug(f"模板格式化失败: {e}")
            return template
    
    def _build_variables(self, event: AstrMessageEvent, user_info: dict = None, lingqian_data: dict = None, **kwargs) -> dict:
        """构建模板变量字典"""
        # 获取全局解签统计信息
        global_stats = get_jieqian_statistics()
        
        variables = {
            'date': get_date(),
            'today': get_today(),
            'user_id': user_info.get('user_id', '') if user_info else event.get_sender_id(),
            'nickname': user_info.get('nickname', '') if user_info else event.get_sender_name(),
            'card': user_info.get('card', '') if user_info else event.get_sender_name(),
            'title': user_info.get('title', '') if user_info else '',
            # 添加全局解签统计变量
            'jqhi_total': global_stats['jqhi_total'],           # 历史解签总数
            'jqhi_total_today': global_stats['jqhi_total_today'], # 今日解签总数
        }
        
        if lingqian_data:
            variables.update({
                'qianxu': lingqian_data.get('qianxu_chinese', ''),
                'qianming': lingqian_data.get('qianming', ''),
                'jixiong': lingqian_data.get('jixiong', ''),
                'gongwei': lingqian_data.get('gongwei', ''),
            })
            
            # 添加图片路径 - 构建格式：./.resource/{lq_pics_version}/{qianxu}.png
            pics_version = self.config.get('lq_pics_version', '100_default')
            if lingqian_data.get('qianxu'):
                plugin_dir = os.path.dirname(__file__)
                image_path = os.path.join(plugin_dir, ".resource", pics_version, f"{lingqian_data['qianxu']}.png")
                # 确保路径存在，如果不存在则使用占位符
                if os.path.exists(image_path):
                    variables['lqpic'] = image_path
                else:
                    logger.warning(f"灵签图片不存在: {image_path}")
                    variables['lqpic'] = f"[图片不存在: {pics_version}/{lingqian_data['qianxu']}.png]"
            else:
                variables['lqpic'] = ""
        
        # 添加其他变量
        variables.update(kwargs)
        
        return variables

    # ==================== 灵签指令 ====================
    
    @filter.command("lq", alias={"lingqian", "抽灵签", "灵签"})
    async def lq_command(self, event: AstrMessageEvent, subcommand: str = ""):
        """灵签指令统一入口"""
        async for result in self.command_handler.handle_lq(event, subcommand):
            yield result
        event.stop_event()

    @filter.command("lqrank", alias={"lingqianrank"})
    async def lq_rank(self, event: AstrMessageEvent):
        """查看群内今日灵签排行榜"""
        async for result in self.command_handler.handle_lq(event, "rank"):
            yield result
        event.stop_event()

    @filter.command("lqhistory", alias={"lqhi", "lingqianhistory", "lingqianhi"})
    async def lq_history(self, event: AstrMessageEvent):
        """查看灵签历史记录"""
        async for result in self.command_handler.handle_lq(event, "history"):
            yield result
        event.stop_event()

    @filter.command("lqdelete", alias={"lqdel", "lingqiandelete", "lingqiandel"})
    async def lq_delete(self, event: AstrMessageEvent, confirm: str = ""):
        """删除灵签历史记录"""
        async for result in self.command_handler.handle_lq(event, "delete"):
            yield result
        event.stop_event()

    @filter.command("lqinitialize", alias={"lqinit", "lingqianinitialize", "lingqianinit"})
    async def lq_initialize(self, event: AstrMessageEvent, confirm: str = ""):
        """初始化灵签今日记录"""
        async for result in self.command_handler.handle_lq(event, "initialize"):
            yield result
        event.stop_event()

    @filter.command("lqreset", alias={"lqre", "lingqianreset", "lingqianre"})
    async def lq_reset(self, event: AstrMessageEvent, confirm: str = ""):
        """重置所有灵签数据"""
        async for result in self.command_handler.handle_lq(event, "reset"):
            yield result
        event.stop_event()

    # ==================== 解签指令 ====================

    @filter.command("jq", alias={"jieqian", "解签"})
    async def jq_command(self, event: AstrMessageEvent, subcommand: str = "", content: str = ""):
        """解签指令统一入口"""
        async for result in self.command_handler.handle_jq(event, subcommand, content):
            yield result
        event.stop_event()

    @filter.command("jqrank", alias={"jieqianrank"})
    async def jq_rank(self, event: AstrMessageEvent):
        """查看群内今日解签排行榜"""
        async for result in self.command_handler.handle_jq(event, "rank"):
            yield result
        event.stop_event()

    @filter.command("jqlist", alias={"jieqianlist"})
    async def jq_list(self, event: AstrMessageEvent, param: str = ""):
        """查看解签列表"""
        async for result in self.command_handler.handle_jq(event, "list", param):
            yield result
        event.stop_event()

    @filter.command("jqhistory", alias={"jqhi", "jieqianhistory", "jieqianhi"})
    async def jq_history(self, event: AstrMessageEvent):
        """查看解签历史记录"""
        async for result in self.command_handler.handle_jq(event, "history"):
            yield result
        event.stop_event()

    @filter.command("jqdelete", alias={"jqdel", "jieqiandelete", "jieqiandel"})
    async def jq_delete(self, event: AstrMessageEvent, param: str = ""):
        """删除解签历史记录"""
        async for result in self.command_handler.handle_jq(event, "delete", param):
            yield result
        event.stop_event()

    @filter.command("jqinitialize", alias={"jqinit", "jieqianinitialize", "jieqianinit"})
    async def jq_initialize(self, event: AstrMessageEvent, confirm: str = ""):
        """初始化解签今日记录"""
        async for result in self.command_handler.handle_jq(event, "initialize"):
            yield result
        event.stop_event()

    @filter.command("jqreset", alias={"jqre", "jieqianreset", "jieqianre"})
    async def jq_reset(self, event: AstrMessageEvent, confirm: str = ""):
        """重置所有解签数据"""
        async for result in self.command_handler.handle_jq(event, "reset"):
            yield result
        event.stop_event()

    async def terminate(self):
        """插件卸载时保存缓存"""
        try:
            # 检查是否需要删除数据
            if self.config.get('uninstall_delete_data', False):
                # 删除插件数据目录
                import shutil
                plugin_data_path = "data/plugin_data/astrbot_plugin_daily_lingqian"
                if os.path.exists(plugin_data_path):
                    shutil.rmtree(plugin_data_path)
                    logger.info("已删除插件数据")
            
            # 检查是否需要删除配置文件
            if self.config.get('uninstall_delete_config', False):
                config_path = "data/config/astrbot_plugin_daily_lingqian_config.json"
                if os.path.exists(config_path):
                    os.remove(config_path)
                    logger.info("已删除插件配置文件")
            
            logger.info("astrbot_plugin_daily_lingqian 插件已卸载")
            
        except Exception as e:
            logger.error(f"插件卸载时发生错误: {e}")