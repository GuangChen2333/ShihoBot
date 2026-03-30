from time import monotonic

import httpx

from nonebot import get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot
from nonebot.plugin import PluginMetadata
from nonebot.rule import is_type

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="is_it_boom",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
COOLDOWN_SECONDS = 300
_last_called_at = 0.0

command_matcher = on_command(
    "viewer状态",
    rule=is_type(GroupMessageEvent),
    aliases={"炸了吗"}
)

@command_matcher.handle()
async def is_it_boom(event: GroupMessageEvent, bot: Bot):
    global _last_called_at

    now = monotonic()
    remaining = COOLDOWN_SECONDS - (now - _last_called_at)
    if remaining > 0:
        return await bot.send(
            event,
            message=f"冷却中，请 {int(remaining) + 1} 秒后再试",
            reply_message=False,
        )

    _last_called_at = now
    await bot.send(event, message="正在获取状态...", reply=False)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://raw.githubusercontent.com/Sekai-World/uptime-monitor/refs/heads/master/history/summary.json",
            timeout=10.0,
        )
        response.raise_for_status()
        services = response.json()
        untitled_response = await client.get(
            "https://live2d-assets.untitled-story.org/model_list.json",
            timeout=10.0,
        )

    lines = [
        f"{service['name']}: {'✅ Online' if service.get('status') == 'up' else '❌ Offline'}"
        for service in services
    ]
    lines.append(
        f"Untitled Live2D Viewer: {'✅ Online' if untitled_response.status_code == 200 else '❌ Offline'}"
    )
    status_text = "\n".join(lines)

    return await bot.send(event, message=status_text, reply_message=False)
