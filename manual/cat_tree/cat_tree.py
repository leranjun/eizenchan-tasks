"""Get the category tree of a category."""
import json
from collections import deque

from mwapi import MwApi

api = MwApi()
api.login_with_config("passwords.py", "zh")
print("Logged in")

ROOT = "追踪分类"
ROOT_ID = 176083

output = {}
q = deque([(ROOT, ROOT_ID)])
while q:
    title, pageid = q.popleft()
    pages = api.list_category_members(pageid=pageid, cmprop="ids|title|type")
    subcats = []
    SUBPAGE = 0
    for page in pages:
        if page["type"] == "subcat":
            q.append((page["title"], page["pageid"]))
            subcats.append(page["pageid"])
        else:
            SUBPAGE += 1
    output[pageid] = {"title": title, "subcats": subcats, "subpage": SUBPAGE}

# save output to JSON file
with open("cat-tree.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False)
