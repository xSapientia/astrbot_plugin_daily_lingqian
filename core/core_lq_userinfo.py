"""
用户信息获取模块
获取用户的nickname、card、title等信息
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
import astrbot.api.message_components as Comp

class UserInfoManager:
    """用户信息管理器"""
    
    @staticmethod
    def get_user_info(event: AstrMessageEvent, target_user_id: str = None):
        """
        获取用户信息
        :param event: 消息事件
        :param target_user_id: 目标用户ID，如果为None则获取发送者信息
        :return: dict 包含nickname, card, title等信息
        """
        try:
            # 如果指定了目标用户ID，尝试从@消息中获取
            if target_user_id:
                # 检查消息中是否有@组件
                messages = event.get_messages()
                for msg in messages:
                    if isinstance(msg, Comp.At) and str(msg.qq) == str(target_user_id):
                        # 找到@的用户，获取其信息
                        return UserInfoManager._get_at_user_info(event, target_user_id)
                
                # 如果没有找到@消息，返回基本信息
                return {
                    'user_id': target_user_id,
                    'nickname': target_user_id,  # 如果无法获取nickname，使用user_id
                    'card': target_user_id,
                    'title': ''
                }
            else:
                # 获取发送者信息
                return UserInfoManager._get_sender_info(event)
                
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            user_id = target_user_id or event.get_sender_id()
            return {
                'user_id': user_id,
                'nickname': user_id,
                'card': user_id,
                'title': ''
            }
    
    @staticmethod
    def _get_sender_info(event: AstrMessageEvent):
        """获取发送者信息"""
        try:
            user_id = event.get_sender_id()
            nickname = event.get_sender_name() or user_id
            
            # 尝试获取群名片
            card = nickname
            title = ''
            
            # 如果是群聊，尝试获取更详细的信息
            if event.get_group_id():
                try:
                    group = event.get_group()
                    if group and hasattr(group, 'members'):
                        for member in group.members:
                            if str(member.user_id) == str(user_id):
                                card = getattr(member, 'card', None) or getattr(member, 'nickname', nickname)
                                title = getattr(member, 'title', '')
                                break
                except Exception as e:
                    logger.debug(f"获取群成员信息失败: {e}")
            
            return {
                'user_id': user_id,
                'nickname': nickname,
                'card': card,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"获取发送者信息失败: {e}")
            user_id = event.get_sender_id()
            return {
                'user_id': user_id,
                'nickname': user_id,
                'card': user_id,
                'title': ''
            }
    
    @staticmethod
    def _get_at_user_info(event: AstrMessageEvent, target_user_id: str):
        """获取@用户的信息"""
        try:
            # 尝试从群成员中获取信息
            if event.get_group_id():
                try:
                    group = event.get_group()
                    if group and hasattr(group, 'members'):
                        for member in group.members:
                            if str(member.user_id) == str(target_user_id):
                                nickname = getattr(member, 'nickname', target_user_id)
                                card = getattr(member, 'card', None) or nickname
                                title = getattr(member, 'title', '')
                                return {
                                    'user_id': target_user_id,
                                    'nickname': nickname,
                                    'card': card,
                                    'title': title
                                }
                except Exception as e:
                    logger.debug(f"从群成员获取@用户信息失败: {e}")
            
            # 如果无法获取详细信息，返回基本信息
            return {
                'user_id': target_user_id,
                'nickname': target_user_id,
                'card': target_user_id,
                'title': ''
            }
            
        except Exception as e:
            logger.error(f"获取@用户信息失败: {e}")
            return {
                'user_id': target_user_id,
                'nickname': target_user_id,
                'card': target_user_id,
                'title': ''
            }
    
    @staticmethod
    def extract_at_user_id(event: AstrMessageEvent):
        """从消息中提取@的用户ID"""
        try:
            messages = event.get_messages()
            for msg in messages:
                if isinstance(msg, Comp.At):
                    return str(msg.qq)
            return None
        except Exception as e:
            logger.error(f"提取@用户ID失败: {e}")
            return None
