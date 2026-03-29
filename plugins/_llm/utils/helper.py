import random

from nonebot.internal.adapter import Message


def contains_text(segments: Message) -> bool:
    return any(getattr(seg, "type", None) == "text" for seg in segments)

def contains_image(segments: Message) -> bool:
    return any(getattr(seg, "type", None) == "image" for seg in segments)

def build_message(segments: Message) -> str:
    msgs = []
    for segment in segments:
        if segment.type == 'at':
            msgs.append(f"@{segment.data['qq']}")
        elif segment.type == 'text':
            msgs.append(segment.data['text'])
    return ''.join(msgs)

def get_images(segments: Message) -> list[str]:
    imgs = []
    for segment in segments:
        if segment.type == 'image':
            imgs.append(segment.data['url'])
    return imgs

def chance(p: float) -> bool:
    return random.random() < p
