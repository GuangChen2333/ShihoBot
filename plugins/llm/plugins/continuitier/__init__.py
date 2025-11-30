import time

from nonebot import get_plugin_config, logger
from nonebot.plugin import PluginMetadata
from openai import AsyncOpenAI

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="Continuitier",
    description="",
    usage="",
    config=Config,
)

from ..common.context import StringContext

config = get_plugin_config(Config)

class Continuitier:
    def __init__(self, max_context_count: int = 7):
        self._client = AsyncOpenAI(
            base_url=config.LLM_CONTINUITIER_BASE_URL,
            api_key=config.LLM_CONTINUITIER_API_KEY
        )
        self._context = StringContext(max_context_count)

    async def judge(self, msg: str) -> bool:
        start = time.perf_counter()

        self._context.push(msg)
        response = await self._client.responses.create(
            model=config.LLM_CONTINUITIER_MODEL,
            instructions=config.LLM_CONTINUITIER_PROMPT,
            input=self._context.build(),
            temperature=0.35
        )
        cost = time.perf_counter() - start

        logger.opt(colors=True).info(
            f"[<g>{cost:.1f}s</g> | <m>{response.usage.total_tokens}</m> Tokens] "
            f"{msg} -> New Topic: <b><y>{response.output_text}</y></b>"
        )
        return response.output_text == "true"
