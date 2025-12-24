import asyncio
import random
import time

import nonebot
from nonebot import get_plugin_config
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot.internal.rule import Rule
from nonebot.plugin.on import on_message
from nonebot.rule import to_me

from ..LLM import LLM
from ..config import Config
from ..utils.helper import contains_text, build_message


def setup():
    config = get_plugin_config(Config)

    async def is_not_ignored(event: GroupMessageEvent) -> bool:
        command_starts: set[str] = nonebot.get_driver().config.command_start
        msg = build_message(event.message)
        return not any(msg.startswith(prefix) for prefix in command_starts)

    async def contain_text(event: GroupMessageEvent) -> bool:
        return contains_text(event.message)

    llm_rules = Rule(
        is_not_ignored, contain_text
    )

    if config.LLM_ONLY_ON_AT:
        llm_rules = llm_rules & to_me()

    message_matcher = on_message(
        rule=llm_rules
    )

    llm = LLM()

    @message_matcher.handle()
    async def on_group_msg_event(event: GroupMessageEvent, bot: Bot):
        start_time = time.monotonic()

        message = build_message(event.message)
        nick_name = event.sender.card if event.sender.card else event.sender.nickname

        llm.push_context(nick_name=nick_name, context=message)

        content = await llm.chat(
            nick_name=nick_name,
            message=message,
            force_reply=event.to_me
        )

        if not content:
            return

        parts = content.split("\n")
        index = 0

        for part in parts:
            if not part.strip():
                index += 1
                continue

            length = len(part)
            char_per_sec = random.uniform(6, 10)
            delay = max(0.5, min(length / char_per_sec, 5))
            await asyncio.sleep(delay)

            total_time = time.monotonic() - start_time
            use_reply = (index == 0 and total_time > 6)

            await bot.send(event, part, reply_message=use_reply)
            index += 1
