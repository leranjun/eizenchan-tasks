import re

from mwapi import mwAPI

with open("config.py", "r") as f:
    CONFIG = eval(f.read())

api = mwAPI()
api.loginWithConfig("passwords.py", CONFIG["site"])
print("Logged in")

before = CONFIG["before"]
after = CONFIG["after"]

pages = api.listCategoryMembers(before, cmprop="ids", cmtype="file")
print(pages)
print("Got list of pages.")

for x in pages:
    print("Working on: " + str(x["pageid"]))
    content = api.getContent(pageid=x["pageid"])

    # Remove random unicode character
    content = re.sub(
        r"[\u1680\u180E\u2000-\u200B\u200E\u200F\u2028-\u202F\u205F]+", "", content
    )
    content = re.sub(r"([^\xA0])\xA0([^\xA0])", r"\1 \2", content)

    content = re.sub(
        r"\[\[(?:Category|分[类類]|cat)\:" + re.escape(before) + r"(\|.*?)?\]\]",
        r"[[分类:" + after + r"\1]]" if after else "",
        content,
        flags=re.I,
    )

    print(
        api.replace(
            pageid=x["pageid"],
            text=content,
            suppressAbuseFilter=True,
            bot=True,
            minor=True,
            summary="分类替换：【" + before + "】→【" + after + "】",
            tags="Bot",
        )
    )

    print("Finished: " + str(x["pageid"]))
