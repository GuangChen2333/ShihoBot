from nonebot import get_plugin_config, Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.plugin import PluginMetadata
from nonebot.plugin.on import on_command
from nonebot.rule import is_type

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="essence-it",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)


async def is_reference(event: GroupMessageEvent) -> bool:
    return event.reply is not None


command_matcher = on_command(
    "essence",
    rule=is_type(GroupMessageEvent) & is_reference,
    aliases={
        "wtf"
    }
)


@command_matcher.handle()
async def essence(bot: Bot, event: GroupMessageEvent):
    msg_id = event.reply.message_id
    await bot.call_api(
        "set_essence_msg",
        message_id=msg_id
    )
