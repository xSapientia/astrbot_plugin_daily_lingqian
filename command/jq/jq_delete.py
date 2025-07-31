"""
解签数据删除指令处理模块
处理删除历史记录功能
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ...core.variable import get_today

class JieqianDeleteHandler:
    """解签删除处理器"""
    
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
    
    async def handle_delete(self, event: AstrMessageEvent, param: str = ""):
        """处理删除解签记录"""
        try:
            user_id = event.get_sender_id()
            
            # 如果有参数且是数字，删除指定序号的今日解签记录
            if param and param.isdigit():
                await self._delete_specific_jieqian(event, user_id, int(param))
                return
            
            # 如果参数是 --confirm，删除除今日外的所有历史记录
            if param == "--confirm":
                await self._delete_history_except_today(event, user_id)
                return
            
            # 默认提示用法
            usage_msg = """解签删除功能用法：
• 删除指定序号的今日解签记录：jq delete [序号]
• 删除除今日外的所有历史记录：jq delete --confirm
• 查看今日解签列表：jq list"""
            yield event.plain_result(usage_msg)
                
        except Exception as e:
            logger.error(f"处理解签删除指令失败: {e}")
            yield event.plain_result("删除解签记录时发生错误，请稍后重试。")
    
    async def _delete_specific_jieqian(self, event: AstrMessageEvent, user_id: str, index: int):
        """删除指定序号的今日解签记录"""
        try:
            # 获取今日解签列表
            today_jieqian_list = self.plugin.llm_manager.get_user_today_jieqian_list(user_id)
            
            if not today_jieqian_list:
                yield event.plain_result("您今日还没有解签记录。")
                return
            
            # 检查序号是否有效
            if index < 1 or index > len(today_jieqian_list):
                yield event.plain_result(f"❌ 序号无效，今日共有 {len(today_jieqian_list)} 条解签记录，请输入 1-{len(today_jieqian_list)} 之间的序号。")
                return
            
            # 加载数据
            from ...core.core_lq_group import GroupManager
            group_manager = GroupManager()
            jieqian_data = group_manager.load_jieqian_history()
            jieqian_content = group_manager.load_jieqian_content()
            
            today = get_today()
            deleted_item = None
            
            # 删除历史记录中的指定项
            if user_id in jieqian_data and today in jieqian_data[user_id]:
                if index <= len(jieqian_data[user_id][today]):
                    deleted_item = jieqian_data[user_id][today].pop(index - 1)
                    
                    # 如果今日记录为空，删除整个日期
                    if not jieqian_data[user_id][today]:
                        del jieqian_data[user_id][today]
                        if not jieqian_data[user_id]:
                            del jieqian_data[user_id]
            
            # 删除内容记录中的对应项
            if user_id in jieqian_content:
                # 找到对应的内容记录并删除
                content_to_remove = None
                for i, item in enumerate(jieqian_content[user_id]):
                    if (item.get('date') == today and 
                        len([x for x in jieqian_content[user_id][:i+1] if x.get('date') == today]) == index):
                        content_to_remove = i
                        break
                
                if content_to_remove is not None:
                    jieqian_content[user_id].pop(content_to_remove)
                    if not jieqian_content[user_id]:
                        del jieqian_content[user_id]
            
            # 保存数据
            success1 = group_manager.save_jieqian_history(jieqian_data)
            success2 = group_manager.save_jieqian_content(jieqian_content)
            
            if success1 and success2:
                if deleted_item:
                    content_preview = deleted_item.get('content', '')[:10] + ('...' if len(deleted_item.get('content', '')) > 10 else '')
                    yield event.plain_result(f"✅ 已删除第 {index} 条解签记录：{content_preview}")
                else:
                    yield event.plain_result(f"✅ 已删除第 {index} 条解签记录")
                logger.info(f"用户 {user_id} 删除了第 {index} 条今日解签记录")
            else:
                yield event.plain_result("❌ 删除解签记录失败，请稍后重试。")
                
        except Exception as e:
            logger.error(f"删除指定解签记录失败: {e}")
            yield event.plain_result("删除解签记录时发生错误，请稍后重试。")
    
    async def _delete_history_except_today(self, event: AstrMessageEvent, user_id: str):
        """删除除今日外的历史记录"""
        try:
            # 加载解签历史数据
            from ...core.core_lq_group import GroupManager
            group_manager = GroupManager()
            jieqian_data = group_manager.load_jieqian_history()
            jieqian_content = group_manager.load_jieqian_content()
            
            if user_id not in jieqian_data:
                yield event.plain_result("您还没有解签历史记录。")
                return
            
            # 保留今日数据，删除其他
            today = get_today()
            user_history = jieqian_data[user_id]
            
            if today in user_history:
                jieqian_data[user_id] = {today: user_history[today]}
            else:
                del jieqian_data[user_id]
            
            # 保留今日内容记录
            if user_id in jieqian_content:
                today_content = [item for item in jieqian_content[user_id] if item.get('date') == today]
                if today_content:
                    jieqian_content[user_id] = today_content
                else:
                    del jieqian_content[user_id]
            
            # 保存数据
            success1 = group_manager.save_jieqian_history(jieqian_data)
            success2 = group_manager.save_jieqian_content(jieqian_content)
            
            if success1 and success2:
                yield event.plain_result("✅ 已删除您除今日外的所有解签历史记录。")
                logger.info(f"用户 {user_id} 删除了除今日外的解签历史记录")
            else:
                yield event.plain_result("❌ 删除历史记录失败，请稍后重试。")
                
        except Exception as e:
            logger.error(f"删除历史记录失败: {e}")
            yield event.plain_result("删除历史记录时发生错误，请稍后重试。")
