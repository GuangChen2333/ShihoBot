import json

from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot.plugin.on import on_message, on_command
from nonebot.rule import to_me

from ..config import Config
from ..plugins.scheduler import Scheduler
from ..utils.helper import contains_text, build_message
from ..plugins.continuitier import Continuitier
from ..plugins.replier import Replier
from nonebot import get_plugin_config, logger


def setup():
    config = get_plugin_config(Config)
    message_matcher = on_message(
        rule=to_me() if config.LLM_ONLY_ON_AT else None
    )
    command_matcher = on_command(
        "test"
    )

    continuitier = Continuitier(max_context_count=7)
    replier = Replier(max_context_count=20)
    scheduler = Scheduler()

    @command_matcher.handle()
    async def on_test(event: GroupMessageEvent, bot: Bot):
        msg = await scheduler.generate()
        await bot.send(event, json.dumps(
            msg, ensure_ascii=False, indent=2
        ), reply_message=True)

    @message_matcher.handle()
    async def on_group_msg_event(event: GroupMessageEvent, bot: Bot):
        if contains_text(event.message):
            # new_topic = await continuitier.judge(event.message.extract_plain_text())
            activity = await scheduler.generate()
            content = await replier.chat(
                nick_name=event.sender.card,
                msg=build_message(event.message),
                current_activity=activity
            )
            await bot.send(event, content, reply_message=True)
