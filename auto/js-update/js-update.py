from sys import exit
import logging
from mwapi import mwAPI
import subprocess
import os
from errno import EEXIST

with open(".control", "r") as f:
    if (f.read().strip() == "off"):
        exit(0)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safe_open_w(path, mode="r", **kwargs):
    mkdir_p(os.path.dirname(path))
    return open(path, mode, **kwargs)


logging.basicConfig(
    filename="log.txt",
    filemode="w",
    level="INFO",
    format="%(asctime)s (%(name)s) - %(levelname)s: %(message)s")

logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
logger.addHandler(ch)

logger.info("Task started.")

logger.info("Getting JS list...")
with open("list.py", "r", encoding="UTF-8") as f:
    LIST = eval(f.read())
logger.info("Got JS list.")

logger.info("Connecting to MGP...")
with open("passwords.py", "r") as f:
    CONFIG = eval(f.read())
api = mwAPI(CONFIG["zh"][0])
logger.info("Connected to MGP.")

for page in LIST:
    logger.info("Getting " + page + "...")
    content = api.getContent(page)
    escaped = page.replace(":", "/")
    with safe_open_w("js/" + escaped, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Finished " + page + ".")

logger.info("Running bash script...")
rc = subprocess.call("./js-update.sh", shell=True)
logger.info("Finished running bash script.")

logger.info("Task finished successfully.")
