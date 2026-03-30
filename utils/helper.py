import random


def minutes_to_seconds(minutes: int) -> int:
    return minutes * 60

def chance(p: float) -> bool:
    return random.random() < p
