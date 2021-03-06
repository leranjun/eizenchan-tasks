import re
import sys
import traceback
from mwapi import mwAPI

with open("passwords.py", "r") as f:
    PW = eval(f.read())

with open("config.py", "r") as f:
    CONFIG = eval(f.read())

site = CONFIG["site"]

api = mwAPI(PW[site][0])
api.login(PW[site][1], PW[site][2])
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
    content = api.getContent(pageid=x["pageid"])

    # Remove random unicode character
    content = re.sub(
        r"[\u1680\u180E\u2000-\u200B\u200E\u200F\u2028-\u202F\u205F]+", "", content)
    content = re.sub(r"([^\xA0])\xA0([^\xA0])", r"\1 \2", content)

    if isRegEx:
        content = re.sub(before, after, content, flags=re.I | re.S)
    else:
        content = content.replace(before, after)

    # time.sleep(5)
    while True:
        try:
            print(api.replace(pageid=x["pageid"],
                              text=content,
                              suppressAbuseFilter=True,
                              bot=True,
                              minor=True,
                              summary="文本替换：【" + before + "】→【" + after +
                              "】",
                              tags="Bot"))
            break
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            traceback.print_exc()

    print("Finished: " + str(x["pageid"]))
