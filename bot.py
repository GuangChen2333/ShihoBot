import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotAdapter

from utils.log import initialize_logger

initialize_logger()

nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter(OneBotAdapter)

nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run()
