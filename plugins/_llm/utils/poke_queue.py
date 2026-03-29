from asyncio import Lock, sleep

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot import logger
from nonebot.adapters.onebot.v11 import PokeNotifyEvent, Bot


class PokeQueue:
    def __init__(self, scheduler: AsyncIOScheduler, sleep_time: int, interval: float):
        self.poke_queue: list[PokeNotifyEvent] = []
        self.lock = Lock()
        self.task_running = False
        self.scheduler = scheduler
        self.sleep_time = sleep_time
        self.interval = interval

    async def add_poke(self, event: PokeNotifyEvent, bot: Bot):
        async with self.lock:
            self.poke_queue.append(event)
            if not self.task_running:
                self.task_running = True
                self.scheduler.add_job(
                    self._process_queue,
                    "date",
                    run_date=None,
                    args=[bot]
                )

    async def _process_queue(self, bot: Bot):
        await sleep(self.sleep_time)
        async with self.lock:
            batch = self.poke_queue[:]
            self.poke_queue.clear()
            self.task_running = False

        for event in batch:
            try:
                await bot.call_api(
                    "send_poke",
                    group_id=event.group_id,
                    user_id=bot.self_id,
                    target_id=event.user_id
                )
            except Exception as e:
                logger.error(f"Poke failed: {e}")
            await sleep(self.interval)
