"""An alternative to pywikibot for connecting to MediaWiki API.

This module contains a class providing methods for establishing
a connection to the API endpoint of a MW wiki.
There are pre-defined methods for querying and editing, although
custom invocation is also possible.

  Typical usage example:

  api = MwApi("https://test.wikipedia.org/w/api.php")
  api.login("botusername", "botpassword")
"""

import ast
import re
import sys
import time
from os import PathLike
from typing import Any, Optional, cast

import requests

APIDict = dict[str, Any]
FileDescriptorOrPath = int | str | bytes | PathLike[str] | PathLike[bytes]


class APIError(Exception):
    """Base class for API errors."""

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        self.message = message
        self.code = code
        super().__init__("API Error: " + message)


class PageNotFoundError(APIError):
    """Raised when a page is not found."""

    def __init__(self, page: Optional[str | int]) -> None:
        self.page = page
        super().__init__("Page not found: " + str(page), "missingtitle")


class PageNameError(APIError):
    """Raised when a page name is invalid."""

    def __init__(self, page: Optional[str | int]) -> None:
        self.page = page
        super().__init__("Invalid page name: " + str(page), "invalidtitle")


class FormatError(Exception):
    """Raised when the response format is not recognised."""

    def __init__(self) -> None:
        super().__init__("Response format not recognised")


class LoginError(Exception):
    """Raised when login fails."""

    def __init__(self) -> None:
        super().__init__("Not logged in")


class MwApi:
    """A class for connecting to MediaWiki API."""

    __s = requests.Session()

    url = None
    lgtoken = None
    token = None
    bot = False

    @staticmethod
    def __join_param(names: str | list[str], params: dict[str, str]) -> None:
        # Convert list to string
        if isinstance(names, str):
            # Only one parameter needs to be converted
            names = [names]

        for name in names:
            if name in params and isinstance(params[name], list):
                params[name] = "|".join(params[name])

    @staticmethod
    def __check_page(page: Optional[str], pageid: Optional[int]) -> None:
        """Check if page or pageid is specified."""
        if page is None and pageid is None:
            raise TypeError("No page or pageid specified")

        if page is not None and pageid is not None:
            raise APIError("Both page and pageid specified", "invalidparammix")

    def __init__(
        self, url: Optional[str] = None, proxies: Optional[dict[str, str]] = None
    ) -> None:
        # Define API endpoint
        self.url = url
        if isinstance(proxies, str):
            proxies = {
                "http": proxies,
                "https": proxies,
            }
        if proxies:
            self.__s.proxies.update(proxies)

    def post(self, params: APIDict, timeout: Optional[int | float] = None) -> APIDict:
        """Send a POST request to the API endpoint."""
        if not self.url:
            raise TypeError("No API endpoint specified")

        params.update({"format": "json"})

        rsp = None
        res: APIDict = {}
        while not rsp:
            try:
                rsp = self.__s.post(self.url, data=params, timeout=timeout)
                rsp.encoding = rsp.apparent_encoding
                rsp.raise_for_status()
                res = rsp.json()
            except requests.exceptions.Timeout:
                pass
            except requests.exceptions.HTTPError:
                if rsp:
                    print(rsp.text, file=sys.stderr)
                else:
                    print("No response", file=sys.stderr)
                raise

        return res

    def get(self, params: APIDict, timeout: Optional[int | float] = None) -> APIDict:
        """Send a GET request to the API endpoint."""
        if not self.url:
            raise TypeError("No API endpoint specified")

        params.update({"format": "json"})

        rsp = None
        res: APIDict = {}
        while not rsp:
            try:
                rsp = self.__s.get(self.url, params=params, timeout=timeout)
                rsp.encoding = rsp.apparent_encoding
                rsp.raise_for_status()
                res = rsp.json()
            except requests.exceptions.Timeout:
                pass
            except requests.exceptions.HTTPError:
                if rsp:
                    print(rsp.text, file=sys.stderr)
                else:
                    print("No response", file=sys.stderr)
                raise

        return res

    def query(self, params: APIDict) -> APIDict:
        """Send a query request to the API endpoint."""
        params.update(
            {
                "action": "query",
            }
        )
        return self.get(params)

    def get_content(
        self,
        page: Optional[str] = None,
        *,
        pageid: Optional[int] = None,
        redirects: bool = True
    ) -> Optional[str]:
        """Get the content of a page."""
        self.__check_page(page, pageid)

        params = {
            "prop": "revisions",
            "titles": page,
            "pageids": pageid,
            "rvprop": "content",
            "rvslots": "*",
            "redirects": redirects,
            "converttitles": 1,
        }
        res = self.query(params)
        res = list(res["query"]["pages"].values())[0]
        if "revisions" in res:
            res = res["revisions"][0]
            if "slots" in res:
                return str(res["slots"]["main"]["*"])
            if "*" in res:
                return str(res["*"])
            raise FormatError
        if "missing" in res:
            raise PageNotFoundError(page or pageid)
        if "invalid" in res:
            raise PageNameError(page or pageid)
        return None

    def list_contribs(
        self,
        username: Optional[str] = None,
        start: Optional[str | int] = None,
        end: Optional[str | int] = None,
        *,
        recursive: bool = True,
        **kwargs: Any
    ) -> list[APIDict]:
        """Get a list of contributions of a user."""
        userid = kwargs.get("userid")
        userprefix = kwargs.get("userprefix")
        if username is None and userid is None and userprefix is None:
            # No username, userid or userprefix specified
            raise TypeError("No username, userid or userprefix specified")

        params: APIDict = {"uclimit": "max"}
        params.update(kwargs)
        params.update(
            {"list": "usercontribs", "ucuser": username, "ucstart": start, "ucend": end}
        )
        res = self.query(params)

        ret: list[APIDict] = res["query"]["usercontribs"]
        if recursive and "continue" in res:
            kwargs["uccontinue"] = res["continue"]["uccontinue"]
            temp = self.list_contribs(username, start, end, **kwargs)
            ret = temp + ret if kwargs.get("ucdir") == "newer" else ret + temp

        return ret

    def list_category_members(
        self,
        category: Optional[str] = None,
        *,
        pageid: Optional[int] = None,
        recursive: bool = True,
        **kwargs: Any
    ) -> list[APIDict]:
        """Get a list of pages in a category."""
        self.__check_page(category, pageid)

        if category is not None:
            category = (
                category
                if re.match(r"^\[\[(?:Category|分[类類]|cat)\:", category, re.I)
                else "Category:" + category
            )

        params: APIDict = {"cmlimit": "max"}
        params.update(kwargs)
        params.update(
            {"list": "categorymembers", "cmtitle": category, "cmpageid": pageid}
        )
        self.__join_param(["cmprop", "cmnamespace", "cmtype"], params)
        res = self.query(params)

        ret: list[APIDict] = res["query"]["categorymembers"]
        if recursive and "continue" in res:
            kwargs["cmcontinue"] = res["continue"]["cmcontinue"]
            ret = ret + self.list_category_members(category, pageid=pageid, **kwargs)

        return ret

    def search(
        self, query: str, *, recursive: bool = True, **kwargs: Any
    ) -> list[APIDict]:
        """Search for pages."""
        params = {"srlimit": "max"}
        params.update(kwargs)
        params.update({"list": "search", "srsearch": query})
        self.__join_param(["srnamespace", "srinfo", "srprop"], params)
        res = self.query(params)

        ret: list[APIDict] = res["query"]["search"]
        if recursive and "continue" in res:
            kwargs["sroffset"] = res["continue"]["sroffset"]
            ret = ret + self.search(query, **kwargs)

        return ret

    def what_links_here(
        self,
        page: Optional[str] = None,
        *,
        pageid: Optional[int] = None,
        recursive: bool = True,
        **kwargs: Any
    ) -> list[APIDict]:
        """Get a list of pages that link to a page."""
        self.__check_page(page, pageid)

        params: APIDict = {"bllimit": "max"}
        params.update(kwargs)
        params.update({"list": "backlinks", "bltitle": page, "blpageid": pageid})
        self.__join_param("blnamespace", params)
        res = self.query(params)
        ret: list[APIDict] = res["query"]["backlinks"]
        if recursive and "continue" in res:
            kwargs["blcontinue"] = res["continue"]["blcontinue"]
            ret = ret + self.what_links_here(page, pageid=pageid, **kwargs)

        return ret

    def file_usage(
        self,
        page: Optional[str] = None,
        *,
        pageid: Optional[int] = None,
        recursive: bool = True,
        **kwargs: Any
    ) -> list[APIDict]:
        """Get a list of pages that use a file."""
        self.__check_page(page, pageid)

        params: APIDict = {"fulimit": "max"}
        params.update(kwargs)
        params.update({"prop": "fileusage", "titles": page, "pageids": pageid})
        self.__join_param(["fuprop", "funamespace", "fushow"], params)
        res = self.query(params)
        ret: list[APIDict] = res["query"]["pages"]
        if recursive and "continue" in res:
            kwargs["fucontinue"] = res["continue"]["fucontinue"]
            ret = ret + self.file_usage(page, pageid=pageid, **kwargs)

        return ret

    def login(self, username: str, password: str) -> None:
        """Login to the wiki."""
        # Get login token
        params = {"meta": "tokens", "type": "login"}
        res = self.query(params)
        self.lgtoken = res["query"]["tokens"]["logintoken"]

        # POST login request
        params = {
            "action": "login",
            "lgname": username,
            "lgpassword": password,
            "lgtoken": self.lgtoken,
        }
        res = self.post(params)

        if res["login"]["result"] != "Success":
            raise APIError(res["login"]["reason"], res["login"]["reason"])

        # Get CSRF token and bot info
        params = {"meta": "tokens|userinfo", "uiprop": "groups"}
        res = self.query(params)
        self.token = res["query"]["tokens"]["csrftoken"]
        self.bot = "bot" in res["query"]["userinfo"]["groups"]

    def connect_with_config(
        self, path: FileDescriptorOrPath, site: str, login: bool = True
    ) -> None:
        """Connect to a wiki using a config file."""
        with open(path, "r", encoding="utf-8") as config_file:
            config = ast.literal_eval(config_file.read())
        self.url = config[site][0]
        if login:
            self.login(config[site][1], config[site][2])

    def login_with_config(self, path: FileDescriptorOrPath, site: str) -> None:
        """Login to a wiki using a config file."""
        self.connect_with_config(path, site, login=True)

    def edit(
        self,
        page: Optional[str] = None,
        *,
        pageid: Optional[int] = None,
        suppressAbuseFilter: bool = False,
        timeout: int | float = 0.5,
        **kwargs: Any
    ) -> APIDict | None:
        """Edit a page."""
        if self.token is None:
            raise LoginError

        self.__check_page(page, pageid)

        # Retrieve a timestamp for the base revision to prevent edit conflict
        params: APIDict = {
            "prop": "revisions",
            "titles": page,
            "pageids": pageid,
            "rvprop": "timestamp",
            "rvslots": "*",
        }
        res = self.query(params)

        base = list(res["query"]["pages"].values())[0]
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
        self.__join_param("tags", params)
        res = self.post(params, timeout)

        if "error" in res:
            code = res["error"]["code"]
            if code == "missingtitle":
                raise PageNotFoundError(page or pageid)
            if code == "invalidtitle":
                raise PageNameError(page or pageid)
            raise APIError(res["error"]["info"], code)

        if res["edit"]["result"] == "Failure":
            if res["edit"]["code"] == "abusefilter-warning" and suppressAbuseFilter:
                self.edit(page, suppressAbuseFilter=suppressAbuseFilter, **kwargs)
            else:
                raise APIError(res["edit"]["info"], res["edit"]["code"])
        elif res["edit"]["result"] == "Success":
            return cast(APIDict, res["edit"])
        return None

    def replace(
        self,
        page: Optional[str] = None,
        text: Optional[str] = None,
        *,
        suppressAbuseFilter: bool = False,
        **kwargs: Any
    ) -> APIDict | None:
        """Replace the content of a page."""
        return self.edit(
            page, text=text, suppressAbuseFilter=suppressAbuseFilter, **kwargs
        )

    def append(
        self,
        page: Optional[str] = None,
        text: Optional[str] = None,
        *,
        suppressAbuseFilter: bool = False,
        **kwargs: Any
    ) -> APIDict | None:
        """Append text to a page."""
        return self.edit(
            page, appendtext=text, suppressAbuseFilter=suppressAbuseFilter, **kwargs
        )

    def prepend(
        self,
        page: Optional[str] = None,
        text: Optional[str] = None,
        *,
        suppressAbuseFilter: bool = False,
        **kwargs: Any
    ) -> APIDict | None:
        """Prepend text to a page."""
        return self.edit(
            page, prependtext=text, suppressAbuseFilter=suppressAbuseFilter, **kwargs
        )

    def add_section(
        self,
        page: Optional[str] = None,
        title: Optional[str] = None,
        text: Optional[str] = None,
        *,
        suppressAbuseFilter: bool = False,
        **kwargs: Any
    ) -> APIDict | None:
        """Add a new section to a page."""
        return self.edit(
            page,
            section="new",
            sectiontitle=title,
            text=text,
            suppressAbuseFilter=suppressAbuseFilter,
            **kwargs
        )

    def replace_top(
        self,
        page: Optional[str] = None,
        text: Optional[str] = None,
        *,
        suppressAbuseFilter: bool = False,
        **kwargs: Any
    ) -> APIDict | None:
        """Replace the top section of a page."""
        return self.edit(
            page,
            section=0,
            text=text,
            suppressAbuseFilter=suppressAbuseFilter,
            **kwargs
        )

    def move(
        self,
        before: Optional[str] = None,
        after: Optional[str] = None,
        reason: Optional[str] = None,
        *,
        beforeid: Optional[int] = None,
        talk: bool = True,
        subpages: bool = True,
        redirect: bool = False,
        **kwargs: Any
    ) -> APIDict | None:
        """Move a page."""
        if self.token is None:
            raise LoginError

        self.__check_page(before, beforeid)
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
        self.__join_param("tags", params)
        res = self.post(params, 0.5)

        if "error" in res:
            code = res["error"]["code"]
            if code == "missingtitle":
                raise PageNotFoundError(before or beforeid)
            if code == "invalidtitle":
                raise PageNameError(before or beforeid)
            raise APIError(res["error"]["info"], code)
        return cast(APIDict, res["move"])
