from nonebot.adapters.onebot.v11 import PokeNotifyEvent, Bot
from nonebot.plugin.on import on_notice
from nonebot import logger
from nonebot.rule import is_type


def setup(poke_queue):
    poke_matcher = on_notice(
        rule=is_type(PokeNotifyEvent)
    )

    @poke_matcher.handle()
    async def on_poke_event(event: PokeNotifyEvent, bot: Bot):
        if str(event.target_id) != bot.self_id:
            return
        if not event.group_id:
            return

        logger.info(
            f"{event.user_id} joined poke queue.")
        await poke_queue.add_poke(event, bot)
