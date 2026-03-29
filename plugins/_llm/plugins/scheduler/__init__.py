import json
import time
from datetime import datetime, date
from typing import Dict, Any

import nonebot_plugin_localstore as store
from nonebot import get_plugin_config, logger
from nonebot.plugin import PluginMetadata
from openai import AsyncOpenAI

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="Scheduler",
    description="",
    usage="",
    config=Config,
)

from ...utils.helper import chance
from ..common.holiday import build_special_note

config = get_plugin_config(Config)
CACHE_FILE = store.get_plugin_data_file("schedule.json")


class Scheduler:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=config.LLM_SCHEDULER_BASE_URL,
            api_key=config.LLM_SCHEDULER_API_KEY
        )
        self.cache: Dict[str, Dict[str, Any]] = self._load_cache()

    @staticmethod
    def _load_cache() -> Dict[str, Dict[str, Any]]:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return {}

    def _save_cache(self) -> None:
        CACHE_FILE.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding='utf-8')

    @staticmethod
    def _resolve_task() -> Dict[str, str]:
        now = datetime.now()
        now_str = now.strftime("%H:%M")
        slots = config.time_slots
        for slot in slots:
            if slot.start <= now_str <= slot.end:
                return {"mode": "time", "task": slot.tasks[0], "slot": f"{slot.start}-{slot.end}"}
        return {"mode": "free", "slot": "free"}

    @staticmethod
    def _apply_random_events(result: Dict[str, Any]) -> Dict[str, Any]:
        triggered = result.get("random_events", [])
        result["random_events"] = triggered
        return result

    async def _call_llm(self, resolved: Dict[str, str]) -> Dict[str, Any]:
        now = datetime.now()
        remaining_slots = []
        now_str = now.strftime("%H:%M")
        for slot in config.time_slots:
            if slot.start >= now_str:
                remaining_slots.append({
                    "slot": f"{slot.start}-{slot.end}",
                    "task": slot.tasks
                })

        today = date.today()
        special_note = build_special_note(today)

        user_data: Dict[str, Any] = {
            "mode": resolved["mode"],
            "time": now.strftime("%H:%M"),
            "date": now.strftime("%Y-%m-%d"),
            "current_task": resolved.get("task", ""),
            "current_slot": resolved.get("slot", ""),
            "remaining_slots": remaining_slots,
            "is_holiday": config.is_holiday(),
            "special_today": special_note
        }

        start = time.perf_counter()
        # noinspection PyTypeChecker
        response = await self._client.chat.completions.create(
            model=config.LLM_SCHEDULER_MODEL,
            messages=[
                {"role": "system", "content": config.LLM_SCHEDULER_PERSONALITY},
                {"role": "user", "content": str(user_data)}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        content_str = response.choices[0].message.content
        result_dict: dict = json.loads(content_str)

        result_dict.update({
            "random_events": [],
            "time_slot": resolved["slot"],
            "next": remaining_slots[0] if len(remaining_slots) > 0 else None,
            "is_holiday": config.is_holiday()
        })

        cost = time.perf_counter() - start
        logger.opt(colors=True).info(
            f"[<g>{cost:.1f}s</g> | <m>{response.usage.total_tokens}</m> Tokens] "
            f"{result_dict.get('action')}"
        )
        return result_dict

    async def get(self) -> Dict[str, Any]:
        today_str = date.today().isoformat()
        resolved = self._resolve_task()
        slot_key = resolved["slot"]
        now_ts = time.time()
        refresh_seconds = max(config.LLM_SCHEDULER_REFRESH_MINUTES, 1) * 60

        if today_str not in self.cache:
            self.cache[today_str] = {}

        cached_entry = self.cache[today_str].get(slot_key)
        generated_at = 0.0
        if isinstance(cached_entry, dict):
            generated_at = cached_entry.get("generated_at", 0.0)

        need_refresh = (
            cached_entry is None
            or (now_ts - generated_at) >= refresh_seconds
        )

        if need_refresh:
            logger.info("Generating schedule...")
            result = await self._call_llm(resolved)
            for ev in config.random_events:
                if chance(ev.probability):
                    result["random_events"].append(ev.event)
            self.cache[today_str][slot_key] = {
                "generated_at": now_ts,
                "data": result
            }
            self._save_cache()
            return result

        cached_data = cached_entry.get("data", cached_entry)
        return cached_data.copy()
