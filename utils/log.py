from nonebot.log import logger, logger_id, default_filter
import sys


def initialize_logger():
    logger.remove(logger_id)
    logger.add(
        sys.stdout,
        level=0,
        diagnose=False,
        format="[<green>{time:YYYY-MM-DD HH:mm:ss}</green>]"
               "[<lvl>{level}</lvl>]"
               "[<cyan>{name}</cyan>]: {message}",
        filter=default_filter,
        colorize=True
    )


