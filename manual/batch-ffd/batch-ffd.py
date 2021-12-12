from mwapi import mwAPI

print("Logging in...")
with open("passwords.py") as f:
    CONFIG = eval(f.read())

api = mwAPI(CONFIG["cm"][0])
api.login(CONFIG["cm"][1], CONFIG["cm"][2])
print("Logged in.")

print("Opening list of pages...")
jobs = []
with open("pages.txt") as f:
    jobs = list(page for page in (p.strip() for p in f) if page)

print(jobs)
print("Got list of pages.")

with open("error.log", "w") as f:
    for page in jobs:
        print("Working on " + page + "...")
        # zhapi = mwAPI(CONFIG["zh"][0])
        # fu = zhapi.fileUsage(page)
        # print(fu)
        # if "known" not in fu["-1"]:
        #     print(page + "does not exist, skipping...")
        #     f.write(page + ": missing\n")
        #     continue
        # if "fileusage" in fu["-1"]:
        #     print(page + "has backlinks, skipping...")
        #     f.write(page + "backlinks\n")
        #     continue
        print("Flagging " + page + " for deletion...")
        api.replace(page, text=r"<noinclude>{{即将删除|代U:Leranjun挂删：用户私人文件|user=Eizenchan}}</noinclude>",
                    bot=True, summary="挂删：用户私人文件", tags="Bot", nocreate=True)
        print("Finished " + page + ".")

