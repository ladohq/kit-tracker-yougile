#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Yougile from the command line: REST API v2, a bearer API key.

Commands: search, get, create, edit, transition, comment, assign, label, link, whoami
(run with --help). Credentials come from YOUGILE_API_KEY and YOUGILE_URL (optional, default
https://yougile.com, or a self-hosted Yougile's address); the key is never printed.
Tasks are named by the key people see (idTaskProject, e.g. DEV-484), the company-wide
number (idTaskCommon, e.g. ID-484) or their id; tasks of other boards are not found.
Text sent to Yougile is Markdown, converted to HTML; get shows a description's HTML as
Markdown again. Project settings come from .lado/tracker.yaml, found from the current
directory up to the repository root.
Python standard library only, run by `uv run --script`.
"""

import argparse
import html
import html.parser
import http.client
import json
import os
import re
import shlex
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Exit codes, one per kind of failure; SKILL.md tells the agent what to do on each.
OK = 0
USAGE = 2
CONFIG = 3
SETUP = 4
KEY_REFUSED = 5
NO_ACCESS = 6
NOT_FOUND = 7
UNREACHABLE = 9
TLS = 10
REFUSED = 11
SERVER_ERROR = 12

TIMEOUT = 30
PAGE = 1000  # the API's largest page
RATE_WAIT = 60  # the API allows 50 requests a minute per company
DEFAULT_URL = "https://yougile.com"
LOOPBACK = ("127.0.0.1", "localhost", "::1")
UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                  r"[0-9a-fA-F]{12}$")
APPLIED = ("; the change may have been applied: once Yougile answers again, check with "
           "get before running it again")
# Yougile answered a 5xx, so nobody will say it answers again: check before running again.
APPLIED_ANSWERED = "; the change may have been applied: check with get before running it again"
STOP_ALL = ("; the lead tells every agent to stop using Yougile until the human sets a new "
            "key in YOUGILE_API_KEY and restarts the session")
WAIT = "; send Yougile nothing more until you are told it answers again"
NOT_YOUGILE = ("the answer is not Yougile's API: YOUGILE_URL is not Yougile's address "
               "(https://yougile.com, or your self-hosted Yougile's)")
CONFIG_PATH = os.path.join(".lado", "tracker.yaml")
CONFIG_MAPS = ("statuses", "labels")
CONFIG_KEYS = ("board",) + CONFIG_MAPS


class Failure(Exception):
    """One plain line for the user and the exit code of its kind."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = None  # the HTTP status of a refused request


# --- .lado/tracker.yaml: a strict YAML subset ------------------------------------------


def _strip_comment(line):
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'" and line[:i].rstrip()[-1:] in (":", "[", ","):
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _scalar(text, where):
    text = text.strip()
    if text[:1] in "\"'":
        if len(text) < 2 or text[-1] != text[0]:
            raise ValueError(where + "a quoted value must end with the same quote")
        return text[1:-1]
    if text[:1] in "{&*!|>":
        raise ValueError(where + "write a plain value: flow maps, anchors, tags and block "
                                 "text are not supported")
    return text


NO_LISTS = "lists are not supported: every value is one plain value"


def _value(text, where):
    text = text.strip()
    if text.startswith("["):
        raise ValueError(where + NO_LISTS)
    return _scalar(text, where)


def parse_config(text, path):
    """Parse the subset: `key: value`, one level of nested maps, `#` comments."""
    data = {}
    lines = {}
    section = None
    indent = None
    for number, raw in enumerate(text.splitlines(), 1):
        where = "%s line %d: " % (path, number)
        if "\t" in raw[:len(raw) - len(raw.lstrip())]:
            raise ValueError(where + "indent with spaces, not tabs")
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        depth = len(line) - len(line.lstrip(" "))
        body = line.strip()
        if body.startswith("- "):
            raise ValueError(where + NO_LISTS)
        if body in ("---", "..."):
            raise ValueError(where + "one document only; remove '%s'" % body)
        key, colon, rest = body.partition(":")
        key = key.strip()
        if not colon or not key or (rest and not rest.startswith(" ")):
            raise ValueError(where + "expected 'key: value'")
        if depth == 0:
            if key in data:
                raise ValueError(where + "'%s' is given twice" % key)
            lines[key] = number
            if rest.strip():
                data[key] = _value(rest, where)
                section = None
            else:
                data[key] = {}
                section, indent = key, None
            continue
        if section is None:
            raise ValueError(where + "unexpected indent")
        if indent is None:
            indent = depth
        if depth != indent:
            raise ValueError(where + "only one level of nesting; indent like the line above")
        if not rest.strip():
            raise ValueError(where + "'%s' needs a value (only one level of nesting)" % key)
        if key in data[section]:
            raise ValueError(where + "'%s' is given twice in '%s'" % (key, section))
        data[section][key] = _value(rest, where)
        lines[section + "." + key] = number
    return _validate(data, path, lines)


def _validate(data, path, lines):
    def where(key):
        return "%s line %d: " % (path, lines[key]) if key in lines else path + ": "
    for key in data:
        if key not in CONFIG_KEYS:
            raise ValueError(where(key) + "unknown key '%s'; known keys: %s"
                             % (key, ", ".join(CONFIG_KEYS)))
    if not isinstance(data.get("board"), str) or not data.get("board"):
        raise ValueError(where("board") + "'board' (the board's id, or its title) is "
                                          "required")
    for key in CONFIG_MAPS:
        value = data.setdefault(key, {})
        if not isinstance(value, dict):
            raise ValueError(where(key) + "'%s' must be a map of 'name: value' lines" % key)
        for name, item in value.items():
            if not isinstance(item, str) or not item:
                raise ValueError(where(key + "." + name) + "'%s.%s' must be one plain value"
                                 % (key, name))
    for name, item in data["labels"].items():
        sticker, _, state = item.rpartition(":")
        if not sticker.strip() or not state.strip():
            raise ValueError(where("labels." + name) + "'labels.%s' must be 'Sticker: State',"
                                                       " e.g. 'Release: Waiting'" % name)
    return data


def find_config(start):
    """Return the path of .lado/tracker.yaml from start up to the repository root."""
    here = os.path.abspath(start)
    while True:
        candidate = os.path.join(here, CONFIG_PATH)
        if os.path.isfile(candidate):
            return candidate
        if os.path.exists(os.path.join(here, ".git")):
            return None
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def load_config():
    path = find_config(os.getcwd())
    if path is None:
        raise Failure(CONFIG, "%s not found from %s up to the repository root: create it "
                              "with at least 'board: <board id or title>'"
                      % (CONFIG_PATH, os.getcwd()))
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        return parse_config(text, path)
    except (OSError, UnicodeDecodeError) as error:
        raise Failure(CONFIG, "%s cannot be read: %s" % (path, error))
    except ValueError as error:
        raise Failure(CONFIG, str(error))


def sticker_state(config, word):
    """The (sticker name, state name) a label word maps to; exit 3 when it maps none."""
    value = config["labels"].get(word)
    if not value:
        known = ", ".join(sorted(config["labels"])) or "none"
        raise Failure(CONFIG, "label '%s' is not in 'labels' of %s (its words: %s); the "
                              "user maps it to 'Sticker: State' there" % (word, CONFIG_PATH,
                                                                          known))
    sticker, _, state = value.rpartition(":")
    return sticker.strip(), state.strip()


# --- HTTP ------------------------------------------------------------------------------


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Yougile:
    def __init__(self):
        key = os.environ.get("YOUGILE_API_KEY", "").strip()
        if not key:
            raise Failure(SETUP, "YOUGILE_API_KEY not set: the user sets it in their login "
                                 "shell's profile, then starts a new session")
        self.base = (os.environ.get("YOUGILE_URL", "").strip() or DEFAULT_URL).rstrip("/")
        try:
            url = urllib.parse.urlsplit(self.base)
            url.port  # raises ValueError on a malformed port
        except ValueError:
            url = None
        if not url or not url.hostname:
            raise Failure(SETUP, "YOUGILE_URL is not a valid address (host, port): it must "
                                 "be Yougile's https:// address")
        # The key goes in every request: only over TLS, or to this machine (tests).
        if not (url.scheme == "https" or (url.scheme == "http" and url.hostname in LOOPBACK)):
            raise Failure(SETUP, "YOUGILE_URL must be Yougile's https:// address: the API "
                                 "key is sent with every request")
        self.auth = "Bearer " + key
        cafile = os.environ.get("SSL_CERT_FILE") or None
        try:
            context = ssl.create_default_context(cafile=cafile)
        except (OSError, ssl.SSLError) as error:
            raise Failure(TLS, "SSL_CERT_FILE (%s) cannot be read: %s; the user points it "
                               "to a file with the corporate CA" % (cafile, error))
        self.opener = urllib.request.build_opener(
            _NoRedirect, urllib.request.HTTPSHandler(context=context))
        self.users = {}
        self._board = None
        self._columns = None

    def call(self, method, path, query=None, body=None, missing=None):
        url = self.base + "/api-v2/" + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        for attempt in (1, 2):
            request = urllib.request.Request(url, data=data, method=method)
            request.add_header("Authorization", self.auth)
            request.add_header("Accept", "application/json")
            request.add_header("Content-Type", "application/json")
            try:
                with self.opener.open(request, timeout=TIMEOUT) as response:
                    raw = response.read()
                break
            except urllib.error.HTTPError as error:
                # A 429 is refused before it runs: wait once and send the same request again.
                if error.code == 429 and attempt == 1:
                    time.sleep(_retry_after(error.headers.get("Retry-After")))
                    continue
                failure = self._http_failure(error, method, missing)
                failure.status = error.code
                raise failure
            except urllib.error.URLError as error:
                raise self._network_failure(error.reason, method)
            except (socket.timeout, TimeoutError, ConnectionError, ssl.SSLError,
                    http.client.HTTPException) as error:
                raise self._network_failure(error, method)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except ValueError:
            raise Failure(SETUP, NOT_YOUGILE)

    def pages(self, path, query=None):
        """Every item of a paged list, page after page."""
        query = dict(query or {}, limit=PAGE, offset=0)
        items = []
        while True:
            result = self.call("GET", path, query) or {}
            content = result.get("content") or []
            items.extend(content)
            if not (result.get("paging") or {}).get("next") or not content:
                return items
            query["offset"] += len(content)

    @staticmethod
    def _network_failure(reason, method):
        if isinstance(reason, ssl.SSLError):
            why = getattr(reason, "reason", None) or type(reason).__name__
            return Failure(TLS, "TLS failed (%s): if Yougile's certificate is from a "
                                "corporate CA, set SSL_CERT_FILE to a file with that CA" % why)
        # A write that got no answer may still have been applied.
        after = WAIT + (APPLIED if method != "GET" else "")
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return Failure(UNREACHABLE, "Yougile did not answer in %d seconds: is the network "
                                        "(or the VPN) up?%s" % (TIMEOUT, after))
        return Failure(UNREACHABLE, "Yougile is not reachable (%s): is the network (or the "
                                    "VPN) up, and YOUGILE_URL right?%s"
                       % (type(reason).__name__, after))

    @staticmethod
    def _http_failure(error, method, missing):
        code = error.code
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except ValueError:
            payload = None
        is_api = isinstance(payload, dict)
        payload = payload if is_api else {}
        parts = []
        for name in ("message", "error"):
            value = payload.get(name)
            value = "; ".join(map(str, value)) if isinstance(value, list) else value
            if value and str(value) not in parts:
                parts.append(str(value))
        detail = ": " + "; ".join(parts) if parts else ""
        if code == 401:
            return Failure(KEY_REFUSED, "Yougile refused the API key (401): YOUGILE_API_KEY "
                                        "is wrong, deleted, or of another company; not "
                                        "retried" + STOP_ALL)
        if 300 <= code < 400:
            return Failure(SETUP, "Yougile answered with a redirect (%d), not followed: "
                                  "YOUGILE_URL is not Yougile's address, or a login page is "
                                  "in front of it" % code)
        if code == 404 and not is_api:
            return Failure(SETUP, NOT_YOUGILE)
        if code == 403:
            return Failure(NO_ACCESS, "no access (403)%s" % detail)
        if code == 404:
            return Failure(NOT_FOUND, missing or "not found (404)%s" % detail)
        if code == 429:
            return Failure(SERVER_ERROR, "Yougile is rate limiting requests (429) after a "
                                         "wait: nothing of this request was applied; report "
                                         "it")
        if code >= 500:
            # A proxy's 502/504 can follow an applied write.
            return Failure(SERVER_ERROR, "Yougile failed (%d)%s%s" % (
                code, detail, APPLIED_ANSWERED if method != "GET" else ""))
        return Failure(REFUSED, "Yougile refused the request (%d)%s" % (code, detail))

    # --- the board, its columns, tasks and people ------------------------------------

    def board(self, config):
        if self._board:
            return self._board
        wanted = config["board"]
        where = "'board: %s' in %s" % (wanted, CONFIG_PATH)
        if UUID.match(wanted):
            try:
                self._board = self.call("GET", "boards/" + wanted)
            except Failure as failure:
                if failure.code == NOT_FOUND:
                    raise Failure(CONFIG, "no board with the id of %s, or you do not see it"
                                  % where)
                raise
            return self._board
        found = [b for b in self.pages("boards", {"title": wanted})
                 if not b.get("deleted") and (b.get("title") or "").casefold()
                 == wanted.casefold()]
        if not found:
            raise Failure(CONFIG, "no board titled as in %s, or you do not see it" % where)
        if len(found) > 1:
            raise Failure(CONFIG, "several boards are titled as in %s; write the id of one: %s"
                          % (where, "; ".join("%s (%s)" % (b.get("id"), b.get("projectId"))
                                              for b in found)))
        self._board = found[0]
        return self._board

    def columns(self, config):
        """The board's columns, in the order the API lists them (the board's order)."""
        if self._columns is None:
            board = self.board(config)
            self._columns = [c for c in self.pages("columns", {"boardId": board["id"]})
                             if not c.get("deleted")]
        return self._columns

    def column(self, config, target):
        """A column of the board by its title, its id, or a word of `statuses`."""
        title = config["statuses"].get(target, target)
        columns = self.columns(config)
        match = [c for c in columns if c.get("id") in (target, title)]
        match = match or [c for c in columns
                          if (c.get("title") or "").casefold() == title.casefold()]
        if len(match) != 1:
            problem = ("is the title of several columns: write the id of one"
                       if match else "is not a column of the board")
            if target in config["statuses"]:
                raise Failure(CONFIG, "'statuses.%s: %s' in %s %s; its columns: %s; the "
                                      "user fixes the file" % (target, title, CONFIG_PATH,
                                                               problem, column_list(columns)))
            advice = ("" if match else "; to use this word, map it to a column in 'statuses' "
                      "of %s (its words: %s)" % (CONFIG_PATH,
                                                 ", ".join(config["statuses"]) or "none"))
            raise Failure(REFUSED, "status '%s' %s; its columns: %s%s"
                          % (target, problem, column_list(columns), advice))
        return match[0]

    def tasks(self, column_id, query=None):
        return [t for t in self.pages("task-list", dict(query or {}, columnId=column_id))
                if not t.get("deleted")]

    def task(self, config, key):
        """The task named by its key (DEV-484), its number (ID-484) or its id, on the board.

        One request: GET /tasks/{key} takes any of the three (tried on Yougile's cloud).
        """
        columns = self.columns(config)
        missing = "task %s not found on board '%s': check the key, or you may not see it" % (
            key, self.board(config).get("title"))
        task = self.call("GET", "tasks/" + urllib.parse.quote(key, safe=""),
                         missing=missing) or {}
        if task.get("deleted") or task.get("columnId") not in {c.get("id") for c in columns}:
            raise Failure(NOT_FOUND, missing)
        return task

    def person(self, user_id):
        """An account as 'Real Name (email)', comparable with whoami."""
        if not user_id:
            return "?"
        if user_id not in self.users:
            try:
                self.users[user_id] = self.call("GET", "users/" + user_id) or {}
            except Failure as failure:
                if failure.code != NOT_FOUND:
                    raise
                self.users[user_id] = {}
        return _person(self.users[user_id]) if self.users[user_id] else "unknown account " + \
            user_id

    def me(self):
        if "me" not in self.users:
            me = self.call("GET", "users/me") or {}
            self.users["me"] = me
            self.users[me.get("id")] = me
        return self.users["me"]

    def user_by(self, who):
        """The account id for 'me', an email, or None for 'none'."""
        if who == "none":
            return None
        if who == "me":
            return self.me().get("id")
        found = [u for u in self.pages("users", {"email": who})
                 if (u.get("email") or "").casefold() == who.casefold()]
        if not found:
            raise Failure(REFUSED, "no account with the email %s in the company: check the "
                                   "email; another account is never guessed" % who)
        self.users[found[0]["id"]] = found[0]
        return found[0]["id"]


def _retry_after(value):
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        seconds = RATE_WAIT
    return max(0, min(seconds, RATE_WAIT))


def _person(user):
    name, email = user.get("realName"), user.get("email")
    if name and email and name != email:
        return "%s (%s)" % (name, email)
    return email or name or "?"


def missing_task(key):
    return "task %s not found (404): check the key, or you may not see it" % key


def key_of(task):
    return task.get("idTaskProject") or task.get("id")


def column_name(column, columns):
    """The column's title, with its id when another column has the same title."""
    title = column.get("title") or "?"
    if sum((c.get("title") or "?").casefold() == title.casefold() for c in columns) > 1:
        return "%s (%s)" % (title, column.get("id"))
    return title


def column_list(columns):
    return ", ".join(column_name(c, columns) for c in columns) or "none"


# --- Markdown -> HTML: a minimal subset, the rest passes as text -----------------------

FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+#.-]*)\s*$")
HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
CODE_SPAN = re.compile(r"(`+)(.+?)\1")
# One level of balanced parentheses in the URL: [a](http://x/y_(z)).
LINK = re.compile(r"(?<!!)\[([^\]\n]+)\]\(((?:[^()\s]|\([^()\s]*\))+)\)")
BOLD = re.compile(r"(?<![\w*])\*\*(?=\S)(.+?)(?<=\S)\*\*(?![\w*])"
                  r"|(?<![\w_])__(?=\S)(.+?)(?<=\S)__(?![\w_])")
ITALIC = re.compile(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])"
                    r"|(?<![\w_])_(?=[^\s_])(.+?)(?<=[^\s_])_(?![\w_])")
SLOT = re.compile("\x00(\\d+)\x00")


def _inline(text):
    # Code spans and link targets are set aside first, so no markup is read inside them.
    slots = []

    def keep(value):
        slots.append(value)
        return "\x00%d\x00" % (len(slots) - 1)

    text = CODE_SPAN.sub(lambda m: keep("<code>%s</code>" % html.escape(m.group(2).strip())),
                         text)
    text = html.escape(text, quote=False)
    text = LINK.sub(lambda m: '<a href="%s">%s</a>' % (
        keep(html.escape(html.unescape(m.group(2)))), m.group(1)), text)
    text = BOLD.sub(lambda m: "<strong>%s</strong>" % (m.group(1) or m.group(2)), text)
    text = ITALIC.sub(lambda m: "<em>%s</em>" % (m.group(1) or m.group(2)), text)
    while SLOT.search(text):
        text = SLOT.sub(lambda m: slots[int(m.group(1))], text)
    return text


def _html(text):
    out = []
    paragraph = []
    lists = []  # (indent, "ul" or "ol") of the open list levels, each with an open <li>
    fence = None
    code = []

    def flush():
        if paragraph:
            out.append("<p>%s</p>" % "<br>".join(_inline(line.strip()) for line in paragraph))
            del paragraph[:]

    def close(level=0):
        while len(lists) > level:
            out.append("</li></%s>" % lists.pop()[1])

    for line in text.replace("\r\n", "\n").split("\n"):
        if fence:
            if line.strip().startswith(fence) and not line.strip().strip(fence[0]):
                out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(code)))
                fence, code = None, []
            else:
                code.append(line)
            continue
        if not line.strip():
            flush()  # a blank line ends a paragraph; a list goes on after it
            continue
        match = FENCE.match(line)
        if match:
            flush()
            close()
            fence = match.group(1)
            continue
        match = LIST_ITEM.match(line)
        if match:
            flush()
            indent = len(match.group(1).expandtabs(4))
            kind = "ol" if match.group(2)[0].isdigit() else "ul"
            while lists and lists[-1][0] > indent:
                close(len(lists) - 1)
            if lists and lists[-1][0] == indent and lists[-1][1] == kind:
                out.append("</li><li>")
            else:
                if lists and lists[-1][0] == indent:
                    close(len(lists) - 1)
                lists.append((indent, kind))
                out.append("<%s><li>" % kind)
            out.append(_inline(match.group(3)))
            continue
        close()
        match = HEADING.match(line)
        if match:
            flush()
            level = len(match.group(1))
            out.append("<h%d>%s</h%d>" % (level, _inline(match.group(2)), level))
        else:
            paragraph.append(line)
    flush()
    close()
    if fence:  # a block left open is closed at the end
        out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(code)))
    return "".join(out)


def plain_html(text):
    """The text escaped, as plain paragraphs."""
    blocks = [b for b in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()) if b]
    return "".join("<p>%s</p>" % html.escape(b).replace("\n", "<br>") for b in blocks)


def to_html(text):
    """Markdown to HTML; the text escaped as plain paragraphs if the conversion fails."""
    try:
        return _html(text)
    except Exception:
        return plain_html(text)


# --- HTML -> Markdown for get: the same subset back, other tags dropped, text kept ------

VOID = {"br", "img", "hr", "wbr", "input", "col", "area", "source", "meta", "link", "base"}
BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "ul", "ol", "li", "table",
         "thead", "tbody", "tfoot", "tr", "blockquote", "hr", "section", "article", "header",
         "footer", "figure"}
SKIP = {"script", "style", "head", "title", "template"}
TAG = re.compile(r"<[a-zA-Z!/]")


# A tag that starts closes the open tag HTML closes for it: <li> an open <li> of the same
# list, a block an open <p>, a cell an open cell of the same row, a row an open row.
IMPLIED = {"li": ({"li"}, {"ul", "ol"}), "td": ({"td", "th"}, {"tr", "table"}),
           "th": ({"td", "th"}, {"tr", "table"}), "tr": ({"tr"}, {"table"})}


class _Tree(html.parser.HTMLParser):
    """The HTML as a tree of (tag, attributes, children); entities decoded."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = ("", {}, [])
        self.open = [self.root]

    def _close(self, closes, stops):
        """Close the innermost open tag of `closes` unless one of `stops` is inside it."""
        for i in range(len(self.open) - 1, 0, -1):
            if self.open[i][0] in closes:
                del self.open[i:]
                return
            if self.open[i][0] in stops:
                return

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK:
            self._close({"p"}, BLOCK - {"p"})
        if tag in IMPLIED:
            self._close(*IMPLIED[tag])
        node = (tag, dict(attrs), [])
        self.open[-1][2].append(node)
        if tag not in VOID:
            self.open.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.open) - 1, 0, -1):
            if self.open[i][0] == tag:
                del self.open[i:]
                return

    def handle_data(self, data):
        self.open[-1][2].append(data)


def _wrap(mark, text):
    """Emphasis around the text, its outer spaces left outside."""
    core = text.strip()
    if not core:
        return text
    return "%s%s%s%s%s" % (text[:len(text) - len(text.lstrip())], mark, core, mark,
                           text[len(text.rstrip()):])


def _raw(node):
    """The text of a node as written (for code blocks); <br> is a line break."""
    if isinstance(node, str):
        return node
    if node[0] == "br":
        return "\n"
    return "".join(_raw(child) for child in node[2])


def _md_inline(node):
    if isinstance(node, str):
        return re.sub(r"\s+", " ", node)
    tag, attrs, children = node
    if tag in SKIP:
        return ""
    if tag == "br":
        return "\n"
    if tag == "img":
        return attrs.get("src") or ""
    if tag == "code":
        code = re.sub(r"\s+", " ", _raw(node)).strip()
        tick = "``" if "`" in code else "`"
        return "%s%s%s" % (tick, code, tick) if code else ""
    text = "".join(_md_inline(child) for child in children)
    if tag in ("strong", "b"):
        return _wrap("**", text)
    if tag in ("em", "i"):
        return _wrap("*", text)
    if tag == "a" and attrs.get("href"):
        return "[%s](%s)" % (text.strip(), attrs["href"]) if text.strip() else attrs["href"]
    return text


def _md_blocks(nodes):
    """Markdown blocks of the nodes: inline runs become paragraphs."""
    blocks, run = [], []

    def flush():
        lines = [line.strip() for line in "".join(run).split("\n")]
        text = "\n".join(lines).strip("\n")
        if text.strip():
            blocks.append(text)
        del run[:]

    for node in nodes:
        if isinstance(node, str) or node[0] not in BLOCK:
            run.append(_md_inline(node))
        else:
            flush()
            blocks.extend(_md_block(node))
    flush()
    return blocks


def _md_list(node):
    lines, number = [], 0
    for child in node[2]:
        if isinstance(child, str) and not child.strip():
            continue
        number += 1
        marker = "%d. " % number if node[0] == "ol" else "- "
        body, run = [], []
        for kid in child[2] if not isinstance(child, str) and child[0] == "li" else [child]:
            if not isinstance(kid, str) and kid[0] in ("ul", "ol"):
                body.extend(_md_blocks(run) + [_md_list(kid)])
                run = []
            else:
                run.append(kid)
        body.extend(_md_blocks(run))
        item = "\n".join(body).split("\n")
        lines.append((marker + item[0]).rstrip())
        lines.extend(" " * len(marker) + line if line else line for line in item[1:])
    return "\n".join(lines)


def _rows(node):
    """The rows of a table, each its cells apart by ' | '."""
    rows = []
    for child in node[2]:
        if isinstance(child, str):
            continue
        if child[0] == "tr":
            cells = [" ".join(_md_blocks(c[2])).replace("\n", " ") for c in child[2]
                     if not isinstance(c, str)]
            rows.append(" | ".join(cells))
        else:
            rows.extend(_rows(child))
    return rows


def _md_block(node):
    tag, _, children = node
    if re.match(r"^h[1-6]$", tag):
        text = " ".join(_md_blocks(children)).replace("\n", " ").strip()
        return ["%s %s" % ("#" * int(tag[1]), text)] if text else []
    if tag == "pre":
        return ["```\n%s\n```" % _raw(node).strip("\n")]
    if tag in ("ul", "ol"):
        text = _md_list(node)
        return [text] if text else []
    if tag in ("table", "thead", "tbody", "tfoot", "tr"):
        rows = [r for r in _rows(("", {}, [node])) if r.strip(" |")]
        return ["\n".join(rows)] if rows else []
    if tag == "hr":
        return ["---"]
    if tag == "blockquote":
        return ["\n".join("> " + line if line else ">"
                          for line in "\n\n".join(_md_blocks(children)).split("\n"))]
    return _md_blocks(children)


def to_markdown(text):
    """Yougile's HTML back to Markdown; the text with tags stripped if that fails."""
    if not TAG.search(text):
        return html.unescape(text).strip()
    try:
        tree = _Tree()
        tree.feed(text)
        tree.close()
        return "\n\n".join(_md_blocks(tree.root[2]))
    except Exception:
        stripped = re.sub(r"<[^>]*>", " ", text)
        return re.sub(r"[ \t]+", " ", html.unescape(stripped)).strip()


# --- commands --------------------------------------------------------------------------


def read_text(value):
    text = sys.stdin.read() if value == "-" else value
    if not text.strip():
        raise Failure(USAGE, "the text is empty")
    return text


def agent_mark():
    agent = os.environ.get("LADO_AGENT", "").strip()
    return "[LADO: %s]" % agent if agent else ""


# A mark as the first paragraph of a description's Markdown (any agent's).
MARK = re.compile(r"\A\s*\[LADO: [^\]\n]*\][ \t]*(?:\n\s*|\Z)")


def unmarked(markdown):
    """The Markdown without the mark it starts with."""
    return MARK.sub("", markdown, count=1)


def _marked(body):
    """HTML to send: the mark as its first paragraph, then the body."""
    label = agent_mark()
    return ("<p>%s</p>" % html.escape(label) if label else "") + body


def marked_html(markdown):
    """The description to send: the mark, then the Markdown as HTML."""
    return _marked(to_html(markdown) if markdown is not None else "")


def _send_message(api, task, markdown, body_html=None):
    """Post a message to the task's chat (its id is the task's id); return its id."""
    label = agent_mark()
    text = "%s\n\n%s" % (label, markdown) if label else markdown
    body = {"text": text, "label": "",
            "textHtml": _marked(body_html) if body_html else marked_html(markdown)}
    result = api.call("POST", "chats/%s/messages" % task["id"], body=body,
                      missing=missing_task(key_of(task)))
    return (result or {}).get("id")


def _assignees(api, ids):
    return ", ".join(api.person(i) for i in ids) if ids else "unassigned"


def _column_title(api, config, column_id):
    columns = api.columns(config) if config else []
    for column in columns:
        if column.get("id") == column_id:
            return column_name(column, columns)
    if not column_id:
        return "no column"
    try:
        return (api.call("GET", "columns/" + column_id) or {}).get("title") or column_id
    except Failure as failure:
        if failure.code != NOT_FOUND:
            raise
        return column_id


def _stickers(api, config):
    """The board's stickers with states, by name."""
    board = api.board(config)
    return [s for s in api.pages("string-stickers", {"boardId": board["id"]})
            if not s.get("deleted")]


def _resolve_label(stickers, config, word):
    """(sticker id, state id) of a label word; exit 3 when the board lacks either."""
    sticker_name, state_name = sticker_state(config, word)
    where = "'labels.%s: %s' in %s" % (word, config["labels"][word], CONFIG_PATH)
    found = [s for s in stickers if (s.get("name") or "").casefold() == sticker_name.casefold()]
    if not found:
        raise Failure(CONFIG, "the board has no sticker '%s' of %s; its stickers: %s"
                      % (sticker_name, where, ", ".join(s.get("name") or "?" for s in stickers)
                         or "none"))
    states = [s for s in found[0].get("states") or [] if not s.get("deleted")]
    state = [s for s in states if (s.get("name") or "").casefold() == state_name.casefold()]
    if not state:
        raise Failure(CONFIG, "sticker '%s' has no state '%s' of %s; its states: %s"
                      % (sticker_name, state_name, where,
                         ", ".join(s.get("name") or "?" for s in states) or "none"))
    return found[0]["id"], state[0]["id"]


def _resolvable(stickers, config, words):
    """(sticker id, state id) of each word the board has; the others left out."""
    resolved = {}
    for word in words:
        try:
            resolved[word] = _resolve_label(stickers, config, word)
        except Failure as failure:
            if failure.code != CONFIG:
                raise
    return resolved


def _has(value, state_id):
    return state_id in value if isinstance(value, list) else value == state_id


def _labels_of(task, resolved):
    stickers = task.get("stickers") or {}
    return [word for word, (sid, state) in sorted(resolved.items())
            if _has(stickers.get(sid), state)]


def cmd_search(api, args):
    if args.start < 0 or args.max < 1:
        raise Failure(USAGE, "--start must be 0 or more and --max 1 or more")
    config = load_config()
    if args.status:
        columns = [api.column(config, args.status)]
    else:
        columns = api.columns(config)
    query = {}
    if args.text:
        query["title"] = args.text
    unassigned = args.assignee == "none"
    if args.assignee and not unassigned:
        query["assignedTo"] = api.user_by(args.assignee)
    found = []
    for column in columns:
        for task in api.tasks(column["id"], query):
            if task.get("archived") or (unassigned and task.get("assigned")):
                continue
            found.append((column, task))
    total = len(found)
    shown = found[args.start:args.start + args.max]
    if not shown:
        print("No tasks (total %d)." % total)
        return OK
    print("Tasks %d-%d of %d" % (args.start + 1, args.start + len(shown), total))
    for column, task in shown:
        print("%s  [%s]  %s  (%s)" % (key_of(task), column_name(column, api.columns(config)),
                                      task.get("title"),
                                      _assignees(api, task.get("assigned") or [])))
    if args.start + len(shown) < total:
        print("More: run again with --start %d" % (args.start + len(shown)))
    return OK


def _show(api, config, task):
    """The task as get prints it, up to its description."""
    print("%s  %s" % (key_of(task), task.get("title")))
    flags = [name for name in ("completed", "archived") if task.get(name)]
    print("Status: %s%s" % (_column_title(api, config, task.get("columnId")),
                            "   (%s)" % ", ".join(flags) if flags else ""))
    print("Assignees: %s" % _assignees(api, task.get("assigned") or []))
    if config["labels"]:
        # Words whose sticker or state the board no longer has are left out, as in label.
        resolved = _resolvable(_stickers(api, config), config, config["labels"])
        print("Labels: %s" % (", ".join(_labels_of(task, resolved)) or "none"))
    print("\nDescription:\n%s" % (to_markdown(task.get("description") or "") or "(empty)"))


def cmd_get(api, args):
    config = load_config()
    task = api.task(config, args.key)
    _show(api, config, task)
    messages = [m for m in api.pages("chats/%s/messages" % task["id"])
                if not m.get("deleted")]
    messages.sort(key=lambda m: m.get("id") or 0)
    shown = messages[-args.comments:] if args.comments > 0 else []
    if messages:
        print("\nComments: %d, the last %d shown" % (len(messages), len(shown)))
    else:
        print("\nComments: none")
    for message in shown:
        stamp = message.get("id")
        when = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(stamp / 1000)) \
            if isinstance(stamp, (int, float)) else "?"
        print("\n--- comment %s, %s, %s\n%s" % (stamp, api.person(message.get("fromUserId")),
                                               when, message.get("text")))
    return OK


def cmd_create(api, args):
    config = load_config()
    if args.status:
        column = api.column(config, args.status)
    else:
        columns = api.columns(config)
        if not columns:
            raise Failure(REFUSED, "board '%s' has no columns to create the task in"
                          % api.board(config).get("title"))
        column = columns[0]
    description = read_text(args.description) if args.description is not None else None
    body = {"title": args.title, "columnId": column["id"]}
    text = marked_html(description)
    if text:
        body["description"] = text
    try:
        created = api.call("POST", "tasks", body=body)
    except Failure as failure:
        # A task that may have been created has no key yet: look for it by its title.
        failure.message = failure.message.replace(
            "check with get before running it again",
            "look for it with search --text %s before running create again"
            % shlex.quote(args.title))
        raise
    task_id = (created or {}).get("id")
    try:
        task = api.call("GET", "tasks/%s" % task_id, missing=missing_task(task_id))
    except Failure as failure:
        raise Failure(failure.code, "task %s created, but reading its key failed (do not run "
                                    "create again): %s" % (task_id, failure.message))
    print("%s created in %s" % (key_of(task), column_name(column, api.columns(config))))
    return OK


def cmd_edit(api, args):
    if args.title is None and args.description is None:
        raise Failure(USAGE, "give --title or --description, or both")
    if args.title is not None and not args.title.strip():
        raise Failure(USAGE, "the title is empty")
    description = None
    if args.description is not None:
        # The mark is the script's: one the text starts with (copied from get) is dropped.
        description = unmarked(read_text(args.description))
        if not description.strip():
            raise Failure(USAGE, "the description is empty")
    config = load_config()
    task = api.task(config, args.key)
    key = key_of(task)
    body, same = {}, []
    if args.title is not None:
        if args.title == task.get("title"):
            same.append("title")
        else:
            body["title"] = args.title
    if description is not None:
        # Compared as get shows them, without the mark: whose mark it is changes nothing.
        old = unmarked(to_markdown(task.get("description") or ""))
        if old == to_markdown(to_html(description)):
            same.append("description")
        else:
            # The whole description is replaced: the old mark goes, this agent's comes first.
            body["description"] = marked_html(description)
    if not body:
        print("%s: %s already so, nothing changed\n" % (key, " and ".join(same)))
        _show(api, config, task)
        return OK
    api.call("PUT", "tasks/%s" % task["id"], body=body, missing=missing_task(key))
    try:
        after = api.call("GET", "tasks/%s" % task["id"], missing=missing_task(key))
    except Failure as failure:
        raise Failure(failure.code, "%s: changed, but reading it back failed (do not run it "
                                    "again; check with get): %s" % (key, failure.message))
    print("%s: %s changed%s\n" % (key, " and ".join(body),
                                  "; %s already so" % same[0] if same else ""))
    _show(api, config, after)
    return OK


def cmd_transition(api, args):
    if args.comment is not None and not args.target:
        raise Failure(USAGE, "--comment needs a target: transition %s <status> --comment ..."
                      % args.key)
    config = load_config()
    task = api.task(config, args.key)
    key = key_of(task)
    columns = api.columns(config)
    current = [c for c in columns if c.get("id") == task.get("columnId")][0]
    if not args.target:
        for column in columns:
            print("%s%s" % (column_name(column, columns),
                            "   (current)" if column is current else ""))
        return OK
    comment = read_text(args.comment) if args.comment is not None else None
    column = api.column(config, args.target)
    if column is current:
        there = "%s is already in %s" % (key, column_name(current, columns))
        if comment is not None:
            there += ", comment %s added" % _send_message(api, task, comment)
        print(there)
        return OK
    api.call("PUT", "tasks/%s" % task["id"], body={"columnId": column["id"]},
             missing=missing_task(key))
    moved = "%s: %s -> %s" % (key, column_name(current, columns), column_name(column, columns))
    if comment is not None:
        try:
            moved += ", comment %s added" % _send_message(api, task, comment)
        except Failure as failure:
            # No answer or a 5xx may follow a message Yougile did add; a 429 runs nothing.
            unsure = failure.code == UNREACHABLE or (failure.code == SERVER_ERROR
                                                     and failure.status != 429)
            check = "check with get, then send the comment with comment if it is not there"
            if failure.code == UNREACHABLE:
                advice = "once you are told Yougile answers again, " + check
            elif unsure:
                advice = check
            elif failure.code == REFUSED:
                advice = "fix the text the line names, then send the comment with comment"
            else:
                advice = "report it; send the comment with comment once you are told to"
            raise Failure(failure.code, "%s done, but %s (do not run the transition again; "
                                        "%s): %s" % (
                moved, "the comment may not have been added" if unsure
                else "the comment was not added", advice, failure.message))
    print(moved)
    return OK


def cmd_comment(api, args):
    text = read_text(args.text)
    task = api.task(load_config(), args.key)
    print("%s: comment %s added" % (key_of(task), _send_message(api, task, text)))
    return OK


def cmd_assign(api, args):
    task = api.task(load_config(), args.key)
    key = key_of(task)
    current = list(task.get("assigned") or [])
    target = api.user_by(args.user)
    wanted = [target] if target else []
    if sorted(current) == sorted(wanted):
        print("%s: assignee %s already, nothing changed" % (key, _assignees(api, current)))
        return OK
    # Taking a task from another account is the human's decision, never a side effect.
    mine = api.me().get("id")
    others = [user for user in current if user != mine]
    if others and not args.reassign:
        raise Failure(REFUSED, "%s is assigned to %s, another account: not changed; report "
                               "it, and add --reassign only when the human or your step says "
                               "to take it from them" % (key, _assignees(api, others)))
    api.call("PUT", "tasks/%s" % task["id"], body={"assigned": wanted},
             missing=missing_task(key))
    print("%s: assignee %s -> %s" % (key, _assignees(api, current), _assignees(api, wanted)))
    return OK


def cmd_label(api, args):
    add = [word for group in args.add or [] for word in group]
    remove = [word for group in args.remove or [] for word in group]
    if not add and not remove:
        raise Failure(USAGE, "give --add or --remove with at least one label")
    config = load_config()
    for word in add + remove:
        sticker_state(config, word)  # a word the settings do not map: before any request
    stickers = _stickers(api, config)
    named = {w: _resolve_label(stickers, config, w) for w in add + remove}
    # Shown labels: the named ones and every other word the board still has.
    resolved = dict(_resolvable(stickers, config, config["labels"]), **named)
    task = api.task(config, args.key)
    key = key_of(task)
    current = dict(task.get("stickers") or {})
    changes = {}
    for word in remove:
        sid, state = resolved[word]
        value = changes.get(sid, current.get(sid))
        if isinstance(value, list) and state in value:
            rest = [s for s in value if s != state]
            changes[sid] = rest or "-"
        elif value == state:
            changes[sid] = "-"
    for word in add:
        sid, state = resolved[word]
        value = changes.get(sid, current.get(sid))
        if isinstance(value, list):
            if state not in value:
                changes[sid] = value + [state]
        elif value != state:
            changes[sid] = state
    changes = {sid: v for sid, v in changes.items() if v != current.get(sid)}
    if not changes:
        print("%s: labels %s, nothing changed" % (key, ", ".join(_labels_of(task, resolved))
                                                  or "none"))
        return OK
    # The whole map is sent, so the task's other stickers stay as they are.
    current.update(changes)
    api.call("PUT", "tasks/%s" % task["id"], body={"stickers": current},
             missing=missing_task(key))
    try:
        after = api.call("GET", "tasks/%s" % task["id"], missing=missing_task(key))
    except Failure as failure:
        raise Failure(failure.code, "%s: labels changed, but reading them back failed (do "
                                    "not run it again): %s" % (key, failure.message))
    print("%s: labels %s" % (key, ", ".join(_labels_of(after, resolved)) or "none"))
    return OK


def cmd_link(api, args):
    task = api.task(load_config(), args.key)
    text = "[%s](%s)" % (args.title, args.url) if args.title else args.url
    # The anchor is built here: a bare URL read as Markdown loses its _x_ to <em>.
    anchor = '<p><a href="%s">%s</a></p>' % (
        html.escape(args.url), _inline(args.title) if args.title else html.escape(args.url))
    print("%s: linked %s in comment %s" % (key_of(task), args.url,
                                           _send_message(api, task, text, anchor)))
    return OK


def cmd_whoami(api, args):
    print("You work as %s" % _person(api.me()))
    return OK


# --- command line ----------------------------------------------------------------------


def parser():
    top = argparse.ArgumentParser(prog="yougile.py",
                                  description="Yougile through its REST API v2.")
    sub = top.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    p = sub.add_parser("search", help="find tasks of the board; archived ones left out")
    p.add_argument("--status", help="a column title or id, or a word of statuses")
    p.add_argument("--assignee", help="'me', an email, or 'none' (unassigned)")
    p.add_argument("--text", help="words of the title")
    p.add_argument("--start", type=int, default=0, help="index of the first task")
    p.add_argument("--max", type=int, default=20, help="tasks per page (default 20)")
    p.set_defaults(run=cmd_search)

    p = sub.add_parser("get", help="read a task: status, assignees, description, comments")
    p.add_argument("key", help="the task's key (DEV-484), number (ID-484) or id")
    p.add_argument("--comments", type=int, default=5, help="last N comments (default 5)")
    p.set_defaults(run=cmd_get)

    p = sub.add_parser("create", help="create a task on the board")
    p.add_argument("--title", required=True)
    p.add_argument("--description", help="Markdown; '-' reads it from stdin")
    p.add_argument("--status", help="a column title or id, or a word of statuses (default: "
                                    "the board's first column)")
    p.set_defaults(run=cmd_create)

    p = sub.add_parser("edit", help="change a task's title or description (or both)")
    p.add_argument("key", help="the task's key (DEV-484), number (ID-484) or id")
    p.add_argument("--title", help="the new title")
    p.add_argument("--description", help="the new description, replacing the old one whole: "
                                         "Markdown; '-' reads it from stdin")
    p.set_defaults(run=cmd_edit)

    p = sub.add_parser("transition", help="list the columns, or move a task to one")
    p.add_argument("key")
    p.add_argument("target", nargs="?", help="a column title or id, or a word of statuses")
    p.add_argument("--comment", help="comment to add after the move (needs a target), "
                                     "Markdown; '-' reads it from stdin")
    p.set_defaults(run=cmd_transition)

    p = sub.add_parser("comment", help="comment on a task (a message in its chat)")
    p.add_argument("key")
    p.add_argument("text", help="Markdown; '-' reads it from stdin")
    p.set_defaults(run=cmd_comment)

    p = sub.add_parser("assign", help="assign a task to you, to an email, or to nobody")
    p.add_argument("key")
    p.add_argument("user", help="'me', an email, or 'none' to unassign")
    p.add_argument("--reassign", action="store_true",
                   help="also when another account holds the task (refused otherwise)")
    p.set_defaults(run=cmd_assign)

    p = sub.add_parser("label", help="add or remove labels (sticker states of labels)")
    p.add_argument("key")
    p.add_argument("--add", action="append", nargs="+", metavar="LABEL")
    p.add_argument("--remove", action="append", nargs="+", metavar="LABEL")
    p.set_defaults(run=cmd_label)

    p = sub.add_parser("link", help="post a URL to a task as a comment")
    p.add_argument("key")
    p.add_argument("url")
    p.add_argument("--title", help="link text (default: the URL)")
    p.set_defaults(run=cmd_link)

    p = sub.add_parser("whoami", help="the account you work as: Real Name (email)")
    p.set_defaults(run=cmd_whoami)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        api = Yougile()
        return args.run(api, args)
    except Failure as failure:
        print("yougile.py: " + failure.message, file=sys.stderr)
        return failure.code


if __name__ == "__main__":
    sys.exit(main())
