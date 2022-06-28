from mwapi import mwAPI
import re

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


def toZhNum(o):
    o = str(o)
    for k, v in ZHNUM:
        o = o.replace(str(k), str(v))


with open("config.py", "r") as f:
    CONFIG = eval(f.read())

api = mwAPI()
api.loginWithConfig("passwords.py", "zh")
print("Logged in")

year_zh = toZhNum(CONFIG["year"])
month_zh = toZhNum(CONFIG["month"])

subList = api.getContent("Help:沙盒").splitlines()
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
    print(api.append(page=target, text="{{subst:U:Eizenchan/mooncake|foreword=" + str(CONFIG["foreword"]) + "|year=" + str(
        CONFIG["year"]) + "|month=" + str(CONFIG["month"]) + "|year-zh=" + year_zh + "|month-zh=" + month_zh + "}}", summary="您点的月饼已送达，不要忘了给我们五星好评噢～", tags="Bot", bot=True))
