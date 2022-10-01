import argparse
import re

from mwapi import mwAPI

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


def toZhNum(o):
    o = str(o)
    for k, v in ZHNUM:
        o = o.replace(str(k), str(v))
    return o


with open("config.py", "r") as f:
    CONFIG = eval(f.read())

with open("ignore.txt", "r") as f:
    IGNORE = set(f.read().splitlines())

if CONFIG["month"] not in ZHMO:
    raise ValueError("Invalid month")

api = mwAPI()
api.loginWithConfig("passwords.py", "zh")
print("Logged in")

year_zh = toZhNum(CONFIG["year"])
month_zh = ZHMO[CONFIG["month"]]

subList = api.getContent("MGP:萌娘百科月报/月饼/订阅").splitlines()
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
        text="\n{{"
        + f'subst:U:Eizenchan/mooncake|foreword={str(CONFIG["foreword"])}|year={str(CONFIG["year"])}|month={str(CONFIG["month"])}|year-zh={year_zh}|month-zh={month_zh}'
        + "}}",
        summary="您点的月饼已送达，不要忘了给我们五星好评噢～",
        tags="Bot",
        bot=True,
        timeout=60,
    )
