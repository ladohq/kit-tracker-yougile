# Blueprint: tracker-yougile

A LADO kit that lets the roles of any process kit work with a Yougile tracker
(yougile.com, REST API v2), while LADO's core knows nothing about trackers. It has no
agents and no flows: it provides one skill, `tracker`, that a session adds next to a
process kit (`lado start <repo> --kit <process-kit> --kit tracker-yougile`). The skill
reaches Yougile through a script in its own folder; each project keeps its own settings
in its repository. It is the Yougile counterpart of `tracker-jira-server` 1.2.0
(github.com/ladohq/kit-tracker-jira-server), and keeps its action names, so a process
kit's text fits both.

Sources: `BRIEF.md` at the repository root (commit ca6bcac); the design round of run
`create/tracker-yougile` (session `tracker-yougile`, LADO messages #2347, the answers
to questions #2363 and #2382, the reason of the first `design_ok` reject); Yougile's OpenAPI description `https://ru.yougile.com/api-json`
("YouGile REST API v2.0", read 2026-10-10), cited below as "API".

## 1. Requirements

- **R1** The kit is universal: it works for any Yougile company, project and board, not
  for one. Nothing company- or project-specific (ids, board, column or sticker names) is
  in the skill's text or the script. The kit and its texts are in English and published
  as `github.com/ladohq/kit-tracker-yougile` in the official marketplace.
  *Source:* brief, "What to carry over"; design round, Q11 ("согласен").
- **R2** The kit has no agents, no flows and no `supervisor:`; it provides exactly one
  skill, named `tracker`, so a process kit's roles say "use the tracker skill" and a role
  that cannot work without it lists `skills: [tracker]`. *Source:* brief, "What to carry
  over".
- **R3** The skill does nine actions, with the names `tracker-jira-server` uses, and says
  in its own words how to do each; the description and the Actions table of SKILL.md name
  every action, since a process kit decides from them whether to ask the human:
  - `search`: tasks of the project's board, filtered by status (a column or a word of
    `statuses`), assignee (`me`, an email, or `none`) and words of the title, paged by
    `--start`/`--max`; archived tasks left out. Yougile has no query language (API,
    `GET /api-v2/task-list`: filters `columnId`, `assignedTo`, `title`, sticker only), so
    the script asks per column of the board.
  - `get`: key, title, status (the column), assignees, description, and the latest
    messages of the task's chat, each with its id (the id `comment` prints).
  - `create`: title, description, optional status (default: the board's first column);
    prints the new task's key.
  - `transition`: without a target, lists the columns of the board the task can move to
    (its current one marked); with a target (a column title or a word of `statuses`),
    moves the task by changing its column. A task already there changes nothing and says
    so (success). `--comment` posts a comment after the move. Moving does not touch
    Yougile's "completed" flag.
  - `comment`: posts a message to the task's chat and prints its id.
  - `assign`: to the account `whoami` names (`me`), to an email, or `none`; the task then
    has exactly that assignee. Already so is success; prints before -> after. A task
    another account holds is refused with that account named, unless `--reassign`, which
    the agent passes only when the human or its step says so. An unknown email is
    reported, never guessed.
  - `label`: `--add`/`--remove` of label words that `labels` in the settings maps to a
    sticker state (R6); add sets that state, remove takes the sticker off the task; other
    stickers untouched; already so is success; prints the task's mapped labels. A word the
    settings do not map is refused (exit 3) before any request.
  - `link`: posts the URL (and an optional title) as a comment and prints its id; Yougile
    has no link object.
  - `whoami`: the account the key belongs to (`GET /api-v2/users/me`), as
    `Real Name (email)`, never the key.
  Assignees are shown everywhere as `Real Name (email)`, an unassigned task as
  `unassigned`, so a task's assignee compares with `whoami`. Nothing else (no delete,
  boards, sprints, checklists, files); more is added when a project needs it.
  *Source:* brief, "The contract `tracker` must keep" 1–7; design round Q3, Q4, Q5, Q6,
  Q8 ("согласен"); link: the human's answer to #2363, "Только комментарий"; the research
  before it: the API has no external-link object and no GitHub/GitLab binding.
- **R4** Tasks are named by the key people see in Yougile, `idTaskProject` (e.g.
  `DEV-484`): the script prints it everywhere and accepts it in every action; it also
  accepts the task's id (a UUID). The key is short and stable, as process kits use it to
  name runs, branches and changes. The API documents `GET /api-v2/tasks/{id}` by id and
  has no filter by key, so the script finds a key among the board's tasks; a key not on
  the board is "not found" (exit 7). *Source:* brief, "Task keys"; design round Q3.
- **R5** No MCP server. The skill reaches Yougile with `skills/tracker/yougile.py`, on
  Python's standard library only, run by `uv` (`uv run --quiet --script`, inline metadata
  naming the Python and no dependencies). `kit.yaml` names `uv` in `expects.commands`,
  with `dependencies.lado: ">=0.30"`. *Source:* brief, "What to carry over";
  `tracker-jira-server` R4.
- **R6** A project's settings live in its repository, `.lado/tracker.yaml`, read only by
  the script, found from the current directory up to the repository root, in the strict
  YAML subset of `tracker-jira-server` (`key: value` lines, one level of nested maps,
  inline `[a, b]` lists, `#` comments; anything else stops it with the path, the line and
  what is wrong). Only `board` is required: the board's id, or its title when that title
  is unique in the company (otherwise the script names the matching boards and asks for
  the id). Optional: `statuses` (a word process kits use -> a column title of the board;
  the example maps `in progress`, `review`, `done`), `labels` (a label word -> `Sticker:
  State`, a sticker with states on the board). An action that needs a missing setting
  names it. *Source:* brief, "What to carry over", "Statuses", "Labels"; design round
  Q4, Q6.
- **R7** Credentials come from the agent's environment, inherited from the user's login
  shell: `YOUGILE_API_KEY` (sent as `Authorization: Bearer`), and `YOUGILE_URL`,
  optional, default `https://yougile.com`, for another address of the same API v2 (a
  company's self-hosted Yougile, which serves the same API, by default on port 8001);
  the README names which of cloud and self-hosted were tried (R12). `YOUGILE_URL` is
  `https://`, or `http://` to localhost for tests. The script never asks for, prints or
  writes the key; it never sees the user's password. The README shows how to make a key
  once (`POST /api-v2/auth/companies`, then `POST /api-v2/auth/keys`, with curl) and keep
  it in the OS keychain, read in the profile (macOS `security` example, the "Always
  Allow" note of `tracker-jira-server`). TLS is verified through the system store or
  `SSL_CERT_FILE`, never disabled. *Source:* brief, "Login"; design round Q1, Q2
  ("согласен").
- **R8** What agents write in Yougile in the user's name is marked by the script: every
  comment and every created task's description starts with `[LADO: <agent>]`, the name
  taken from `LADO_AGENT`; none when it is unset (run by hand). SKILL.md says how the
  mark shows in `get`. *Source:* brief, "What to carry over".
- **R9** Agents write the text they send (`comment`, `link --title`, `create
  --description`, `transition --comment`) in Markdown; the script converts it to HTML
  (headings, bold, italic, inline code, fenced code blocks, bullet and numbered lists,
  links) for the description and the message's `textHtml`, and sends the Markdown as
  the message's plain `text` (the API requires both). If the converter fails, the text is
  sent escaped as plain paragraphs. `get` shows text as Yougile keeps it, with no reverse
  conversion. *Source:* brief, "Text format"; design round Q9 ("согласен").
- **R10** One default write scope in SKILL.md: reading is always fine; create,
  transition, comment, assign, label or link only when the agent's role, its step or the
  human asks, and only on the tasks named. A process kit may allow more. *Source:* brief,
  "What to carry over"; `tracker-jira-server` R11.
- **R11** Each failure is one plain line saying what happened and what to do, with an
  exit code per kind, keeping `tracker-jira-server`'s table where the meaning is the same
  (2 arguments, 3 settings, 4 variable unset or `YOUGILE_URL` wrong, 5 key refused, 6 no
  access, 7 not found, 9 not reachable, 10 TLS, 11 refused request, 12 server error or
  rate limit, 1 crash). A refused key (401) is never retried, and its message says every
  agent stops using Yougile until the human fixes the key. The API allows 50 requests a
  minute per company (API, "Как использовать"): on 429 the script waits once (the
  `Retry-After` it gets, at most 60 s) and repeats that request once, since a 429 means
  it was not applied; a second 429 is exit 12. SKILL.md tells the agent what to do on each
  code, as `tracker-jira-server`'s does: after exit 9 send Yougile nothing more until told
  it answers again; after a crash or a 5xx on a write, `get` before running it again; a
  message from `uv` or Python before the script ran means nothing reached Yougile.
  *Source:* brief, "Exit codes", "Rate limits"; design round Q9; `tracker-jira-server`
  R8 and the findings in its `kit-reports/`.
- **R12** The script is tested against a fake Yougile on localhost (standard library
  `unittest` and `http.server`, as `tests/test_jira.py` of `tracker-jira-server`): its
  requests, key lookup, the YAML subset, the mark, Markdown to HTML, 429 and every error
  path. Before the release the kit is tried on a real Yougile: Yougile's self-hosted
  server, run locally in Docker from files in the kit's repository
  (`tests/yougile-server/`), reached at `http://localhost:8001`. Its distribution is
  Linux x64 only (`https://dist.yougile.com/linux/latest/yougile.tar.gz`, started by
  `./server`, port 8001; Yougile's install guide
  `https://ru.yougile.com/media/docs/yougile-linux-ru.pdf`), so on an arm64 Mac the
  container runs as `linux/amd64` under emulation. The README of `tests/yougile-server/`
  says how to start it, make the first company, account and key, and a board for the
  trial. The facts the API leaves open (whether `GET /tasks/{id}` takes a key, that a
  task's chat id is the task's id, the shape of 401 and 429 answers) are checked there;
  until then the script relies only on what the API documents. If the self-hosted server
  cannot run without a license Yougile does not give for tests, the author reports it and
  the trial moves to the cloud, with the human. The cloud is tried when an account is at
  hand; that is not a condition of the release.
  *Source:* brief, "What to carry over"; design round Q10 ("решим в процессе работы");
  the human at the first `design_ok` gate (rejected: "Сможем ли мы поднять для
  тестирования свой yougile сервер? Желательно в Docker") and the answer to #2382 ("Да:
  Docker-коробка в репо и проба на ней").

Decided in the design round, not requirements of this kit: the shared contract of status
words between process and tracker kits stays with `sdlc` (its backlog, R16); this kit's
example of `statuses` uses the words `in progress`, `review`, `done`.

## 2. Starting point

No archetype: the kit has no roles and no flows, so no team shape applies. It is a skill
pack, the shape of `tracker-jira-server` 1.2.0, carried over as the brief lists: one
skill `tracker`, one standard-library script run by `uv`, credentials from the login
shell, the mark, the write scope, the project settings file, Markdown in, one line and
one exit code per failure, tests against a fake server. What differs follows Yougile's
API: statuses are a board's columns (R3, R6), search has filters instead of a query
language (R3), the key is `idTaskProject` found on the board (R4), labels are sticker
states (R6), a link is a comment (R3), text is HTML (R9), and the rate limit is waited
out once (R11).

Flow skeletons: none; the kit has no flows (R2), so there are no diagrams.

## 3. Traceability

| Element | Kind | Covers | Why it exists / why nothing simpler |
|---|---|---|---|
| `kit.yaml` | manifest | R1, R2, R5 | name, version, description naming the nine actions; `expects.commands: [uv]`, `dependencies.lado: ">=0.30"`; no `supervisor:`, no `dependencies.skills` |
| `uv` | command (expects) | R5 | runs `yougile.py` with the Python its metadata names on every project; a session without it does not start instead of failing at the first action |
| `tracker` (`skills/tracker/SKILL.md`) | skill | R1, R2, R3, R4, R6, R8, R9, R10, R11 | the one skill the convention names; how to run each action, keys, Markdown, the settings with an example, the write scope, what each exit code means and what to do |
| `skills/tracker/yougile.py` | skill script | R3, R4, R5, R6, R7, R8, R9, R11 | the only way to Yougile without MCP; one file, standard library only; the nine commands, key lookup, settings, Markdown to HTML, the mark, the error table and the 429 wait |
| `tests/test_yougile.py` | tests (outside the skill) | R11, R12 | checks the script against a fake Yougile before any real board; outside `skills/` so it does not ship into agents' skill folders |
| `tests/yougile-server/` | test environment (outside the skill) | R7, R12 | a Dockerfile and compose file that run Yougile's self-hosted server on localhost, with a README on making the company, account, key and trial board; the only real Yougile the trial can rely on without a cloud account; outside `skills/`, so agents never get it |
| `README.md` | doc | R1, R2, R5, R7 | how to add the kit, that `uv` is required, how to make and keep the key, `YOUGILE_URL`, and how to write `.lado/tracker.yaml` |

Reverse check:
- R1: `kit.yaml`, `tracker` skill, `README.md` (no project values anywhere).
- R2: `kit.yaml`, `tracker` skill, `README.md`.
- R3: `tracker` skill, `yougile.py`.
- R4: `tracker` skill, `yougile.py`.
- R5: `kit.yaml`, `uv`, `yougile.py`, `README.md`.
- R6: `tracker` skill, `yougile.py`.
- R7: `yougile.py`, `README.md`, `tests/yougile-server/`.
- R8: `tracker` skill, `yougile.py`.
- R9: `tracker` skill, `yougile.py`.
- R10: `tracker` skill.
- R11: `tracker` skill, `yougile.py`, `tests/test_yougile.py`.
- R12: `tests/test_yougile.py`, `tests/yougile-server/`; the trial itself is done in
  the run before the release, not a kit file.

## 4. Complexity budget

Planned, counted by hand; replaced by the `kit-budget` script's output after the build.

| Measure | Value | Zone | Reason, when not green |
|---|---|---|---|
| Worker roles (not supervisor) | 0 | green | |
| Work steps in a flow | 0 (no flows) | green | |
| Gates in a flow | 0 (no flows) | green | |
| Words in the longest role prompt | 0 (no roles) | green | |
| Own skills | 1 | green | |
| MCP servers | 0 | green | |

## 5. Change log

How the kit changed and the fact that caused it, newest first. Empty for a new kit.

| Date | Version | Change | ← Fact (session, run, metric or report) |
|---|---|---|---|
