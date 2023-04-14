"""Send mooncake to subscribers."""

import argparse
import ast
import re
import sys

from mwapi import MwApi

parser = argparse.ArgumentParser()
parser.add_argument("--dry", action="store_true", help="dry run")
args = parser.parse_args()

ZHNUM = {
    (0, "〇"),
    (1, "一"),
    (2, "二"),
    (3, "三"),
    (4, "四"),
    (5, "五"),
    (6, "六"),
    (7, "七"),
    (8, "八"),
    (9, "九"),
}

ZHMO = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
    11: "十一",
    12: "十二",
}


def to_zh_num(o: int) -> str:
    # pylint: disable=invalid-name
    """Convert number to Chinese number."""
    r = str(o)
    for k, v in ZHNUM:
        r = r.replace(str(k), str(v))
    return r


with open("config.py", "r", encoding="utf-8") as f:
    CONFIG = ast.literal_eval(f.read())

with open("ignore.txt", "r", encoding="utf-8") as f:
    IGNORE = set(f.read().splitlines())

if CONFIG["month"] not in ZHMO:
    raise ValueError("Invalid month")

api = MwApi()
api.login_with_config("passwords.py", "zh")
print("Logged in")

YEAR_ZH = to_zh_num(CONFIG["year"])
MONTH_ZH = ZHMO[CONFIG["month"]]

res = api.get_content("MGP:萌娘百科月报/月饼/订阅")
if not res:
    sys.exit(1)

subList = res.splitlines()
with open("ignore.txt", "a", encoding="utf-8") as f:
    for line in subList:
        if not line.startswith("#"):
            print(f"{line} ignored")
            continue
        target = re.search(r"\[\[(.*?)\]\]", line)
        if target is None:
            print(f"{line} ignored")
            continue
        target = target.group(1)
        print(f"{line} -> {target}")
        if target in IGNORE:
            print(f"{target} ignored")
            continue
        if args.dry:
            continue
        api.append(
            page=target,
            text=(
                "\n{{subst:U:Eizenchan/mooncake"
                f'|foreword={str(CONFIG["foreword"])}'
                f'|year={str(CONFIG["year"])}'
                f'|month={str(CONFIG["month"])}'
                f"|year-zh={YEAR_ZH}"
                f"|month-zh={MONTH_ZH}"
                "}}"
            ),
            summary="您点的月饼已送达，不要忘了给我们五星好评噢～",
            tags="Bot",
            bot=True,
            timeout=60,
        )
        f.write(f"{target}\n")

if not args.dry:
    with open("ignore.txt", "w", encoding="utf-8") as f:
        f.write("")
