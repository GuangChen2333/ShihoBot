from nonebot import get_plugin_config, logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot.plugin import PluginMetadata
from nonebot.plugin.on import on_command
from nonebot.rule import is_type

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="mute",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

command_matcher = on_command(
    "mute_me",
    is_type(GroupMessageEvent),
    aliases={
        "please"
    }
)


async def mute_user(bot: Bot, user_id: int, group_id: int, duration: int):
    await bot.call_api(
        "set_group_ban",
        group_id=group_id,
        user_id=user_id,
        duration=duration
    )
    logger.info(f"Mute user {user_id} in {duration} seconds")

@command_matcher.handle()
async def on_command(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.user_id
    await mute_user(bot, user_id, group_id, 30)

# async def is_bilibili(event: GroupMessageEvent):
#     for msg in event.message:
#         if msg.type == "text":
#             content: str = msg.data['text']
#             return 'bilibili' in content.lower() or 'b23' in content.lower()
#         elif msg.type == "json":
#             data: dict = json.loads(msg.data['data'])
#             return data.get("meta", {}).get("detail_1", {}).get("appid") == "1109937557"
#     return False
#
#
# message_matcher = on_message(
#     rule=is_bilibili
# )
#
# @message_matcher.handle()
# async def on_group_message(bot: Bot, event: GroupMessageEvent):
#     await mute_user(bot, 3106123652, event.group_id, 60)
