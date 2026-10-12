"""Tests of skills/tracker/yougile.py against a fake Yougile on localhost.

Run from the repository root: uv run --no-project python -m unittest discover -s tests
Standard library only; the TLS test needs the `openssl` command and is skipped without it.
"""

import contextlib
import copy
import io
import json
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.join(HERE, "..", "skills", "tracker"))
import yougile  # noqa: E402

KEY = "k3y-Secret-0123456789abcdef"
CONFIG = """\
# settings of the test project
board: Dev
statuses:
  in progress: In progress   # a word of the process -> a column of the board
  review: Review
  done: Done
labels:
  waiting for release: 'Release: Waiting'
  shipped: Release: Shipped
"""


def uid(n):
    return "00000000-0000-4000-8000-%012d" % n


BOARD, OTHER_BOARD = uid(1), uid(2)
TODO, PROGRESS, REVIEW, DONE, FOREIGN = uid(11), uid(12), uid(13), uid(14), uid(15)
ME, ANN = uid(21), uid(22)
T1, T2, T3, T4 = uid(31), uid(32), uid(33), uid(34)
RELEASE, PRIORITY = uid(41), uid(42)


class Raw:
    """A payload sent as it is."""

    def __init__(self, data):
        self.data = data


class Seq:
    """Payloads answered one per request, the last one from then on."""

    def __init__(self, *answers):
        self.answers = list(answers)

    def next(self):
        return self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]


def model():
    return {
        "boards": [{"id": BOARD, "title": "Dev", "projectId": uid(90)},
                   {"id": OTHER_BOARD, "title": "Dev ops", "projectId": uid(90)}],
        "columns": [{"id": TODO, "title": "To do", "boardId": BOARD},
                    {"id": PROGRESS, "title": "In progress", "boardId": BOARD},
                    {"id": REVIEW, "title": "Review", "boardId": BOARD},
                    {"id": DONE, "title": "Done", "boardId": BOARD},
                    {"id": FOREIGN, "title": "Elsewhere", "boardId": OTHER_BOARD}],
        "users": [{"id": ME, "realName": "Agent Smith", "email": "agent@example.com"},
                  {"id": ANN, "realName": "Ann Lee", "email": "ann@example.com"}],
        "tasks": [
            {"id": T1, "idTaskProject": "DEV-1", "idTaskCommon": "ID-11", "title": "Login form", "columnId": TODO,
             "assigned": [], "description": "<p>Make it</p>"},
            {"id": T2, "idTaskProject": "DEV-2", "idTaskCommon": "ID-12", "title": "Logout", "columnId": PROGRESS,
             "assigned": [ANN]},
            {"id": T3, "idTaskProject": "DEV-3", "idTaskCommon": "ID-13", "title": "Old login", "columnId": PROGRESS,
             "assigned": [], "archived": True},
            {"id": T4, "idTaskProject": "DEV-4", "idTaskCommon": "ID-14", "title": "Profile", "columnId": REVIEW,
             "assigned": [ME], "stickers": {PRIORITY: "hi"}},
        ],
        "stickers": [
            {"id": RELEASE, "name": "Release", "boardId": BOARD,
             "states": [{"id": "wait", "name": "Waiting"}, {"id": "ship", "name": "Shipped"}]},
            {"id": PRIORITY, "name": "Priority", "boardId": BOARD,
             "states": [{"id": "hi", "name": "High"}]},
        ],
        "messages": {T1: [{"id": 1700000000000 + n, "fromUserId": ANN, "text": "note %d" % n,
                           "textHtml": "<p>note %d</p>" % n, "label": ""}
                          for n in (3, 1, 2)]},
    }


class FakeYougile:
    """A tiny Yougile: a model behind the API's paths; `routes` override a path."""

    def __init__(self, tls_context=None):
        self.data = model()
        self.routes = {}
        self.requests = []
        self.created = 0
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                url = urllib.parse.urlsplit(self.path)
                request = {"method": self.command, "path": url.path,
                           "query": dict(urllib.parse.parse_qsl(url.query)),
                           "headers": dict(self.headers),
                           "body": json.loads(body) if body else None}
                fake.requests.append(request)
                route = fake.routes.get((self.command, url.path))
                if route is not None:
                    status, headers, payload = route
                    if isinstance(payload, Seq):
                        status, headers, payload = payload.next()
                else:
                    headers = {}
                    status, payload = fake.serve(request)
                data = payload.data if isinstance(payload, Raw) else (
                    json.dumps(payload).encode() if payload is not None else b"")
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PUT = do_DELETE = _answer

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        if tls_context:
            self.server.socket = tls_context.wrap_socket(self.server.socket,
                                                         server_side=True)
        scheme = "https" if tls_context else "http"
        self.url = "%s://127.0.0.1:%d" % (scheme, self.server.server_address[1])
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       args=(0.05,), daemon=True)
        self.thread.start()

    @staticmethod
    def page(items, query):
        limit, offset = int(query.get("limit", 50)), int(query.get("offset", 0))
        content = items[offset:offset + limit]
        return 200, {"paging": {"count": len(content), "limit": limit, "offset": offset,
                                "next": offset + limit < len(items)},
                     "content": copy.deepcopy(content)}

    def find(self, kind, id_):
        return next((x for x in self.data[kind] if x["id"] == id_), None)

    def serve(self, request):
        method, query, body = request["method"], request["query"], request["body"]
        parts = request["path"].split("/")[2:]  # after /api-v2/
        not_found = (404, {"statusCode": 404, "message": "Not Found"})
        if parts == ["users", "me"]:
            return 200, self.find("users", ME)
        if parts[0] == "users" and len(parts) == 2:
            user = self.find("users", parts[1])
            return (200, user) if user else not_found
        if parts == ["users"]:
            users = [u for u in self.data["users"]
                     if "email" not in query or u["email"] == query["email"]]
            return self.page(users, query)
        if parts[0] == "boards" and len(parts) == 2:
            board = self.find("boards", parts[1])
            return (200, board) if board else not_found
        if parts == ["boards"]:  # the title filter matches part of a title
            return self.page([b for b in self.data["boards"] if query.get("title", "").lower()
                              in b["title"].lower()], query)
        if parts[0] == "columns" and len(parts) == 2:
            column = self.find("columns", parts[1])
            return (200, column) if column else not_found
        if parts == ["columns"]:
            return self.page([c for c in self.data["columns"]
                              if c["boardId"] == query.get("boardId")], query)
        if parts == ["task-list"]:
            tasks = [t for t in self.data["tasks"]
                     if t["columnId"] == query.get("columnId")
                     and query.get("title", "") in t["title"]
                     and ("assignedTo" not in query
                          or query["assignedTo"] in t.get("assigned", []))]
            return self.page(tasks, query)
        if parts == ["tasks"] and method == "POST":
            self.created += 1
            task = dict(body, id=uid(70 + self.created), idTaskProject="DEV-%d"
                        % (100 + self.created), idTaskCommon="ID-%d" % (100 + self.created),
                        assigned=[])
            self.data["tasks"].append(task)
            return 201, {"id": task["id"]}
        if parts[0] == "tasks" and len(parts) == 2:
            # Yougile takes the id, the key or the number, in any case.
            wanted = urllib.parse.unquote(parts[1]).casefold()
            task = next((t for t in self.data["tasks"] if wanted in (
                t["id"], t["idTaskProject"].casefold(),
                t.get("idTaskCommon", "").casefold())), None)
            if not task:
                return not_found
            if method == "PUT":
                task.update(body)
                task["stickers"] = {k: v for k, v in task.get("stickers", {}).items()
                                    if v != "-"}
                return 200, {"id": task["id"]}
            return 200, copy.deepcopy(task)
        if parts == ["string-stickers"]:
            return self.page([s for s in self.data["stickers"]
                              if s["boardId"] == query.get("boardId")], query)
        if parts[0] == "chats" and parts[2:] == ["messages"]:
            if not self.find("tasks", parts[1]):
                return not_found
            messages = self.data["messages"].setdefault(parts[1], [])
            if method == "POST":
                message = dict(body, id=1800000000000 + len(messages), fromUserId=ME)
                messages.append(message)
                return 201, {"id": message["id"]}
            return self.page(messages, query)
        return 404, {"statusCode": 404, "message": "Cannot %s" % request["path"]}

    def route(self, method, path, payload=None, status=200, headers=None):
        self.routes[(method, "/api-v2/" + path)] = (status, headers or {}, payload)

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class YougileTestCase(unittest.TestCase):
    def setUp(self):
        self.api = FakeYougile()
        self.addCleanup(self.api.close)
        self.repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.repo)
        os.mkdir(os.path.join(self.repo, ".git"))
        os.mkdir(os.path.join(self.repo, ".lado"))
        self.write_config(CONFIG)
        old = os.getcwd()
        os.chdir(self.repo)
        self.addCleanup(os.chdir, old)
        env = {"YOUGILE_URL": self.api.url + "/", "YOUGILE_API_KEY": KEY,
               "LADO_AGENT": "developer"}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sleeps = []
        sleeper = mock.patch.object(yougile.time, "sleep", self.sleeps.append)
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def write_config(self, text):
        with open(os.path.join(self.repo, ".lado", "tracker.yaml"), "w") as handle:
            handle.write(text)

    def run_yougile(self, *argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch("sys.stdin", io.StringIO(stdin)):
            try:
                code = yougile.main(list(argv))
            except SystemExit as exit:
                code = exit.code
        self.assertNotIn(KEY, out.getvalue() + err.getvalue())
        return code, out.getvalue(), err.getvalue()

    def assertFails(self, code, pattern, *argv, stdin=""):
        got, out, err = self.run_yougile(*argv, stdin=stdin)
        self.assertEqual(got, code, out + err)
        self.assertRegex(err, pattern)
        self.assertEqual(len(err.strip().splitlines()), 1, err)
        return err

    def sent(self, method, path):
        return [r for r in self.api.requests
                if r["method"] == method and r["path"] == "/api-v2/" + path]

    def task(self, id_):
        return self.api.find("tasks", id_)


class ConfigTest(unittest.TestCase):
    def parse(self, text):
        return yougile.parse_config(text, "tracker.yaml")

    def test_full_example(self):
        config = self.parse(CONFIG)
        self.assertEqual(config["board"], "Dev")
        self.assertEqual(config["statuses"]["in progress"], "In progress")
        self.assertEqual(config["labels"]["waiting for release"], "Release: Waiting")
        self.assertEqual(config["labels"]["shipped"], "Release: Shipped")

    def test_only_board_is_required(self):
        config = self.parse("board: %s\n" % BOARD)
        self.assertEqual((config["statuses"], config["labels"]), ({}, {}))
        with self.assertRaisesRegex(ValueError, "'board'.*required"):
            self.parse("statuses:\n  done: Done\n")

    def test_localized_names(self):
        config = self.parse("board: Разработка\nstatuses:\n  review: Ревью  # translated\n")
        self.assertEqual(config["statuses"]["review"], "Ревью")

    def test_errors_name_the_line(self):
        cases = {
            "board: A\n\tstatuses:\n": "line 2: indent with spaces",
            "board: A\nstatuses:\n  - a\n": "line 3: lists are not supported: every value "
                                         "is one plain value",
            "board: [A, B]\n": "line 1: lists are not supported",
            "board: A\nstatuses:\n  a:\n    b: c\n": "line 3: .*one level",
            "board A\n": "line 1: expected 'key: value'",
            "board: A\nboard: B\n": "line 2: 'board' is given twice",
            "board: 'A\n": "line 1: .*same quote",
            "board: A\n  x: y\n": "line 2: unexpected indent",
            "board: {a: b}\n": "line 1: .*flow maps",
            "board: A\nproject: B\n": "line 2: unknown key 'project'",
            "board: A\nlabels:\n  x: NoState\n": "line 3: 'labels.x' must be 'Sticker: State'",
            "board: A\nstatuses: a\n": "line 2: 'statuses' must be a map",
            "---\nboard: A\n": "line 1: one document only",
        }
        for text, pattern in cases.items():
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, pattern):
                    self.parse(text)


class MarkdownTest(unittest.TestCase):
    def test_blocks(self):
        text = ("# Title\n\nSome **bold**, *italic*, _also_ and `a<b>`.\n"
                "Next line [site](https://x.org/a?b=1&c=2)\n\n"
                "- one\n- two\n  - nested\n\n1. first\n2. second\n\n"
                "```python\nif a < b:\n    pass\n```\nafter")
        self.assertEqual(yougile.to_html(text), (
            "<h1>Title</h1>"
            "<p>Some <strong>bold</strong>, <em>italic</em>, <em>also</em> and "
            "<code>a&lt;b&gt;</code>.<br>Next line "
            '<a href="https://x.org/a?b=1&amp;c=2">site</a></p>'
            "<ul><li>one</li><li>two<ul><li>nested</li></ul></li></ul>"
            "<ol><li>first</li><li>second</li></ol>"
            "<pre><code>if a &lt; b:\n    pass</code></pre>"
            "<p>after</p>"))

    def test_html_is_escaped_and_words_kept(self):
        self.assertEqual(yougile.to_html("<script>x</script> snake_case_name 2*3*4"),
                         "<p>&lt;script&gt;x&lt;/script&gt; snake_case_name 2*3*4</p>")

    def test_no_markup_inside_code(self):
        self.assertEqual(yougile.to_html("`**not bold** [a](b)`"),
                         "<p><code>**not bold** [a](b)</code></p>")

    def test_open_fence_is_closed(self):
        self.assertEqual(yougile.to_html("```\ncode"), "<pre><code>code</code></pre>")

    def test_falls_back_to_plain_paragraphs(self):
        with mock.patch.object(yougile, "_html", side_effect=RuntimeError):
            self.assertEqual(yougile.to_html("a <b>\nc\n\nd"),
                             "<p>a &lt;b&gt;<br>c</p><p>d</p>")


class HtmlToMarkdownTest(unittest.TestCase):
    def test_elements_the_script_writes(self):
        self.assertEqual(yougile.to_markdown(
            "<p>[LADO: dev]</p><h2>Plan</h2>"
            "<p>Some <strong>bold</strong>, <b>b</b>, <em>it</em>, <i>i</i> &amp; "
            "<code>a&lt;b</code><br>next "
            '<a href="https://x.org/?a=1&amp;b=2">site</a></p>'
            "<pre><code>if a &lt; b:\n    pass</code></pre>"), (
            "[LADO: dev]\n\n## Plan\n\n"
            "Some **bold**, **b**, *it*, *i* & `a<b`\nnext [site](https://x.org/?a=1&b=2)"
            "\n\n```\nif a < b:\n    pass\n```"))

    def test_nested_lists(self):
        self.assertEqual(yougile.to_markdown(
            "<ul><li>one</li><li>two<ul><li>nested</li></ul></li></ul>"
            "<ol><li>first</li><li>second<ol><li>sub</li></ol><ul><li>mixed</li></ul>"
            "</li></ol>"),
            "- one\n- two\n  - nested\n\n1. first\n2. second\n   1. sub\n   - mixed")

    def test_end_tags_left_out(self):
        self.assertEqual(yougile.to_markdown(
            "<p>a<p>b<ul><li>one<li><p>two<ul><li>n<li>m</ul><li>three</ul>"
            "<table><tr><td>1<td>2<tr><td>3<td>4</table>"),
            "a\n\nb\n\n- one\n- two\n  - n\n  - m\n- three\n\n1 | 2\n3 | 4")

    def test_other_tags_dropped_text_kept(self):
        self.assertEqual(yougile.to_markdown(
            '<p><span style="color:red">kept</span>&nbsp;<u>too</u>'
            '<script>alert(1)</script></p><div>block</div>'
            '<p>see <img src="https://img.example/x.png" alt="x"></p>'),
            "kept too\n\nblock\n\nsee https://img.example/x.png")

    def test_table_cells_and_rows(self):
        self.assertEqual(yougile.to_markdown(
            "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
            "<tbody><tr><td>1</td><td><strong>2</strong></td></tr></tbody></table>"),
            "A | B\n1 | **2**")

    def test_plain_text_and_empty(self):
        self.assertEqual(yougile.to_markdown("a &lt; b\nc"), "a < b\nc")
        self.assertEqual(yougile.to_markdown(""), "")

    def test_round_trip_of_what_the_script_writes(self):
        text = ("# Title\n\nSome **bold**, *italic* and `code`.\n"
                "Next [site](https://x.org/a?b=1&c=2)\n\n"
                "- one\n- two\n  - nested\n\n1. first\n2. second\n   1. sub\n\n"
                "```\nif a < b:\n    pass\n```\n\nafter")
        self.assertEqual(yougile.to_markdown(yougile.to_html(text)), text)

    def test_falls_back_to_stripped_tags(self):
        with mock.patch.object(yougile, "_md_blocks", side_effect=RuntimeError):
            self.assertEqual(yougile.to_markdown("<p>a &amp; <b>b</b></p><p>c</p>"),
                             "a & b c")


class CommandsTest(YougileTestCase):
    def test_whoami_sends_the_key_as_bearer(self):
        code, out, err = self.run_yougile("whoami")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "You work as Agent Smith (agent@example.com)\n")
        request = self.api.requests[0]
        self.assertEqual(request["path"], "/api-v2/users/me")
        self.assertEqual(request["headers"]["Authorization"], "Bearer " + KEY)
        self.assertEqual(request["headers"]["Content-Type"], "application/json")

    def test_default_url_is_the_cloud(self):
        with mock.patch.dict(os.environ, {"YOUGILE_URL": ""}):
            self.assertEqual(yougile.Yougile().base, "https://yougile.com")

    def test_search_every_column_without_archived(self):
        code, out, err = self.run_yougile("search")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, (
            "Tasks 1-3 of 3\n"
            "DEV-1  [To do]  Login form  (unassigned)\n"
            "DEV-2  [In progress]  Logout  (Ann Lee (ann@example.com))\n"
            "DEV-4  [Review]  Profile  (Agent Smith (agent@example.com))\n"))
        self.assertEqual({r["query"]["columnId"] for r in self.sent("GET", "task-list")},
                         {TODO, PROGRESS, REVIEW, DONE})

    def test_search_filters(self):
        code, out, _ = self.run_yougile("search", "--status", "in progress",
                                        "--assignee", "ann@example.com", "--text", "Log")
        self.assertEqual((code, out.splitlines()[1:]),
                         (0, ["DEV-2  [In progress]  Logout  (Ann Lee (ann@example.com))"]))
        query = self.sent("GET", "task-list")[0]["query"]
        self.assertEqual((query["columnId"], query["assignedTo"], query["title"]),
                         (PROGRESS, ANN, "Log"))
        _, out, _ = self.run_yougile("search", "--assignee", "none")
        self.assertEqual([line.split()[0] for line in out.splitlines()[1:]], ["DEV-1"])
        _, out, _ = self.run_yougile("search", "--assignee", "me")
        self.assertEqual([line.split()[0] for line in out.splitlines()[1:]], ["DEV-4"])

    def test_search_pages(self):
        code, out, _ = self.run_yougile("search", "--max", "2")
        self.assertEqual(out.splitlines()[0], "Tasks 1-2 of 3")
        self.assertEqual(out.splitlines()[-1], "More: run again with --start 2")
        _, out, _ = self.run_yougile("search", "--start", "2", "--max", "2")
        self.assertEqual(out.splitlines(), ["Tasks 3-3 of 3", "DEV-4  [Review]  Profile  "
                                            "(Agent Smith (agent@example.com))"])
        _, out, _ = self.run_yougile("search", "--status", "done")
        self.assertEqual(out, "No tasks (total 0).\n")

    def test_search_refuses_negative_paging(self):
        for argv in (("--start", "-1"), ("--max", "0")):
            with self.subTest(argv=argv):
                self.assertFails(yougile.USAGE, "--start must be 0 or more and --max 1 or more",
                                 "search", *argv)
        self.assertEqual(self.api.requests, [])

    def test_lists_are_read_page_after_page(self):
        self.api.data["tasks"] += [
            {"id": uid(500 + n), "idTaskProject": "DEV-%d" % (500 + n), "title": "t",
             "columnId": DONE, "assigned": []} for n in range(1001)]
        code, out, err = self.run_yougile("search", "--status", "done", "--start", "1000")
        self.assertEqual(code, 0, err)
        self.assertIn("DEV-1500  [Done]  t", out)
        offsets = [r["query"]["offset"] for r in self.sent("GET", "task-list")
                   if r["query"]["columnId"] == DONE]
        self.assertEqual(offsets, ["0", "1000"])

    def test_search_unknown_status(self):
        self.assertFails(yougile.REFUSED, "status 'qa' is not a column of the board; its "
                                          "columns: To do, In progress, Review, Done; to use "
                                          "this word, map it to a column in 'statuses' of "
                                          r"\.lado/tracker\.yaml \(its words: in progress, "
                                          r"review, done\)",
                         "search", "--status", "qa")
        self.write_config("board: Dev\n")
        self.assertFails(yougile.REFUSED, r"'statuses' of .*\(its words: none\)",
                         "transition", "DEV-1", "qa")

    def test_statuses_word_of_no_column_is_the_settings(self):
        self.write_config("board: Dev\nstatuses:\n  review: QA\n")
        self.assertFails(yougile.CONFIG, "'statuses.review: QA' in .*is not a column of the "
                                         "board; its columns: To do.*the user fixes the file",
                         "transition", "DEV-1", "review")
        self.assertEqual(self.sent("PUT", "tasks/" + T1), [])

    def test_get_by_key(self):
        code, out, err = self.run_yougile("get", "dev-1", "--comments", "2")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, (
            "DEV-1  Login form\nStatus: To do\nAssignees: unassigned\nLabels: none\n"
            "\nDescription:\nMake it\n"
            "\nComments: 3, the last 2 shown\n"
            "\n--- comment 1700000000002, Ann Lee (ann@example.com), 2023-11-14 22:13 UTC\n"
            "note 2\n"
            "\n--- comment 1700000000003, Ann Lee (ann@example.com), 2023-11-14 22:13 UTC\n"
            "note 3\n"))
        self.assertEqual(self.sent("GET", "chats/%s/messages" % T1)[0]["query"]["limit"],
                         "1000")
        # One request for the task, none over the board's tasks.
        self.assertEqual(len(self.sent("GET", "tasks/dev-1")), 1)
        self.assertEqual(self.sent("GET", "task-list"), [])

    def test_statuses_column_by_id_and_ambiguous_title(self):
        self.write_config("board: Dev\nstatuses:\n  review: %s\n" % REVIEW)
        code, out, err = self.run_yougile("transition", "DEV-1", "review")
        self.assertEqual((code, out), (0, "DEV-1: To do -> Review\n"), err)
        self.api.data["columns"].append({"id": uid(16), "title": "Review", "boardId": BOARD})
        self.write_config("board: Dev\nstatuses:\n  review: Review\n")
        err = self.assertFails(yougile.CONFIG, "is the title of several columns: write the "
                                               "id of one", "transition", "DEV-1", "review")
        self.assertNotIn("rename", err)
        self.assertIn("Review (%s), Done, Review (%s)" % (REVIEW, uid(16)), err)

    def test_transition_lists_repeated_titles_with_ids(self):
        self.api.data["columns"].append({"id": uid(16), "title": "review", "boardId": BOARD})
        code, out, _ = self.run_yougile("transition", "DEV-2")
        self.assertEqual(out, "To do\nIn progress   (current)\nReview (%s)\nDone\n"
                              "review (%s)\n" % (REVIEW, uid(16)))
        code, out, err = self.run_yougile("transition", "DEV-2", uid(16))
        self.assertEqual((code, out), (0, "DEV-2: In progress -> review (%s)\n" % uid(16)), err)

    def test_get_by_number_and_id_shows_the_key(self):
        for name in ("ID-12", "id-12", T2):
            with self.subTest(name=name):
                code, out, err = self.run_yougile("get", name)
                self.assertEqual(code, 0, err)
                self.assertIn("DEV-2  Logout\nStatus: In progress\n", out)

    def test_get_needs_the_settings(self):
        os.remove(os.path.join(self.repo, ".lado", "tracker.yaml"))
        self.assertFails(yougile.CONFIG, "tracker.yaml not found", "get", T2)

    def test_get_shows_flags_and_labels(self):
        self.task(T4).update(completed=True, stickers={RELEASE: "wait", PRIORITY: "hi"})
        _, out, _ = self.run_yougile("get", "DEV-4")
        self.assertIn("Status: Review   (completed)\n", out)
        self.assertIn("Labels: waiting for release\n", out)

    def test_get_unknown_key(self):
        self.assertFails(yougile.NOT_FOUND, "task DEV-9 not found on board 'Dev'",
                         "get", "DEV-9")

    def test_board_by_id_and_ambiguous_title(self):
        self.write_config("board: %s\n" % BOARD)
        code, _, err = self.run_yougile("get", "DEV-1")
        self.assertEqual(code, 0, err)
        self.assertTrue(self.sent("GET", "boards/" + BOARD))
        self.api.data["boards"].append({"id": uid(3), "title": "dev", "projectId": uid(91)})
        self.write_config("board: Dev\n")
        self.assertFails(yougile.CONFIG, "several boards are titled.*write the id of one",
                         "get", "DEV-1")
        self.write_config("board: Nope\n")
        self.assertFails(yougile.CONFIG, "no board titled", "get", "DEV-1")
        self.write_config("board: %s\n" % uid(9))
        self.assertFails(yougile.CONFIG, "no board with the id", "get", "DEV-1")

    def test_create_in_first_column_with_mark(self):
        code, out, err = self.run_yougile("create", "--title", "New", "--description", "-",
                                          stdin="**Why:** it <breaks>\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "DEV-101 created in To do\n")
        self.assertEqual(self.sent("POST", "tasks")[0]["body"], {
            "title": "New", "columnId": TODO,
            "description": "<p>[LADO: developer]</p><p><strong>Why:</strong> it "
                           "&lt;breaks&gt;</p>"})

    def test_get_shows_a_created_description_as_markdown(self):
        text = "**Why:** it fails\n\n- one\n  - nested\n\n[site](https://x.org)"
        code, _, err = self.run_yougile("create", "--title", "New", "--description", "-",
                                        stdin=text)
        self.assertEqual(code, 0, err)
        code, out, err = self.run_yougile("get", "DEV-101")
        self.assertEqual(code, 0, err)
        self.assertIn("\nDescription:\n[LADO: developer]\n\n%s\n\nComments" % text, out)

    def test_create_in_a_status_and_by_hand(self):
        with mock.patch.dict(os.environ, {"LADO_AGENT": ""}):
            code, out, _ = self.run_yougile("create", "--title", "New", "--status", "review")
        self.assertEqual(out, "DEV-101 created in Review\n")
        self.assertEqual(self.sent("POST", "tasks")[0]["body"],
                         {"title": "New", "columnId": REVIEW})

    def test_create_failure_says_search_not_get(self):
        self.api.route("POST", "tasks", {"error": "boom"}, status=502)
        err = self.assertFails(yougile.SERVER_ERROR, "may have been applied: look for it with "
                                                     "search --text 'Don'\"'\"'t crash' "
                                                     "before running create again",
                               "create", "--title", "Don't crash")
        self.assertNotIn("check with get", err)

    def test_create_key_not_read_back(self):
        self.api.route("GET", "tasks/" + uid(71), {"error": "x"}, status=500)
        self.assertFails(yougile.SERVER_ERROR, "created, but reading its key failed \\(do "
                                               "not run create again\\)",
                         "create", "--title", "New")

    def test_edit_title_only(self):
        code, out, err = self.run_yougile("edit", "DEV-1", "--title", "Login page")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "DEV-1: title changed\n\nDEV-1  Login page\nStatus: To do\n"
                              "Assignees: unassigned\nLabels: none\n\nDescription:\nMake it\n")
        self.assertEqual(self.sent("PUT", "tasks/" + T1)[0]["body"], {"title": "Login page"})
        self.assertEqual(self.task(T1)["description"], "<p>Make it</p>")

    def test_edit_adds_the_mark_to_a_persons_description(self):
        code, out, err = self.run_yougile("edit", "DEV-1", "--description", "-",
                                          stdin="Make it **now**\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.sent("PUT", "tasks/" + T1)[0]["body"], {
            "description": "<p>[LADO: developer]</p><p>Make it <strong>now</strong></p>"})
        self.assertTrue(out.startswith("DEV-1: description changed\n\nDEV-1  Login form\n"))
        self.assertIn("\nDescription:\n[LADO: developer]\n\nMake it **now**\n", out)
        self.assertNotIn("Comments", out)

    def test_edit_replaces_an_agents_mark(self):
        self.task(T1)["description"] = "<p>[LADO: analyst]</p><p>Old</p>"
        # A mark copied from get with the text is the script's to set, not doubled.
        code, _, err = self.run_yougile("edit", "DEV-1", "--description", "-",
                                        stdin="[LADO: analyst]\n\nNew\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.task(T1)["description"], "<p>[LADO: developer]</p><p>New</p>")

    def test_edit_title_and_description(self):
        code, out, err = self.run_yougile("edit", "DEV-1", "--title", "Login page",
                                          "--description", "Make it now")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("DEV-1: title and description changed\n\nDEV-1  Login "
                                       "page\n"), out)
        self.assertEqual(self.sent("PUT", "tasks/" + T1)[0]["body"], {
            "title": "Login page", "description": "<p>[LADO: developer]</p><p>Make it now</p>"})
        self.assertEqual(len(self.sent("PUT", "tasks/" + T1)), 1)

    def test_edit_already_so(self):
        self.task(T1)["description"] = "<p>[LADO: analyst]</p><p>Make it</p>"
        code, out, err = self.run_yougile("edit", "DEV-1", "--title", "Login form",
                                          "--description", "Make it")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("DEV-1: title and description already so, nothing "
                                       "changed\n\nDEV-1  Login form\n"), out)
        _, out, _ = self.run_yougile("edit", "DEV-1", "--title", "Login page",
                                     "--description", "Make it")
        self.assertTrue(out.startswith("DEV-1: title changed; description already so\n"), out)
        self.assertEqual([r["body"] for r in self.sent("PUT", "tasks/" + T1)],
                         [{"title": "Login page"}])

    def test_edit_already_so_without_inline_code(self):
        # Yougile drops inline code from descriptions: `foo` comes back as foo.
        self.task(T1)["description"] = "<p>[LADO: analyst]</p><p>use foo here</p>"
        code, out, err = self.run_yougile("edit", "DEV-1", "--description", "use `foo` here")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("DEV-1: description already so, nothing changed\n"), out)
        self.assertEqual(self.sent("PUT", "tasks/" + T1), [])

    def test_edit_needs_a_flag_and_text(self):
        self.assertFails(yougile.USAGE, "give --title or --description", "edit", "DEV-1")
        self.assertFails(yougile.USAGE, "the title is empty", "edit", "DEV-1", "--title", " ")
        self.assertFails(yougile.USAGE, "the text is empty", "edit", "DEV-1",
                         "--description", "-", stdin="\n")
        self.assertFails(yougile.USAGE, "the description is empty", "edit", "DEV-1",
                         "--description", "[LADO: developer]")
        self.assertEqual(self.api.requests, [])

    def test_edit_task_of_another_board(self):
        self.task(T2)["columnId"] = FOREIGN
        self.assertFails(yougile.NOT_FOUND, "not found on board 'Dev'", "edit", "DEV-2",
                         "--title", "x")
        self.assertEqual(self.sent("PUT", "tasks/" + T2), [])

    def test_edit_by_hand_has_no_mark(self):
        self.task(T1)["description"] = "<p>[LADO: analyst]</p><p>Old</p>"
        with mock.patch.dict(os.environ, {"LADO_AGENT": ""}):
            code, _, err = self.run_yougile("edit", "DEV-1", "--description", "New")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.task(T1)["description"], "<p>New</p>")

    def test_transition_lists_columns(self):
        code, out, _ = self.run_yougile("transition", "DEV-2")
        self.assertEqual(out, "To do\nIn progress   (current)\nReview\nDone\n")
        self.assertEqual(self.sent("PUT", "tasks/" + T2), [])

    def test_transition_moves_and_comments(self):
        code, out, err = self.run_yougile("transition", "DEV-2", "review", "--comment",
                                          "Ready")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "DEV-2: In progress -> Review, comment 1800000000000 added\n")
        self.assertEqual(self.sent("PUT", "tasks/" + T2)[0]["body"], {"columnId": REVIEW})
        self.assertNotIn("completed", self.task(T2))
        self.assertEqual(self.api.data["messages"][T2][0]["text"],
                         "[LADO: developer]\n\nReady")

    def test_transition_by_column_title_already_there(self):
        code, out, _ = self.run_yougile("transition", "DEV-2", "IN PROGRESS")
        self.assertEqual((code, out), (0, "DEV-2 is already in In progress\n"))
        self.assertEqual(self.sent("PUT", "tasks/" + T2), [])

    def test_task_of_another_board_is_not_found(self):
        self.task(T2)["columnId"] = FOREIGN
        for argv in (("transition", T2, "done"), ("get", "DEV-2"), ("comment", "ID-12", "x")):
            with self.subTest(argv=argv):
                self.assertFails(yougile.NOT_FOUND, "not found on board 'Dev'", *argv)
        self.assertEqual(self.api.data["messages"].get(T2, []), [])

    def test_repeated_titles_show_the_id_everywhere(self):
        self.api.data["columns"].append({"id": uid(16), "title": "review", "boardId": BOARD})
        review = "Review (%s)" % REVIEW
        _, out, _ = self.run_yougile("get", "DEV-4")
        self.assertIn("Status: %s\n" % review, out)
        _, out, _ = self.run_yougile("search", "--status", REVIEW)
        self.assertIn("DEV-4  [%s]  Profile" % review, out)
        _, out, _ = self.run_yougile("create", "--title", "x", "--status", REVIEW)
        self.assertRegex(out, r"created in Review \(%s\)\n$" % REVIEW)
        _, out, _ = self.run_yougile("transition", "DEV-4", REVIEW)
        self.assertEqual(out, "DEV-4 is already in %s\n" % review)
        _, out, _ = self.run_yougile("transition", "DEV-2", REVIEW)
        self.assertEqual(out, "DEV-2: In progress -> %s\n" % review)

    def test_transition_comment_needs_a_target(self):
        self.assertFails(yougile.USAGE, "--comment needs a target", "transition", "DEV-2",
                         "--comment", "Ready")
        self.assertEqual(self.api.requests, [])

    def test_transition_comment_failure_keeps_the_move(self):
        self.api.route("POST", "chats/%s/messages" % T2, {"message": "bad"}, status=400)
        err = self.assertFails(yougile.REFUSED, "DEV-2: In progress -> Done done, but the "
                                                "comment was not added \\(do not run",
                               "transition", "DEV-2", "done", "--comment", "x")
        self.assertIn("fix the text", err)
        self.assertEqual(self.task(T2)["columnId"], DONE)

    def test_comment(self):
        code, out, err = self.run_yougile("comment", "DEV-1", "-", stdin="- a\n- b\n")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "DEV-1: comment 1800000000003 added\n")
        self.assertEqual(self.sent("POST", "chats/%s/messages" % T1)[0]["body"], {
            "text": "[LADO: developer]\n\n- a\n- b\n",
            "textHtml": "<p>[LADO: developer]</p><ul><li>a</li><li>b</li></ul>",
            "label": ""})

    def test_comment_empty_text(self):
        self.assertFails(yougile.USAGE, "the text is empty", "comment", "DEV-1", "-",
                         stdin="  \n")
        self.assertEqual(self.api.requests, [])

    def test_link_is_a_comment(self):
        code, out, _ = self.run_yougile("link", "DEV-1", "https://git.example/pr/7",
                                        "--title", "PR 7")
        self.assertEqual(out, "DEV-1: linked https://git.example/pr/7 in comment "
                              "1800000000003\n")
        self.assertEqual(self.api.data["messages"][T1][-1]["textHtml"],
                         '<p>[LADO: developer]</p><p><a href="https://git.example/pr/7">PR '
                         '7</a></p>')

    def test_link_without_title_is_an_anchor(self):
        url = "https://git.example/o/r/tree/fix/_draft_/x"
        code, out, err = self.run_yougile("link", "DEV-1", url)
        self.assertEqual(code, 0, err)
        message = self.api.data["messages"][T1][-1]
        self.assertEqual(message["textHtml"], '<p>[LADO: developer]</p><p><a href="%s">%s'
                                              '</a></p>' % (url, url))
        self.assertEqual(message["text"], "[LADO: developer]\n\n" + url)

    def test_link_url_refuses_type(self):
        self.assertFails(yougile.USAGE, "--type is for a link between two tasks", "link",
                         "DEV-1", "https://git.example/pr/7", "--type", "blocks")
        self.assertEqual(self.api.requests, [])


class LinkTasksTest(YougileTestCase):
    def link(self, *argv):
        code, out, err = self.run_yougile("link", *argv)
        self.assertEqual(code, 0, err)
        return out

    def texts(self, task):
        return [m["text"] for m in self.api.data["messages"].get(task, [])]

    def test_relates_by_default(self):
        out = self.link("DEV-1", "DEV-2")
        self.assertEqual(out, "DEV-1: linked (relates to DEV-2) in comment 1800000000003\n"
                              "DEV-2: linked (relates to DEV-1) in comment 1800000000000\n")
        message = self.api.data["messages"][T1][-1]
        self.assertEqual(message["text"], "[LADO: developer]\n\n**Link:** relates to DEV-2 "
                                          "«Logout»")
        self.assertEqual(message["textHtml"], "<p>[LADO: developer]</p><p><strong>Link:"
                                              "</strong> relates to DEV-2 «Logout»</p>")
        self.assertEqual(self.texts(T2), ["[LADO: developer]\n\n**Link:** relates to DEV-1 "
                                          "«Login form»"])

    def test_each_word(self):
        cases = {"blocks": ("blocks", "is blocked by"),
                 "duplicates": ("duplicates", "is duplicated by"),
                 "derived": ("derived from", "source of")}
        for word, (there, back) in cases.items():
            with self.subTest(word=word):
                self.api.data["messages"] = {}
                self.link("DEV-1", "DEV-4", "--type", word)
                self.assertEqual(self.texts(T1), ["[LADO: developer]\n\n**Link:** %s DEV-4 "
                                                  "«Profile»" % there])
                self.assertEqual(self.texts(T4), ["[LADO: developer]\n\n**Link:** %s DEV-1 "
                                                  "«Login form»" % back])

    def test_link_types_of_the_project(self):
        self.write_config(CONFIG + "link_types:\n  blocks: 'блокирует / заблокирована'\n"
                                   "  relates: связана с\n  parent: 'parent of / child of'\n")
        self.link("DEV-1", "DEV-2", "--type", "blocks")
        self.link("DEV-1", "DEV-4")
        self.link("DEV-2", "DEV-4", "--type", "parent")
        self.assertEqual([t.split("\n")[-1] for t in self.texts(T1) if "Link" in t],
                         ["**Link:** блокирует DEV-2 «Logout»",
                          "**Link:** связана с DEV-4 «Profile»"])
        self.assertEqual([t.split("\n")[-1] for t in self.texts(T2)],
                         ["**Link:** заблокирована DEV-1 «Login form»",
                          "**Link:** parent of DEV-4 «Profile»"])
        self.assertEqual([t.split("\n")[-1] for t in self.texts(T4)],
                         ["**Link:** связана с DEV-1 «Login form»",
                          "**Link:** child of DEV-2 «Logout»"])

    def test_link_types_wrong(self):
        for value in ("'a / b / c'", "' / b'", "'a / '"):
            with self.subTest(value=value):
                self.write_config(CONFIG + "link_types:\n  blocks: %s\n" % value)
                self.assertFails(yougile.CONFIG, "line 11: 'link_types.blocks' must be "
                                                 "'<in KEY> / <in KEY2>' or one phrase",
                                 "link", "DEV-1", "DEV-2", "--type", "blocks")
        self.assertEqual(self.api.requests, [])

    def test_unknown_word_before_any_request(self):
        self.assertFails(yougile.REFUSED, "link type 'causes' is unknown; the words: "
                                          "blocks, derived, duplicates, relates",
                         "link", "DEV-1", "DEV-2", "--type", "causes")
        self.assertEqual(self.api.requests, [])

    def test_already_linked(self):
        self.link("DEV-1", "DEV-2", "--type", "blocks")
        writes = len(self.sent("POST", "chats/%s/messages" % T1))
        self.assertEqual(self.link("DEV-1", "DEV-2", "--type", "blocks"),
                         "DEV-1: already linked (blocks DEV-2), nothing changed\n")
        self.assertEqual(len(self.sent("POST", "chats/%s/messages" % T1)), writes)
        self.assertEqual(len(self.texts(T2)), 1)

    def test_relates_in_the_reverse_order(self):
        self.link("DEV-1", "DEV-2")
        self.assertEqual(self.link("DEV-2", "DEV-1"),
                         "DEV-2: already linked (relates to DEV-1), nothing changed\n")
        # blocks is not symmetric: the reverse is another link.
        self.link("DEV-1", "DEV-4", "--type", "blocks")
        self.assertIn("linked (blocks DEV-1)", self.link("DEV-4", "DEV-1", "--type", "blocks"))

    def test_line_of_another_agent_or_without_mark(self):
        self.api.data["messages"][T1] = [
            {"id": 5, "text": "[LADO: reviewer]\n\n**Link:** relates to DEV-2 «Logout»"}]
        self.api.data["messages"][T2] = [{"id": 6, "text": "Link: relates to dev-1 «x»"}]
        self.assertEqual(self.link("DEV-1", "DEV-2"),
                         "DEV-1: already linked (relates to DEV-2), nothing changed\n")

    def test_other_task_named_by_either_key(self):
        self.api.data["messages"][T1] = [{"id": 5, "text": "**Link:** relates to ID-12 «x»"}]
        self.api.data["messages"][T2] = [{"id": 6, "text": "**Link:** relates to DEV-1 «x»"}]
        self.assertIn("already linked", self.link("ID-11", "DEV-2"))
        self.assertIn("already linked", self.link("DEV-1", "ID-12"))
        self.assertIn("already linked", self.link(T1, T2))

    def test_no_match_on_a_longer_key_deleted_or_another_phrase(self):
        self.api.data["messages"][T1] = [
            {"id": 5, "text": "**Link:** relates to DEV-21 «x»"},
            {"id": 6, "text": "**Link:** relates to DEV-2 «x»", "deleted": True},
            {"id": 7, "text": "**Link:** blocks DEV-2 «x»"},
            {"id": 8, "text": "see **Link:** relates to DEV-2"}]
        self.assertIn("DEV-1: linked (relates to DEV-2)", self.link("DEV-1", "DEV-2"))

    def test_task_without_project_key_is_found_by_its_id(self):
        self.task(T2)["idTaskProject"] = ""
        out = self.link("DEV-1", T2)
        self.assertIn("DEV-1: linked (relates to %s)" % T2, out)
        self.assertEqual(self.link("DEV-1", T2),
                         "DEV-1: already linked (relates to %s), nothing changed\n" % T2)

    def test_rate_limit_on_the_second_side_advises_only_a_rerun(self):
        self.api.route("POST", "chats/%s/messages" % T2, {"message": "slow"}, status=429)
        err = self.assertFails(yougile.SERVER_ERROR, "linked on DEV-1 \\(comment \\d+\\), "
                                                     "not on DEV-2: .*\\(429\\).*was applied; "
                                                     "run it again$", "link", "DEV-1", "DEV-2")
        self.assertNotIn("report it", err)

    def test_writes_only_the_missing_side(self):
        self.api.data["messages"][T1] = [{"id": 5, "text": "**Link:** blocks DEV-2 «Logout»"}]
        out = self.link("DEV-1", "DEV-2", "--type", "blocks")
        self.assertEqual(out, "DEV-1: already linked (blocks DEV-2) in comment 5\n"
                              "DEV-2: linked (is blocked by DEV-1) in comment 1800000000000\n")
        self.assertEqual(self.sent("POST", "chats/%s/messages" % T1), [])

    def test_second_side_fails(self):
        self.api.route("POST", "chats/%s/messages" % T2, {"message": "bad"}, status=400)
        self.assertFails(yougile.REFUSED, "^yougile.py: linked on DEV-1 \\(comment "
                                          "1800000000003\\), not on DEV-2: Yougile refused "
                                          "the request \\(400\\): bad; run it again$",
                         "link", "DEV-1", "DEV-2")
        del self.api.routes[("POST", "/api-v2/chats/%s/messages" % T2)]
        out = self.link("DEV-1", "DEV-2")
        self.assertEqual(out, "DEV-1: already linked (relates to DEV-2) in comment "
                              "1800000000003\nDEV-2: linked (relates to DEV-1) in comment "
                              "1800000000000\n")
        self.assertEqual(len(self.texts(T1)), 4)

    def test_unclear_answer_advises_running_it_again(self):
        self.api.route("POST", "chats/%s/messages" % T1, {"error": "boom"}, status=502)
        err = self.assertFails(yougile.SERVER_ERROR, "failed \\(502\\): boom; the comment "
                                                     "may have been written: run it again",
                               "link", "DEV-1", "DEV-2")
        self.assertNotIn("check with get", err)
        self.api.routes.clear()
        self.api.route("POST", "chats/%s/messages" % T2, {"error": "boom"}, status=504)
        err = self.assertFails(yougile.SERVER_ERROR, "linked on DEV-1 \\(comment \\d+\\), "
                                                     "not on DEV-2: Yougile failed \\(504\\): "
                                                     "boom; run it again$",
                               "link", "DEV-1", "DEV-2")
        failure = yougile._link_failure(yougile.Yougile._network_failure(TimeoutError(),
                                                                         "POST"), "DEV-2", None)
        self.assertRegex(failure.message, "did not answer.*the comment may have been "
                                          "written: send Yougile nothing more until you are "
                                          "told it answers again, then run it again")
        self.assertNotIn("check with get", failure.message)

    def test_self_link(self):
        self.assertFails(yougile.USAGE, "not linked to itself", "link", "DEV-1", "dev-1")
        self.assertEqual(self.api.requests, [])
        self.assertFails(yougile.USAGE, "DEV-1 and ID-11 are the same task", "link",
                         "DEV-1", "ID-11")
        self.assertEqual(self.sent("POST", "chats/%s/messages" % T1), [])

    def test_task_not_on_the_board(self):
        self.api.data["tasks"].append({"id": uid(35), "idTaskProject": "OPS-1",
                                       "idTaskCommon": "ID-15", "title": "x",
                                       "columnId": FOREIGN})
        self.assertFails(yougile.NOT_FOUND, "task OPS-1 not found on board", "link", "DEV-1",
                         "OPS-1")
        self.assertEqual(self.sent("POST", "chats/%s/messages" % T1), [])

    def test_wrong_arguments_before_any_request(self):
        self.assertFails(yougile.USAGE, "'git.example/pr' is neither a URL", "link", "DEV-1",
                         "git.example/pr")
        self.assertFails(yougile.USAGE, "--title is for a URL", "link", "DEV-1", "DEV-2",
                         "--title", "x")
        self.assertEqual(self.api.requests, [])

    def test_chat_read_page_after_page(self):
        self.api.data["messages"][T1] = [{"id": n, "text": "note"} for n in range(1500)] + [
            {"id": 2000, "text": "**Link:** relates to DEV-2 «x»"}]
        self.api.data["messages"][T2] = [{"id": 1, "text": "**Link:** relates to DEV-1 «x»"}]
        self.assertIn("already linked", self.link("DEV-1", "DEV-2"))
        self.assertEqual([r["query"]["offset"] for r in
                          self.sent("GET", "chats/%s/messages" % T1)], ["0", "1000"])

    def test_title_is_escaped_in_html(self):
        self.task(T2)["title"] = "a <b> & *c*"
        self.link("DEV-1", "DEV-2")
        self.assertEqual(self.api.data["messages"][T1][-1]["textHtml"],
                         "<p>[LADO: developer]</p><p><strong>Link:</strong> relates to DEV-2 "
                         "«a &lt;b&gt; &amp; *c*»</p>")


class LinkUrlTest(YougileTestCase):
    def test_assign_me_and_none(self):
        code, out, err = self.run_yougile("assign", "DEV-1", "me")
        self.assertEqual((code, out), (0, "DEV-1: assignee unassigned -> Agent Smith "
                                          "(agent@example.com)\n"), err)
        self.assertEqual(self.task(T1)["assigned"], [ME])
        _, out, _ = self.run_yougile("assign", "DEV-1", "me")
        self.assertEqual(out, "DEV-1: assignee Agent Smith (agent@example.com) already, "
                              "nothing changed\n")
        _, out, _ = self.run_yougile("assign", "DEV-1", "none")
        self.assertEqual(out, "DEV-1: assignee Agent Smith (agent@example.com) -> "
                              "unassigned\n")
        self.assertEqual(self.task(T1)["assigned"], [])

    def test_assign_by_email(self):
        code, out, _ = self.run_yougile("assign", "DEV-4", "ann@example.com")
        self.assertEqual(out, "DEV-4: assignee Agent Smith (agent@example.com) -> Ann Lee "
                              "(ann@example.com)\n")
        self.assertEqual(self.task(T4)["assigned"], [ANN])

    def test_assign_refuses_a_task_another_holds(self):
        self.assertFails(yougile.REFUSED, "DEV-2 is assigned to Ann Lee \\(ann@example.com\\), "
                                          "another account: not changed.*--reassign",
                         "assign", "DEV-2", "me")
        self.assertEqual(self.sent("PUT", "tasks/" + T2), [])
        code, out, _ = self.run_yougile("assign", "DEV-2", "me", "--reassign")
        self.assertEqual(code, 0)
        self.assertEqual(self.task(T2)["assigned"], [ME])

    def test_assign_unknown_email(self):
        self.assertFails(yougile.REFUSED, "no account with the email bob@example.com.*never "
                                          "guessed", "assign", "DEV-1", "bob@example.com")
        self.assertEqual(self.sent("PUT", "tasks/" + T1), [])

    def test_label_add_and_remove(self):
        code, out, err = self.run_yougile("label", "DEV-4", "--add", "waiting for release")
        self.assertEqual((code, out), (0, "DEV-4: labels waiting for release\n"), err)
        self.assertEqual(self.sent("PUT", "tasks/" + T4)[0]["body"],
                         {"stickers": {PRIORITY: "hi", RELEASE: "wait"}})
        _, out, _ = self.run_yougile("label", "DEV-4", "--add", "waiting for release")
        self.assertEqual(out, "DEV-4: labels waiting for release, nothing changed\n")
        _, out, _ = self.run_yougile("label", "DEV-4", "--remove", "waiting for release",
                                     "--add", "shipped")
        self.assertEqual(out, "DEV-4: labels shipped\n")
        _, out, _ = self.run_yougile("label", "DEV-4", "--remove", "shipped")
        self.assertEqual(out, "DEV-4: labels none\n")
        self.assertEqual(self.sent("PUT", "tasks/" + T4)[-1]["body"],
                         {"stickers": {PRIORITY: "hi", RELEASE: "-"}})
        self.assertEqual(self.task(T4)["stickers"], {PRIORITY: "hi"})

    def test_label_remove_leaves_another_state(self):
        self.task(T4)["stickers"] = {RELEASE: "ship"}
        _, out, _ = self.run_yougile("label", "DEV-4", "--remove", "waiting for release")
        self.assertEqual(out, "DEV-4: labels shipped, nothing changed\n")

    def test_label_unmapped_word_before_any_request(self):
        self.assertFails(yougile.CONFIG, "label 'urgent' is not in 'labels'",
                         "label", "DEV-4", "--add", "urgent")
        self.assertEqual(self.api.requests, [])

    def test_label_stale_mapping_of_another_word(self):
        self.write_config(CONFIG + "  gone: 'Release: Lost'\n")
        code, out, err = self.run_yougile("label", "DEV-4", "--add", "shipped")
        self.assertEqual((code, out), (0, "DEV-4: labels shipped\n"), err)
        _, out, _ = self.run_yougile("get", "DEV-4")
        self.assertIn("Labels: shipped\n", out)

    def test_label_mapping_not_on_board(self):
        self.write_config("board: Dev\nlabels:\n  x: 'Release: Lost'\n")
        self.assertFails(yougile.CONFIG, "sticker 'Release' has no state 'Lost'.*Waiting, "
                                         "Shipped", "label", "DEV-4", "--add", "x")


class ErrorsTest(YougileTestCase):
    def test_key_unset(self):
        with mock.patch.dict(os.environ, {"YOUGILE_API_KEY": ""}):
            self.assertFails(yougile.SETUP, "YOUGILE_API_KEY not set", "whoami")

    def test_url_must_be_https_or_loopback(self):
        for url in ("http://yougile.example.com", "ftp://x", "https://x:port"):
            with self.subTest(url=url), mock.patch.dict(os.environ, {"YOUGILE_URL": url}):
                self.assertFails(yougile.SETUP, "YOUGILE_URL", "whoami")

    def test_key_refused_is_not_retried(self):
        self.api.route("GET", "users/me", {"statusCode": 401, "message": "Unauthorized"},
                       status=401)
        self.assertFails(yougile.KEY_REFUSED, "refused the API key.*not retried.*every "
                                              "agent to stop using Yougile", "whoami")
        self.assertEqual(len(self.api.requests), 1)

    def test_rate_limit_waits_once(self):
        self.api.route("GET", "users/me", Seq(
            (429, {"Retry-After": "7"}, {"message": "Too Many Requests"}),
            (200, {}, {"id": ME, "realName": "Agent Smith", "email": "agent@example.com"})))
        code, out, err = self.run_yougile("whoami")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.sleeps, [7])
        self.assertEqual(len(self.api.requests), 2)

    def test_rate_limit_twice(self):
        self.api.route("GET", "users/me", {"message": "Too Many Requests"}, status=429,
                       headers={"Retry-After": "600"})
        self.assertFails(yougile.SERVER_ERROR, "rate limiting.*nothing of this request was "
                                               "applied", "whoami")
        self.assertEqual(self.sleeps, [60])
        self.assertEqual(len(self.api.requests), 2)

    def test_rate_limit_without_retry_after(self):
        self.assertEqual(yougile._retry_after(None), 60)
        self.assertEqual(yougile._retry_after("Wed, 21 Oct 2026 07:28:00 GMT"), 60)

    def test_no_access(self):
        self.api.route("GET", "tasks/" + T1, {"message": "Forbidden"}, status=403)
        self.assertFails(yougile.NO_ACCESS, "no access \\(403\\): Forbidden", "get", T1)

    def test_not_found_by_id(self):
        self.assertFails(yougile.NOT_FOUND, "task %s not found on board .Dev." % uid(99),
                         "get", uid(99))

    def test_refused_request(self):
        self.api.route("PUT", "tasks/" + T1, {"message": ["columnId must be a string"],
                                              "error": "Bad Request"}, status=400)
        self.assertFails(yougile.REFUSED, "refused the request \\(400\\): columnId must be a "
                                          "string; Bad Request", "transition", "DEV-1", "done")

    def test_server_error_on_write_may_be_applied(self):
        self.api.route("POST", "chats/%s/messages" % T1, {"error": "boom"}, status=502)
        self.assertFails(yougile.SERVER_ERROR, "failed \\(502\\): boom; the change may have "
                                               "been applied: check with get",
                         "comment", "DEV-1", "x")

    def test_not_yougile(self):
        self.api.route("GET", "users/me", Raw(b"<html>nope</html>"), status=404)
        self.assertFails(yougile.SETUP, "not Yougile's API", "whoami")
        self.api.route("GET", "users/me", Raw(b"<html>ok</html>"))
        self.assertFails(yougile.SETUP, "not Yougile's API", "whoami")

    def test_redirect_not_followed(self):
        self.api.route("GET", "users/me", None, status=302, headers={"Location": "/login"})
        self.assertFails(yougile.SETUP, "redirect \\(302\\), not followed", "whoami")

    def test_unreachable(self):
        self.api.close()
        err = self.assertFails(yougile.UNREACHABLE, "not reachable.*send Yougile nothing "
                                                    "more", "get", T1)
        self.assertNotIn("applied", err)
        # A write that got no answer may have been applied.
        failure = yougile.Yougile._network_failure(ConnectionResetError(), "POST")
        self.assertEqual(failure.code, yougile.UNREACHABLE)
        self.assertIn("the change may have been applied", failure.message)

    def test_settings_missing_or_wrong(self):
        self.write_config("board: Dev\nstatuses:\n  - a\n")
        self.assertFails(yougile.CONFIG, "line 3: lists are not supported", "search")
        self.assertEqual(self.api.requests, [])
        os.remove(os.path.join(self.repo, ".lado", "tracker.yaml"))
        self.assertFails(yougile.CONFIG, "tracker.yaml not found", "search")

    def test_usage(self):
        code, _, _ = self.run_yougile("label", "DEV-1")
        self.assertEqual(code, yougile.USAGE)
        code, _, _ = self.run_yougile("frobnicate")
        self.assertEqual(code, yougile.USAGE)


@unittest.skipUnless(shutil.which("openssl"), "needs the openssl command")
class TlsTest(YougileTestCase):
    def setUp(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder)
        self.cert = os.path.join(folder, "cert.pem")
        key = os.path.join(folder, "key.pem")
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", key, "-out", self.cert, "-days", "2",
                        "-subj", "/CN=127.0.0.1",
                        "-addext", "subjectAltName=IP:127.0.0.1"],
                       check=True, capture_output=True)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert, key)
        super().setUp()
        self.api.close()
        self.api = FakeYougile(tls_context=context)
        self.addCleanup(self.api.close)
        os.environ["YOUGILE_URL"] = self.api.url

    def test_untrusted_certificate(self):
        with mock.patch.dict(os.environ, {"SSL_CERT_FILE": ""}):
            self.assertFails(yougile.TLS, "SSL_CERT_FILE", "whoami")

    def test_trusted_through_ssl_cert_file(self):
        with mock.patch.dict(os.environ, {"SSL_CERT_FILE": self.cert}):
            code, out, err = self.run_yougile("whoami")
        self.assertEqual(code, 0, err)
        self.assertIn("Agent Smith", out)


if __name__ == "__main__":
    unittest.main()
