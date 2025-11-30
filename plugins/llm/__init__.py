from pathlib import Path

import nonebot
from nonebot import get_plugin_config, logger, require
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="llm",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_localstore")
from nonebot_plugin_apscheduler import scheduler

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)
from .events import message_handler, poke_handler

if config.LLM_ONLY_ON_AT:
    logger.opt(colors=True).info(
        "Only responds to LLM requests when mentioned, because LLM_ONLY_ON_AT is <y>enabled</y>"
    )

from .utils.poke_queue import PokeQueue

poke_queue = PokeQueue(
    scheduler=scheduler,
    sleep_time=config.LLM_POKE_SLEEP_TIME,
    interval=config.LLM_POKE_INTERVAL
)

message_handler.setup()
poke_handler.setup(poke_queue)
