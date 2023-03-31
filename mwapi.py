"""An alternative to pywikibot for connecting to MediaWiki API.

This module contains a class providing methods for establishing a connection to the API endpoint of a MW wiki. There are pre-defined methods for querying and editing, although custom invocation is also possible.

  Typical usage example:

  api = mwAPI("https://test.wikipedia.org/w/api.php")
  api.login("botusername", "botpassword")
"""
import re
import sys
import time

import requests


class APIError(Exception):
    def __init__(self, message, code=None):
        self.message = message
        self.code = code
        super().__init__("API Error: " + message)


class PageNotFoundError(APIError):
    def __init__(self, page):
        self.page = page
        super().__init__("Page not found: " + page, "missingtitle")


class PageNameError(APIError):
    def __init__(self, page):
        self.page = page
        super().__init__("Invalid page name: " + page, "invalidtitle")


class FormatError(Exception):
    def __init__(self):
        super().__init__("Response format not recognised")


class LoginError(Exception):
    def __init__(self):
        super().__init__("Not logged in")


class mwAPI:
    __s = requests.Session()

    url = None
    lgtoken = None
    token = None
    bot = False

    def __joinParam(self, names, params):
        # Convert list to string
        if isinstance(names, str):
            # Only one parameter needs to be converted
            names = [names]

        for name in names:
            if name in params and isinstance(params[name], list):
                params[name] = "|".join(params[name])

    def __checkPage(self, page, pageid):
        if page is None and pageid is None:
            raise TypeError("No page or pageid specified")

        if page is not None and pageid is not None:
            raise APIError("Both page and pageid specified", "invalidparammix")

    def __init__(self, url=None, proxies=None):
        # Define API endpoint
        self.url = url
        if isinstance(proxies, str):
            proxies = {
                "http": proxies,
                "https": proxies,
            }
        self.__s.proxies = proxies

    def post(self, params, timeout=None):
        params.update({"format": "json"})

        r = None
        while not r:
            try:
                r = self.__s.post(self.url, data=params, timeout=timeout)
                r.encoding = r.apparent_encoding
                r.raise_for_status()
                r = r.json()
            except requests.exceptions.Timeout:
                pass
            except requests.exceptions.HTTPError:
                print(r.text, file=sys.stderr)
                raise

        return r

    def get(self, params, timeout=None):
        params.update({"format": "json"})

        r = None
        while not r:
            try:
                r = self.__s.get(self.url, params=params, timeout=timeout)
                r.encoding = r.apparent_encoding
                r.raise_for_status()
                r = r.json()
            except requests.exceptions.Timeout:
                pass
            except requests.exceptions.HTTPError:
                print(r.text, file=sys.stderr)
                raise

        return r

    def query(self, params):
        params.update(
            {
                "action": "query",
            }
        )
        return self.get(params)

    def getContent(self, page=None, *, pageid=None, redirects=True):
        self.__checkPage(page, pageid)

        params = {
            "prop": "revisions",
            "titles": page,
            "pageids": pageid,
            "rvprop": "content",
            "rvslots": "*",
            "redirects": redirects,
            "converttitles": 1,
        }
        r = self.query(params)
        r = list(r["query"]["pages"].values())[0]
        if "revisions" in r:
            r = r["revisions"][0]
            if "slots" in r:
                return r["slots"]["main"]["*"]
            elif "*" in r:
                return r["*"]
            else:
                raise FormatError
        else:
            if "missing" in r:
                raise PageNotFoundError(page or pageid)
            if "invalid" in r:
                raise PageNameError(page or pageid)

    def listContribs(
        self, username=None, start=None, end=None, *, recursive=True, **kwargs
    ):
        userid = kwargs.get("userid", None)
        userprefix = kwargs.get("userprefix", None)
        if username is None and userid is None and userprefix is None:
            # No username, userid or userprefix specified
            raise TypeError("No username, userid or userprefix specified")

        params = {"uclimit": "max"}
        params.update(kwargs)
        params.update(
            {"list": "usercontribs", "ucuser": username, "ucstart": start, "ucend": end}
        )
        r = self.query(params)

        res = r["query"]["usercontribs"]
        if recursive and "continue" in r:
            kwargs["uccontinue"] = r["continue"]["uccontinue"]
            t = self.listContribs(username, start, end, **kwargs)
            res = t + res if kwargs.get("ucdir", None) == "newer" else res + t

        return res

    def listCategoryMembers(
        self, category=None, *, pageid=None, recursive=True, **kwargs
    ):
        self.__checkPage(category, pageid)

        if category is not None:
            category = (
                category
                if re.match(r"^\[\[(?:Category|分[类類]|cat)\:", category, re.I)
                else "Category:" + category
            )

        params = {"cmlimit": "max"}
        params.update(kwargs)
        params.update(
            {"list": "categorymembers", "cmtitle": category, "cmpageid": pageid}
        )
        self.__joinParam(["cmprop", "cmnamespace", "cmtype"], params)
        r = self.query(params)

        res = r["query"]["categorymembers"]
        if recursive and "continue" in r:
            kwargs["cmcontinue"] = r["continue"]["cmcontinue"]
            res = res + self.listCategoryMembers(category, pageid=pageid, **kwargs)

        return res

    def search(self, query, *, recursive=True, **kwargs):
        params = {"srlimit": "max"}
        params.update(kwargs)
        params.update({"list": "search", "srsearch": query})
        self.__joinParam(["srnamespace", "srinfo", "srprop"], params)
        r = self.query(params)

        res = r["query"]["search"]
        if recursive and "continue" in r:
            kwargs["sroffset"] = r["continue"]["sroffset"]
            res = res + self.search(query, **kwargs)

        return res

    def whatLinksHere(self, page=None, *, pageid=None, recursive=True, **kwargs):
        self.__checkPage(page, pageid)

        params = {"bllimit": "max"}
        params.update(kwargs)
        params.update({"list": "backlinks", "bltitle": page, "blpageid": pageid})
        self.__joinParam("blnamespace", params)
        r = self.query(params)
        res = r["query"]["backlinks"]
        if recursive and "continue" in r:
            kwargs["blcontinue"] = r["continue"]["blcontinue"]
            res = res + self.whatLinksHere(page, pageid=pageid, **kwargs)

        return res

    def fileUsage(self, page=None, *, pageid=None, recursive=True, **kwargs):
        self.__checkPage(page, pageid)

        params = {"fulimit": "max"}
        params.update(kwargs)
        params.update({"prop": "fileusage", "titles": page, "pageids": pageid})
        self.__joinParam(["fuprop", "funamespace", "fushow"], params)
        r = self.query(params)
        res = r["query"]["pages"]
        if recursive and "continue" in r:
            kwargs["fucontinue"] = r["continue"]["fucontinue"]
            res = res + self.fileUsage(page, pageid=pageid, **kwargs)

        return res

    def login(self, username, password):
        # Get login token
        params = {"meta": "tokens", "type": "login"}
        r = self.query(params)
        self.lgtoken = r["query"]["tokens"]["logintoken"]

        # POST login request
        params = {
            "action": "login",
            "lgname": username,
            "lgpassword": password,
            "lgtoken": self.lgtoken,
        }
        r = self.post(params)

        if r["login"]["result"] != "Success":
            raise APIError(r["login"]["reason"], r["login"]["reason"])

        # Get CSRF token and bot info
        params = {"meta": "tokens|userinfo", "uiprop": "groups"}
        r = self.query(params)
        self.token = r["query"]["tokens"]["csrftoken"]
        self.bot = "bot" in r["query"]["userinfo"]["groups"]

    def connectWithConfig(self, path, site, login=True):
        with open(path, "r") as f:
            PW = eval(f.read())
        self.url = PW[site][0]
        if login:
            self.login(PW[site][1], PW[site][2])

    def loginWithConfig(self, path, site):
        self.connectWithConfig(path, site, login=True)

    def edit(
        self,
        page=None,
        *,
        pageid=None,
        suppressAbuseFilter=False,
        timeout=0.5,
        **kwargs
    ):
        if self.token is None:
            raise LoginError

        self.__checkPage(page, pageid)

        # Retrieve a timestamp for the base revision to prevent edit conflict
        params = {
            "prop": "revisions",
            "titles": page,
            "pageids": pageid,
            "rvprop": "timestamp",
            "rvslots": "*",
        }
        r = self.query(params)

        base = list(r["query"]["pages"].values())[0]
        if "revisions" in base:
            base = base["revisions"][0]["timestamp"]
        else:
            base = None

        params = {"bot": self.bot}
        params.update(kwargs)
        params.update(
            {
                "action": "edit",
                "title": page,
                "pageid": pageid,
                "token": self.token,
                "basetimestamp": base,
                "starttimestamp": int(time.time()),
            }
        )
        self.__joinParam("tags", params)
        r = self.post(params, timeout)

        if "error" in r:
            code = r["error"]["code"]
            if code == "missingtitle":
                raise PageNotFoundError(page or pageid)
            if code == "invalidtitle":
                raise PageNameError(page or pageid)
            raise APIError(r["error"]["info"], code)

        if r["edit"]["result"] == "Failure":
            if r["edit"]["code"] == "abusefilter-warning" and suppressAbuseFilter:
                self.edit(page, suppressAbuseFilter=suppressAbuseFilter, **kwargs)
            else:
                raise APIError(r["edit"]["info"], r["edit"]["code"])
        elif r["edit"]["result"] == "Success":
            return r["edit"]

    def replace(self, page=None, text=None, *, suppressAbuseFilter=False, **kwargs):
        return self.edit(
            page, text=text, suppressAbuseFilter=suppressAbuseFilter, **kwargs
        )

    def append(self, page=None, text=None, *, suppressAbuseFilter=False, **kwargs):
        return self.edit(
            page, appendtext=text, suppressAbuseFilter=suppressAbuseFilter, **kwargs
        )

    def prepend(self, page=None, text=None, *, suppressAbuseFilter=False, **kwargs):
        return self.edit(
            page, prependtext=text, suppressAbuseFilter=suppressAbuseFilter, **kwargs
        )

    def addSection(
        self, page=None, title=None, text=None, *, suppressAbuseFilter=False, **kwargs
    ):
        return self.edit(
            page,
            section="new",
            sectiontitle=title,
            text=text,
            suppressAbuseFilter=suppressAbuseFilter,
            **kwargs
        )

    def replaceTop(self, page=None, text=None, *, suppressAbuseFilter=False, **kwargs):
        return self.edit(
            page,
            section=0,
            text=text,
            suppressAbuseFilter=suppressAbuseFilter,
            **kwargs
        )

    def move(
        self,
        before=None,
        after=None,
        reason=None,
        *,
        beforeid=None,
        talk=True,
        subpages=True,
        redirect=False,
        **kwargs
    ):
        if self.token is None:
            raise LoginError

        self.__checkPage(before, beforeid)
        if after is None:
            raise TypeError("No page name specified for the destination")

        params = kwargs
        params.update(
            {
                "action": "move",
                "from": before,
                "fromid": beforeid,
                "to": after,
                "reason": reason,
                "movetalk": talk,
                "movesubpages": subpages,
                "noredirect": (not redirect),
                "token": self.token,
            }
        )
        self.__joinParam("tags", params)
        r = self.post(params, 0.5)

        if "error" in r:
            code = r["error"]["code"]
            if code == "missingtitle":
                raise PageNotFoundError(before or beforeid)
            if code == "invalidtitle":
                raise PageNameError(before or beforeid)
            raise APIError(r["error"]["info"], code)
        else:
            return r["move"]
