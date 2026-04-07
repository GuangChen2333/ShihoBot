import json

from nonebot import get_plugin_config, logger, require
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Bot, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.plugin.on import on_command
from nonebot.rule import is_type

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_localstore")
from nonebot_plugin_apscheduler import scheduler
import nonebot_plugin_localstore as store

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="group_name",
    description="群名修改请求与审批",
    usage="/request <name> 提交改名请求(<=10字符)\n/approve 管理员审批",
    config=Config,
)

config = get_plugin_config(Config)
QUEUE_FILE = store.get_plugin_data_file("queue.json")


def load_queue() -> list[dict]:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    return []


def save_queue(queue: list[dict]) -> None:
    QUEUE_FILE.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8"
    )


request_cmd = on_command("request", rule=is_type(GroupMessageEvent))
approve_cmd = on_command(
    "approve",
    rule=is_type(GroupMessageEvent),
    permission=GROUP_ADMIN | GROUP_OWNER,
)


@request_cmd.handle()
async def handle_request(_: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        await request_cmd.finish("Usage: /request <New Name>", reply_message=True)
    if len(name) > 10:
        await request_cmd.finish("名称不能超过10个字符", reply_message=True)

    is_admin = event.sender.role in ("admin", "owner")
    queue = load_queue()
    queue.append({
        "group_id": str(event.group_id),
        "name": name,
        "requested_by": event.user_id,
        "approved": is_admin,
    })
    save_queue(queue)

    if is_admin:
        position = next(
            i + 1 for i, e in enumerate(queue) if e is queue[-1]
        )
        await request_cmd.finish(
            f"排在第 {position} 位。",
            reply_message=True,
        )
    else:
        await request_cmd.finish(
            f"等待管理员 /approve", reply_message=True
        )


@approve_cmd.handle()
async def handle_approve(_: Bot, event: GroupMessageEvent):
    queue = load_queue()
    group_id = str(event.group_id)

    pending = next(
        (e for e in queue if e["group_id"] == group_id and not e.get("approved")),
        None,
    )
    if not pending:
        await approve_cmd.finish("当前没有待审批的改名请求", reply_message=True)

    pending["approved"] = True
    save_queue(queue)
    position = next(
        i + 1 for i, e in enumerate(queue) if e is pending
    )
    await approve_cmd.finish(
        f"已批准: {config.GROUP_NAME_PREFIX} {pending['name']}\n"
        f"排在第 {position} 位。",
        reply_message=True,
    )


@scheduler.scheduled_job("cron", hour=0, minute=0)
async def apply_group_names():
    from nonebot import get_bot

    queue = load_queue()
    if not queue:
        return

    first = next((e for e in queue if e.get("approved")), None)
    if not first:
        return

    bot: Bot = get_bot()  # type: ignore
    group_name = f"{config.GROUP_NAME_PREFIX} {first['name']}"
    try:
        await bot.set_group_name(
            group_id=int(first["group_id"]), group_name=group_name
        )
        logger.info(f"群 {first['group_id']} 改名为: {group_name}")
        queue.remove(first)
        save_queue(queue)
    except Exception as e:
        logger.error(f"群 {first['group_id']} 改名失败: {e}")
