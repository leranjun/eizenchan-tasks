"""Auto update for Azur Lane equip data."""
import logging
import os
import subprocess
import sys
from typing import List, cast

from dotenv import load_dotenv
from github import Github
from github.ContentFile import ContentFile

from mwapi import MwApi

load_dotenv()

with open(".control", "r", encoding="utf-8") as f:
    if f.read().strip() == "off":
        sys.exit(0)

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

logger.info("Getting repo...")
g = Github(os.getenv("GH_TOKEN"))
# TODO: use AzurLaneTools/AzurLaneLuaScripts instead
repo = g.get_repo("Dimbreath/AzurLaneData")
logger.info("Got repo.")

logger.info("Getting latest commit...")
commit = repo.get_branch("master").commit
open("commit.txt", "a", encoding="utf-8").close()
with open("commit.txt", "r+", encoding="utf-8") as f:
    base = f.read()
    if base == commit.sha:
        logger.info("No new commits.")
        logger.info("Task finished successfully.")
        sys.exit(0)
    else:
        f.seek(0)
        f.write(commit.sha)
        f.truncate()
logger.info("Got latest commit.")

logger.info("Updating files...")
NO_CHANGE = True

logger.info("Updating equip file...")
content = cast(
    ContentFile, repo.get_contents("zh-CN/sharecfg/equip_data_statistics.lua")
)
content = content.decoded_content.decode("utf-8")
open("ESF/dat/equip_data_statistics.lua", "w", encoding="utf-8").close()
with open("ESF/dat/equip_data_statistics.lua", "r+", encoding="utf-8") as f:
    if f.read() != content:
        NO_CHANGE = False
        f.seek(0)
        f.write(content)
        f.truncate()
        logger.info("Updated equip file.")
    else:
        logger.info("Equip file already up to date.")

logger.info("Updating data files...")
contents = cast(
    List[ContentFile], repo.get_contents("zh-CN/sharecfg/equip_data_statistics_sublist")
)
for content in contents:
    name = content.name
    content = content.decoded_content.decode("utf-8")
    open("ESF/dat/" + name, "w", encoding="utf-8").close()
    with open("ESF/dat/" + name, "r+", encoding="utf-8") as f:
        if f.read() != content:
            f.seek(0)
            f.write(content)
            f.truncate()
            logger.info("Updated %s.", name)

if NO_CHANGE:
    logger.info("No changes to data files.")
    logger.info("Task finished successfully.")
    sys.exit(0)
else:
    logger.info("Finished updating files.")

logger.info("Running ESF...")
p = subprocess.Popen(["/usr/bin/lua", "ESF/esf.lua"])
p.wait()
logger.info("Finished running ESF.")

logger.info("Opening formatted equip file...")
with open("equip_formatted.lua", "r", encoding="utf-8") as f:
    data = f.read()
    logger.info("Got formatted equip file.")

logger.info("Getting target page...")
api = MwApi()
api.login_with_config("passwords.py", "zh")
target = api.get_content("Module:碧蓝航线Equips/data")
if target != data:
    logger.info("Target page is outdated. Updating target page...")
    api.edit(
        "Module:碧蓝航线Equips/data",
        text=data,
        bot=True,
        minor=True,
        summary="更新数据",
        tags="Bot",
    )
else:
    logger.info("Target page is already up to date.")

logger.info("Task finished successfully.")
