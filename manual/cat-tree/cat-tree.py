from mwapi import mwAPI
from collections import deque
import json

api = mwAPI(proxies="http://127.0.0.1:7890")
api.loginWithConfig("passwords.py", "zh")
print("Logged in")

ROOT = "追踪分类"
ROOT_ID = 176083

output = {}
q = deque([(ROOT, ROOT_ID)])
while q:
    title, id = q.popleft()
    pages = api.listCategoryMembers(pageid=id, cmprop="ids|title|type")
    subcats = []
    subpage = 0
    for page in pages:
        if page["type"] == "subcat":
            q.append((page["title"], page["pageid"]))
            subcats.append(page["pageid"])
        else:
            subpage += 1
    output[id] = {
        "title": title,
        "subcats": subcats,
        "subpage": subpage
    }

# save output to JSON file
with open("cat-tree.json", "w") as f:
    json.dump(output, f, ensure_ascii=False)
