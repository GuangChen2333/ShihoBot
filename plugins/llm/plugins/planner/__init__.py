import time as time_module
from datetime import datetime, time

from nonebot import get_plugin_config, logger
from nonebot.plugin import PluginMetadata
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="Planner",
    description="",
    usage="",
    config=Config,
)

from ..common.context import StringContext

config = get_plugin_config(Config)


class Planner:
    def __init__(self, max_context_count: int = 5):
        self._client = AsyncOpenAI(
            base_url=config.LLM_PLANNER_BASE_URL,
            api_key=config.LLM_PLANNER_API_KEY,
        )
        self._context = StringContext(max_context_count)

    def push_context(self, nick_name: str, context: str):
        self._context.push(f"{nick_name}: {context}")

    async def judge(self, msg: str) -> bool:
        start = time_module.perf_counter()
        now = datetime.now().time()
        if now >= time(23, 0) or now <= time(6, 30):
            result = False
            response = None
        else:
            response = await self._client.chat.completions.create(
                model=config.LLM_PLANNER_MODEL,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=config.LLM_PLANNER_PROMPT
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=self._context.build()
                    )
                ],
                temperature=0.05
            )
            result = response.choices[0].message.content == "true"
        cost = time_module.perf_counter() - start

        if response:
            logger.opt(colors=True).info(
                f"[<g>{cost:.1f}s</g> | <m>{response.usage.total_tokens}({response.usage.prompt_tokens_details.cached_tokens} Cached)</m> Tokens] "
                f"{msg} -> Reply: <b><y>{response.choices[0].message.content}</y></b>"
            )
        else:
            logger.opt(colors=True).info(
                f"[<g>{cost:.1f}s</g>] {msg} -> Reply: <b><y>{response.choices[0].message.content}</y></b>")

        return result
