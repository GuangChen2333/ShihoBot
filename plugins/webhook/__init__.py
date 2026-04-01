from nonebot import get_driver, get_plugin_config, logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot.compat import model_dump
from nonebot.exception import ActionFailed
from nonebot.plugin import PluginMetadata
from pydantic import BaseModel

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="webhook",
    description="通过 HTTP webhook 向群里转发消息",
    usage="POST WEBHOOK_PATH，请求体中的 data 会被发送到配置的群",
    config=Config,
)

config = get_plugin_config(Config)


class WebhookPayload(BaseModel):
    data: str
    group_id: int | None = None
    secret: str | None = None


driver = get_driver()
app = driver.server_app


@app.post(config.WEBHOOK_PATH)
async def webhook_send(payload: WebhookPayload):
    if config.WEBHOOK_SECRET and payload.secret != config.WEBHOOK_SECRET:
        return {"ok": False, "message": "invalid secret"}

    group_id = payload.group_id or config.WEBHOOK_GROUP_ID
    if group_id is None:
        return {"ok": False, "message": "group_id is required"}

    try:
        bots = list(driver.bots.values())
        if not bots:
            return {"ok": False, "message": "bot is not connected"}

        bot = bots[0]
        if not isinstance(bot, Bot):
            return {"ok": False, "message": "unsupported bot type"}

        result = await bot.send_group_msg(group_id=group_id, message=payload.data)
        return {"ok": True, "group_id": group_id, "result": model_dump(result)}
    except ActionFailed as e:
        logger.exception("Webhook send failed")
        return {"ok": False, "message": str(e)}

