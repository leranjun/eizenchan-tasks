import logging

from mwapi import mwAPI

logging.basicConfig(
    filename="log.txt",
    filemode="w",
    level="INFO",
    format="%(asctime)s (%(name)s) - %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
logger.addHandler(ch)

logger.info("Task started.")

logger.info("Opening formatted equip file...")
with open("equip_formatted.lua") as f:
    data = f.read()
    logger.info("Got formatted equip file.")

logger.info("Getting target page...")
with open("passwords.py", "r") as f:
    CONFIG = eval(f.read())
api = mwAPI(CONFIG["zh"][0])
api.login(CONFIG["zh"][1], CONFIG["zh"][2])
target = api.getContent("Module:碧蓝航线Equips/data")
logger.info("Updating target page...")
api.edit(
    "Module:碧蓝航线Equips/data",
    text=data,
    bot=True,
    minor=True,
    summary="更新数据",
    tags="Bot",
)

logger.info("Task finished successfully.")
