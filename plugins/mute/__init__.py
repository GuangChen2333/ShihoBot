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
