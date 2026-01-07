from plugins.llm.plugins.continuitier import Continuitier
from plugins.llm.plugins.planner import Planner
from plugins.llm.plugins.replier import Replier
from plugins.llm.plugins.scheduler import Scheduler


class LLM:
    def __init__(self):
        self._replier = Replier(max_context_count=20)
        self._scheduler = Scheduler()
        self._planner = Planner(max_context_count=10)

    def push_context(self, nick_name: str, context: str) -> None:
        self._replier.push_context(nick_name, context)
        self._planner.push_context(nick_name, context)
    
    async def chat(self, nick_name: str, message: str, force_reply: bool = False) -> str | None:
        activity = await self._scheduler.get()

        if force_reply or await self._planner.judge(message):
            result = await self._replier.chat(
                nick_name=nick_name,
                message=message,
                current_activity=activity
            )
            self._planner.push_context("你", result)
            return result
        else:
            return None
