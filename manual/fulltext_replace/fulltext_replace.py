"""Replace text in all pages that match a query."""
import ast
import re
import sys

from mwapi import MwApi

with open("config.py", "r", encoding="utf-8") as f:
    CONFIG = ast.literal_eval(f.read())

api = MwApi()
api.login_with_config("passwords.py", CONFIG["site"])
print("Logged in")

before = CONFIG["before"]
after = CONFIG["after"]
isRegEx = CONFIG["isRegEx"]
query = CONFIG["query"]
namespace = CONFIG["namespace"]

pages = api.search(query, srprop="", srnamespace=namespace)
print(pages)
print("Got list of pages.")

for x in pages:
    print("Working on: " + str(x["pageid"]))
    content = api.get_content(pageid=x["pageid"])

    if content is None:
        print("Page does not exist, skipping...")
        continue

    # Remove random unicode character
    content = re.sub(
        r"[\u1680\u180E\u2000-\u200B\u200E\u200F\u2028-\u202F\u205F]+", "", content
    )
    content = re.sub(r"([^\xA0])\xA0([^\xA0])", r"\1 \2", content)

    if isRegEx:
        content = re.sub(before, after, content, flags=re.I | re.S)
    else:
        content = content.replace(before, after)

    try:
        print(
            api.replace(
                pageid=x["pageid"],
                text=content,
                suppressAbuseFilter=True,
                bot=True,
                minor=True,
                summary="文本替换：【" + before + "】→【" + after + "】",
                tags="Bot",
            )
        )
        break
    except KeyboardInterrupt:
        sys.exit(1)
    except BaseException as e:  # pylint: disable=broad-except
        print(e)

    print("Finished: " + str(x["pageid"]))
