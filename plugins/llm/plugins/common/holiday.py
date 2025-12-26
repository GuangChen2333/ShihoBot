import json
import urllib.request
from datetime import date
from typing import Dict, List, Tuple

import nonebot_plugin_localstore as store

# 固定公历节日兜底，按 (month, day)
_FALLBACK_HOLIDAYS: Dict[Tuple[int, int], str] = {
    (1, 1): "元旦",
    (2, 14): "情人节",
    (3, 8): "妇女节",
    (5, 1): "劳动节",
    (6, 1): "儿童节",
    (10, 1): "国庆节",
    (12, 24): "平安夜",
    (12, 25): "圣诞节",
    (12, 31): "跨年夜",
}

# 角色生日
_BIRTHDAYS: Dict[Tuple[int, int], str] = {
    (1, 8): "志步生日",
    (1, 27): "真冬生日",
    (1, 30): "流歌生日",
    (2, 10): "奏生日",
    (2, 17): "KAITO生日",
    (3, 2): "心羽生日",
    (3, 19): "爱莉生日",
    (4, 14): "实乃理生日",
    (4, 30): "绘名生日",
    (5, 9): "咲希生日",
    (5, 17): "司生日",
    (5, 25): "冬弥生日",
    (6, 24): "类生日",
    (7, 20): "宁宁生日",
    (7, 26): "杏生日",
    (8, 11): "一歌生日",
    (8, 27): "瑞希生日",
    (8, 31): "初音未来生日",
    (9, 9): "笑梦生日",
    (10, 5): "遥生日",
    (10, 27): "穗波生日",
    (11, 5): "MEIKO生日",
    (11, 12): "彰人生日",
    (12, 6): "雫生日",
    (12, 27): "铃和连生日",
}

_CACHE_FILE = store.get_plugin_data_file("holidays.json")
_holiday_cache: Dict[str, Dict[str, str]] | None = None


def _load_cache() -> Dict[str, Dict[str, str]]:
    global _holiday_cache
    if _holiday_cache is not None:
        return _holiday_cache
    if _CACHE_FILE.exists():
        try:
            _holiday_cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            _holiday_cache = {}
    else:
        _holiday_cache = {}
    return _holiday_cache


def _save_cache(cache: Dict[str, Dict[str, str]]) -> None:
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_year(year: int) -> Dict[str, str]:
    url = f"https://api.11holidays.com/v1/holidays?country=JP&year={year}"
    req = urllib.request.Request(url, headers={"User-Agent": "ShihoBot/holiday-fetch"})
    with urllib.request.urlopen(req, timeout=3) as resp:
        content = resp.read().decode("utf-8")
    raw_list = json.loads(content)
    result: Dict[str, str] = {}
    for item in raw_list:
        date_str = item.get("date")
        name = item.get("name")
        if date_str and name:
            result[date_str] = name
    return result


def _get_year_holidays(year: int) -> Dict[str, str]:
    cache = _load_cache()
    key = str(year)
    if key in cache:
        return cache[key]
    try:
        data = _fetch_year(year)
        cache[key] = data
        _save_cache(cache)
        return data
    except Exception:
        # 网络失败时返回空，后续用兜底
        return {}


def holiday_notes(today: date) -> List[str]:
    notes: List[str] = []
    remote = _get_year_holidays(today.year)
    if remote:
        name = remote.get(today.isoformat())
        if name:
            notes.append(f"今天是{name}")
    if not notes:
        fallback_name = _FALLBACK_HOLIDAYS.get((today.month, today.day))
        if fallback_name:
            notes.append(f"今天是{fallback_name}")
    return notes


def birthday_notes(today: date) -> List[str]:
    notes: List[str] = []
    name = _BIRTHDAYS.get((today.month, today.day))
    if name:
        notes.append(f"今天是{name}")
    return notes


def build_special_note(today: date) -> str:
    notes = holiday_notes(today) + birthday_notes(today)
    return "；".join(notes) if notes else "今天无特别节日/生日"
