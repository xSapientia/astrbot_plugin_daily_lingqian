"""
群聊功能模块
处理群聊相关功能，包括排行榜中的群成员筛选
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from .core_lq_userinfo import UserInfoManager
from .variable import get_today

class GroupManager:
    """群聊管理器"""
    
    @staticmethod
    async def get_group_members(event: AstrMessageEvent):
        """获取群成员列表"""
        try:
            if not event.get_group_id():
                return []
            
            group = await event.get_group()
            if not group or not hasattr(group, 'members'):
                return []
            
            members = []
            for member in group.members:
                user_id = str(member.user_id)
                nickname = getattr(member, 'nickname', user_id)
                card = getattr(member, 'card', None) or nickname
                title = getattr(member, 'title', '')
                
                members.append({
                    'user_id': user_id,
                    'nickname': nickname,
                    'card': card,
                    'title': title
                })
            
            return members
            
        except Exception as e:
            logger.error(f"获取群成员列表失败: {e}")
            return []
    
    @staticmethod
    async def filter_group_ranking_data(event: AstrMessageEvent, history_data: dict, sort_data: list):
        """
        筛选群聊内的排行数据
        :param event: 消息事件
        :param history_data: 历史数据字典
        :param sort_data: 排序数据列表
        :return: 筛选后的排行数据列表
        """
        try:
            if not event.get_group_id():
                logger.debug("非群聊消息，无法生成群排行")
                return []
            
            # 获取群成员列表
            group_members = await GroupManager.get_group_members(event)
            if not group_members:
                logger.warning("无法获取群成员列表")
                return []
            
            # 获取群成员的用户ID列表
            group_user_ids = {member['user_id'] for member in group_members}
            
            # 获取今日日期
            today = get_today()
            
            # 筛选出今日有数据且在群内的用户
            ranking_data = []
            
            for user_id, user_history in history_data.items():
                # 检查用户是否在群内
                if user_id not in group_user_ids:
                    continue
                
                # 检查用户今日是否有数据
                if today not in user_history:
                    continue
                
                # 获取用户信息
                user_info = None
                for member in group_members:
                    if member['user_id'] == user_id:
                        user_info = member
                        break
                
                if not user_info:
                    continue
                
                # 获取今日数据
                today_data = user_history[today]
                if isinstance(today_data, dict) and 'qianxu' in today_data:
                    qianxu = today_data['qianxu']
                    qianming = today_data.get('qianming', '未知')
                    jixiong = today_data.get('jixiong', '未知')
                elif isinstance(today_data, (int, str)):
                    qianxu = int(today_data)
                    # 查找对应的吉凶和签名信息
                    jixiong = "未知"
                    qianming = "未知"
                    for sort_item in sort_data:
                        if sort_item.get('签序') == qianxu:
                            jixiong = sort_item.get('吉凶', '未知')
                            break
                else:
                    continue
                
                ranking_data.append({
                    'user_id': user_id,
                    'nickname': user_info['nickname'],
                    'card': user_info['card'],
                    'title': user_info['title'],
                    'qianxu': qianxu,
                    'qianming': qianming,
                    'jixiong': jixiong,
                    'sort_priority': GroupManager._get_sort_priority(qianxu, sort_data)
                })
            
            # 根据排序优先级排序
            ranking_data.sort(key=lambda x: x['sort_priority'])
            
            return ranking_data
            
        except Exception as e:
            logger.error(f"筛选群排行数据失败: {e}")
            return []
    
    @staticmethod
    def _get_sort_priority(qianxu: int, sort_data: list) -> int:
        """
        获取签序的排序优先级
        :param qianxu: 签序
        :param sort_data: 排序数据列表
        :return: 排序优先级（越小越靠前）
        """
        try:
            for i, sort_item in enumerate(sort_data):
                if sort_item.get('签序') == qianxu:
                    return i
            return len(sort_data)  # 如果找不到，排在最后
        except Exception as e:
            logger.error(f"获取排序优先级失败: {e}")
            return 9999
    
    @staticmethod
    async def filter_group_jieqian_ranking_data(event: AstrMessageEvent, jieqian_data: dict):
        """
        筛选群聊内的解签排行数据
        :param event: 消息事件
        :param jieqian_data: 解签数据字典
        :return: 筛选后的解签排行数据列表
        """
        try:
            if not event.get_group_id():
                logger.debug("非群聊消息，无法生成群解签排行")
                return []
            
            # 获取群成员列表
            group_members = await GroupManager.get_group_members(event)
            if not group_members:
                logger.warning("无法获取群成员列表")
                return []
            
            # 获取群成员的用户ID列表
            group_user_ids = {member['user_id'] for member in group_members}
            
            # 获取今日日期
            today = get_today()
            
            # 筛选出今日有解签数据且在群内的用户
            ranking_data = []
            
            for user_id, user_jieqian in jieqian_data.items():
                # 检查用户是否在群内
                if user_id not in group_user_ids:
                    continue
                
                # 检查用户今日是否有解签数据
                if today not in user_jieqian:
                    continue
                
                # 获取用户信息
                user_info = None
                for member in group_members:
                    if member['user_id'] == user_id:
                        user_info = member
                        break
                
                if not user_info:
                    continue
                
                # 计算今日解签数量
                today_jieqian = user_jieqian[today]
                if isinstance(today_jieqian, list):
                    jieqian_count = len(today_jieqian)
                else:
                    jieqian_count = 0
                
                if jieqian_count > 0:
                    ranking_data.append({
                        'user_id': user_id,
                        'nickname': user_info['nickname'],
                        'card': user_info['card'],
                        'title': user_info['title'],
                        'jieqian_count': jieqian_count
                    })
            
            # 按解签数量降序排序
            ranking_data.sort(key=lambda x: x['jieqian_count'], reverse=True)
            
            return ranking_data
            
        except Exception as e:
            logger.error(f"筛选群解签排行数据失败: {e}")
            return []
    
    def add_jieqian_record(self, user_id: str, content: str, jieqian_result: str):
        """
        添加解签记录（这个方法主要是为了兼容，实际记录保存在LLMManager中）
        :param user_id: 用户ID
        :param content: 解签内容
        :param jieqian_result: 解签结果
        """
        try:
            # 这个方法主要是为了兼容，实际的解签记录保存已经在LLMManager中处理了
            logger.debug(f"解签记录已保存: 用户{user_id}, 内容: {content[:20]}...")
        except Exception as e:
            logger.error(f"添加解签记录失败: {e}")
    
    def get_user_today_jieqian_list(self, user_id: str) -> list:
        """
        获取用户今日解签列表（委托给LLMManager处理）
        :param user_id: 用户ID
        :return: 解签列表
        """
        try:
            # 这里需要通过其他方式获取LLMManager实例，或者直接读取文件
            # 为了简化，暂时返回空列表，让LLMManager处理
            return []
        except Exception as e:
            logger.error(f"获取用户今日解签列表失败: {e}")
            return []
