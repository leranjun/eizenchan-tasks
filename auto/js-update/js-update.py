"""Update JS files on MGP."""

import logging
import subprocess
import sys
from pathlib import Path

from mwapi import mwAPI

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

logger.info("Getting JS list...")
with open("list.py", "r", encoding="UTF-8") as f:
    LIST = eval(f.read())
logger.info("Got JS list.")

logger.info("Connecting to MGP...")
api = mwAPI()
api.connectWithConfig("passwords.py", "zh")
logger.info("Connected to MGP.")

for page in LIST:
    logger.info("Getting %s...", page)
    content = api.getContent(page)
    escaped = page.replace(":", "/")
    path = Path("js/" + escaped)
    path.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(content))
    logger.info("Finished %s.", page)

logger.info("Running bash script...")
subprocess.call("./js-update.sh", shell=True)
logger.info("Finished running bash script.")

logger.info("Task finished successfully.")
