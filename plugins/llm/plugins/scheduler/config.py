from datetime import datetime
from typing import List

from pydantic import BaseModel


class SchedulerTimeSlot(BaseModel):
    start: str
    end: str
    tasks: List[str]

class SchedulerRandomEvent(BaseModel):
    event: str
    probability: float

class Config(BaseModel):
    LLM_SCHEDULER_BASE_URL: str
    LLM_SCHEDULER_API_KEY: str
    LLM_SCHEDULER_MODEL: str = "gpt-5-mini"
    LLM_SCHEDULER_PERSONALITY: str = """
你现在扮演日野森志步。请根据当前时间合理安排活动

角色设定:
日本女高中二年级学生，性格温柔但略带傲娇
Leo/need 乐队的贝斯手，喜欢拉面、书法和可爱的小动物
对姐姐日野森雫有依赖感，但不会主动去关心她，大概率在处于被动状态
日常生活中喜欢练习贝斯和乐队，空闲时间可以自由安排
你的乐队成员如下:
星乃一歌（主唱吉他手）
天马咲希（键盘手，且是同班同学，于二年级同班）
望月穗波（鼓手）
日野森志步（贝斯手）
四个人在同一所学校

行为要求：
根据当前时间合理安排活动
action 字段仅输出当前时间段的活动，后续的日程表仅供参考
reason 字段填写这么做的心里想法
注意今天是否是休息日
在空闲时间可以自由发挥，但符合角色性格
输出内容必须中文

输出格式必须严格遵循如下JSON格式：
{
  "action": "12:35 的午休时间，我坐在教室靠窗的角落，轻轻闭眼小憩，手边摊着书法练习本和笔，旁边是一只可爱的小动物毛绒玩具。心里想着今晚的贝斯练习和下一节课要复习的内容。",
  "reason": "利用午休让眼睛和手臂短暂放松、恢复状态，方便稍后继续排练与练字。"
}
"""

    LLM_SCHEDULER_WORKDAY_TIMESLOTS: str = ""
    LLM_SCHEDULER_HOLIDAY_TIMESLOTS: str = ""
    LLM_SCHEDULER_WORKDAY_RANDOM_EVENTS: str = ""
    LLM_SCHEDULER_HOLIDAY_RANDOM_EVENTS: str = ""
    FORCE_HOLIDAY: bool = False

    def is_holiday(self) -> bool:
        if self.FORCE_HOLIDAY:
            return True
        now = datetime.now()
        return now.weekday() >= 5

    @property
    def time_slots(self) -> List[SchedulerTimeSlot]:
        slots = []
        raw = (self.LLM_SCHEDULER_HOLIDAY_TIMESLOTS if self.is_holiday()
               else self.LLM_SCHEDULER_WORKDAY_TIMESLOTS)
        if not raw:
            return slots
        for item in raw.split(","):
            time_range, tasks_str = item.split("=")
            start, end = time_range.split("-")
            tasks = tasks_str.split("|")
            slots.append(SchedulerTimeSlot(start=start, end=end, tasks=tasks))
        return slots

    @property
    def random_events(self) -> List[SchedulerRandomEvent]:
        events = []
        raw = (self.LLM_SCHEDULER_HOLIDAY_RANDOM_EVENTS if self.is_holiday()
               else self.LLM_SCHEDULER_WORKDAY_RANDOM_EVENTS)
        if not raw:
            return events
        for item in raw.split(","):
            event, prob = item.split(":")
            events.append(SchedulerRandomEvent(event=event, probability=float(prob)))
        return events
