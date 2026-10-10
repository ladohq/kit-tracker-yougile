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
            {"id": T1, "idTaskProject": "DEV-1", "title": "Login form", "columnId": TODO,
             "assigned": [], "description": "<p>Make it</p>"},
            {"id": T2, "idTaskProject": "DEV-2", "title": "Logout", "columnId": PROGRESS,
             "assigned": [ANN]},
            {"id": T3, "idTaskProject": "DEV-3", "title": "Old login", "columnId": PROGRESS,
             "assigned": [], "archived": True},
            {"id": T4, "idTaskProject": "DEV-4", "title": "Profile", "columnId": REVIEW,
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
                        % (100 + self.created), assigned=[])
            self.data["tasks"].append(task)
            return 201, {"id": task["id"]}
        if parts[0] == "tasks" and len(parts) == 2:
            task = self.find("tasks", parts[1])
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
            "board: A\nstatuses:\n  - a\n": "line 3: block lists",
            "board: A\nstatuses:\n  a:\n    b: c\n": "line 3: .*one level",
            "board A\n": "line 1: expected 'key: value'",
            "board: A\nboard: B\n": "line 2: 'board' is given twice",
            "board: 'A\n": "line 1: .*same quote",
            "board: A\n  x: y\n": "line 2: unexpected indent",
            "board: {a: b}\n": "line 1: .*flow maps",
            "board: A\nproject: B\n": "line 2: unknown key 'project'",
            "board: A\nlabels:\n  x: NoState\n": "line 3: 'labels.x' must be 'Sticker: State'",
            "board: A\nstatuses: [a]\n": "line 2: 'statuses' must be a map",
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

    def test_lists_are_read_page_after_page(self):
        self.api.data["tasks"] += [
            {"id": uid(500 + n), "idTaskProject": "DEV-%d" % (500 + n), "title": "t",
             "columnId": DONE, "assigned": []} for n in range(1001)]
        code, out, err = self.run_yougile("get", "DEV-1500")
        self.assertEqual(code, 0, err)
        self.assertIn("DEV-1500  t", out)
        offsets = [r["query"]["offset"] for r in self.sent("GET", "task-list")
                   if r["query"]["columnId"] == DONE]
        self.assertEqual(offsets, ["0", "1000"])

    def test_search_unknown_status(self):
        self.assertFails(yougile.REFUSED, "status 'qa' is not a column of the board; its "
                                          "columns: To do, In progress, Review, Done",
                         "search", "--status", "qa")

    def test_get_by_key(self):
        code, out, err = self.run_yougile("get", "dev-1", "--comments", "2")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, (
            "DEV-1  Login form\nStatus: To do\nAssignees: unassigned\nLabels: none\n"
            "\nDescription:\n<p>Make it</p>\n"
            "\nComments: 3, the last 2 shown\n"
            "\n--- comment 1700000000002, Ann Lee (ann@example.com), 2023-11-14 22:13 UTC\n"
            "note 2\n"
            "\n--- comment 1700000000003, Ann Lee (ann@example.com), 2023-11-14 22:13 UTC\n"
            "note 3\n"))
        self.assertEqual(self.sent("GET", "chats/%s/messages" % T1)[0]["query"]["limit"],
                         "1000")

    def test_get_by_id_without_settings(self):
        os.remove(os.path.join(self.repo, ".lado", "tracker.yaml"))
        code, out, err = self.run_yougile("get", T2)
        self.assertEqual(code, 0, err)
        self.assertIn("DEV-2  Logout\nStatus: In progress\n", out)
        self.assertNotIn("Labels", out)
        self.assertEqual(self.sent("GET", "task-list"), [])

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

    def test_create_in_a_status_and_by_hand(self):
        with mock.patch.dict(os.environ, {"LADO_AGENT": ""}):
            code, out, _ = self.run_yougile("create", "--title", "New", "--status", "review")
        self.assertEqual(out, "DEV-101 created in Review\n")
        self.assertEqual(self.sent("POST", "tasks")[0]["body"],
                         {"title": "New", "columnId": REVIEW})

    def test_create_key_not_read_back(self):
        self.api.route("GET", "tasks/" + uid(71), {"error": "x"}, status=500)
        self.assertFails(yougile.SERVER_ERROR, "created, but reading its key failed \\(do "
                                               "not run create again\\)",
                         "create", "--title", "New")

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

    def test_transition_task_of_another_board(self):
        self.task(T2)["columnId"] = FOREIGN
        self.assertFails(yougile.REFUSED, "is not on board 'Dev'", "transition", T2, "done")

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
        self.assertFails(yougile.NOT_FOUND, "task %s not found \\(404\\)" % uid(99),
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
        self.assertFails(yougile.CONFIG, "line 3: block lists", "search")
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
