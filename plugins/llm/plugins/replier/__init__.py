import json
import time
from datetime import datetime

from nonebot import get_plugin_config, logger
from nonebot.plugin import PluginMetadata
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam, \
    ChatCompletionAssistantMessageParam

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="Replier",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

from ..common.context import ChatCompletionContext


class Replier:
    def __init__(self, max_context_count: int = 20):
        self._client = AsyncOpenAI(
            base_url=config.LLM_REPLIER_BASE_URL,
            api_key=config.LLM_REPLIER_API_KEY
        )
        self._context = ChatCompletionContext(max_context_count)

    async def chat(self, nick_name: str, msg: str, current_activity: dict):
        start = time.perf_counter()

        self._context.push(
            ChatCompletionUserMessageParam(
                role="user",
                content=f"{nick_name}: {msg}"
            )
        )

        action = current_activity.get("action", "")
        reason = current_activity.get("reason", "")
        events = current_activity.get("random_events", [])
        events_str = ", ".join(events) if events else "无"
        time_slot = current_activity.get("time_slot", "")
        next_activity = current_activity.get("next", {})
        activity_str = (f"当前活动: {action}, 时间段: {time_slot}, 理由: {reason}, "
                        f"随机事件: {events_str}, 下个日程: {json.dumps(next_activity)}")

        system_messages = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=config.LLM_REPLIER_PROMPT
            ),
            ChatCompletionSystemMessageParam(
                role="system",
                content=activity_str
            ),
            ChatCompletionSystemMessageParam(
                role="system",
                content=f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        ]

        response = await self._client.chat.completions.create(
            model=config.LLM_REPLIER_MODEL,
            messages=system_messages + self._context.messages,
            temperature=0.8,
        )

        reply_text = response.choices[0].message.content

        self._context.push(
            ChatCompletionAssistantMessageParam(
                role="assistant",
                content=reply_text
            )
        )

        cost = time.perf_counter() - start
        logger.opt(colors=True).info(
            f"[<g>{cost:.1f}s</g> | <m>{response.usage.total_tokens}({response.usage.prompt_tokens_details.cached_tokens} Cached)</m> Tokens] "
            f"{nick_name} {msg} -> Reply: <b><y>{reply_text}</y></b>"
        )

        return reply_text
