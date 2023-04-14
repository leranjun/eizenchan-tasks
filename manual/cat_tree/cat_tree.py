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
    title, id = q.popleft()
    pages = api.list_category_members(pageid=id, cmprop="ids|title|type")
    subcats = []
    subpage = 0
    for page in pages:
        if page["type"] == "subcat":
            q.append((page["title"], page["pageid"]))
            subcats.append(page["pageid"])
        else:
            subpage += 1
    output[id] = {"title": title, "subcats": subcats, "subpage": subpage}

# save output to JSON file
with open("cat-tree.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False)
