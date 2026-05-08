import asyncio
import random
from dataclasses import dataclass, field

from nonebot import get_plugin_config, logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.plugin.on import on_command
from nonebot.rule import is_type

from utils.helper import minutes_to_seconds, chance
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="mute",
    description="群禁言相关命令",
    usage="/mute_me 随机禁言自己\n/mvote @用户 <分钟> 发起 1 分钟禁言投票",
    config=Config,
)

config = get_plugin_config(Config)

VOTE_DURATION_SECONDS = 60


@dataclass
class VoteChoice:
    vote: str
    role: str


@dataclass
class MuteVote:
    group_id: int
    target_id: int
    duration_minutes: int
    votes: dict[int, VoteChoice] = field(default_factory=dict)
    closed: bool = False


mute_votes: dict[int, MuteVote] = {}


mute_me_matcher = on_command(
    "mute_me",
    is_type(GroupMessageEvent),
    aliases={
        "please"
    }
)

mvote_matcher = on_command("mvote", rule=is_type(GroupMessageEvent))
agree_matcher = on_command("agree", rule=is_type(GroupMessageEvent))
deny_matcher = on_command("deny", rule=is_type(GroupMessageEvent))


async def mute_user(bot: Bot, user_id: int, group_id: int, duration: int):
    await bot.call_api(
        "set_group_ban",
        group_id=group_id,
        user_id=user_id,
        duration=duration
    )
    logger.info(f"Mute user {user_id} in {duration} seconds")


def parse_mvote_args(args: Message) -> tuple[int | None, int | None]:
    target_id = None
    for segment in args:
        if segment.type == "at":
            qq = segment.data.get("qq")
            if qq and qq != "all":
                target_id = int(qq)
                break

    duration_text = args.extract_plain_text().strip()
    duration_minutes = None
    if duration_text:
        duration_minutes = int(duration_text.split()[0])

    return target_id, duration_minutes


def count_vote(vote: MuteVote) -> tuple[int, int]:
    agree = 0
    deny = 0
    for choice in vote.votes.values():
        weight = 2 if choice.role in ("admin", "owner") else 1
        if choice.vote == "agree":
            agree += weight
        else:
            deny += weight
    return agree, deny


async def settle_vote(bot: Bot, message_id: int):
    await asyncio.sleep(VOTE_DURATION_SECONDS)
    vote = mute_votes.pop(message_id, None)
    if not vote or vote.closed:
        return

    vote.closed = True
    agree, deny = count_vote(vote)
    if agree > deny:
        await mute_user(
            bot,
            vote.target_id,
            vote.group_id,
            minutes_to_seconds(vote.duration_minutes),
        )
        await bot.call_api(
            "send_group_msg",
            group_id=vote.group_id,
            message=f"投票结束：agree {agree} > deny {deny}，已禁言 {vote.target_id} {vote.duration_minutes} 分钟。",
        )
    else:
        await bot.call_api(
            "send_group_msg",
            group_id=vote.group_id,
            message=f"投票结束：agree {agree}，deny {deny}，未禁言 {vote.target_id}。",
        )


@mute_me_matcher.handle()
async def on_command(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.user_id
    if chance(0.85):
        duration = minutes_to_seconds(random.randint(1, 5))
    else:
        duration = minutes_to_seconds(random.randint(6, 10))

    await mute_user(bot, user_id, group_id, duration)


@mvote_matcher.handle()
async def on_mvote(
    bot: Bot,
    event: GroupMessageEvent,
    args: Message = CommandArg(),
):
    try:
        target_id, duration_minutes = parse_mvote_args(args)
    except ValueError:
        await mvote_matcher.finish("Usage: /mvote @用户 <分钟>", reply_message=True)

    if target_id is None or duration_minutes is None or duration_minutes <= 0:
        await mvote_matcher.finish("Usage: /mvote @用户 <分钟>", reply_message=True)

    result = await mvote_matcher.send(
        f"禁言投票开始：目标 {target_id}，时长 {duration_minutes} 分钟。\n"
        f"请在 {VOTE_DURATION_SECONDS // 60} 分钟内引用本消息发送 /agree 或 /deny。\n"
        "管理员票权重为 2，普通成员为 1。",
        reply_message=True,
    )
    message_id = result["message_id"]
    mute_votes[message_id] = MuteVote(
        group_id=event.group_id,
        target_id=target_id,
        duration_minutes=duration_minutes,
    )
    asyncio.create_task(settle_vote(bot, message_id))
    await mvote_matcher.finish()


async def handle_vote(event: GroupMessageEvent, choice: str):
    if not event.reply:
        return None

    vote = mute_votes.get(event.reply.message_id)
    if not vote or vote.closed or vote.group_id != event.group_id:
        return None

    vote.votes[event.user_id] = VoteChoice(vote=choice, role=event.sender.role)
    return count_vote(vote)


@agree_matcher.handle()
async def on_agree(event: GroupMessageEvent):
    result = await handle_vote(event, "agree")
    if result is None:
        await agree_matcher.finish("请引用有效的禁言投票消息来投票", reply_message=True)

    agree, deny = result
    await agree_matcher.finish(
        f"已记录 /agree。当前票数：agree {agree}，deny {deny}",
        reply_message=True,
    )


@deny_matcher.handle()
async def on_deny(event: GroupMessageEvent):
    result = await handle_vote(event, "deny")
    if result is None:
        await deny_matcher.finish("请引用有效的禁言投票消息来投票", reply_message=True)

    agree, deny = result
    await deny_matcher.finish(
        f"已记录 /deny。当前票数：agree {agree}，deny {deny}",
        reply_message=True,
    )
