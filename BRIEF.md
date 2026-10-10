# Brief: the tracker kit for Yougile (`tracker-yougile`)

Written by the supervisor of LADO session `yougile` on 2026-10-10, from the human's
messages there, so that the session that builds this kit starts from what is already
known. It is input for the interview, not a decision: the human settles everything below
in the `design` step of the flow `create`.

## What the human asked for

"We have a tracker kit for working with Jira. I want to make another tracker kit for
working with Yougile." So the interview takes the branch where a sibling kit already
exists: `tracker-jira-server` is the model, and the new kit should be its counterpart
for Yougile (yougile.com, its REST API v2).

## The model: `tracker-jira-server` 1.2.0

Repository `~/Projects/kit-tracker-jira-server` (github.com/ladohq/kit-tracker-jira-server,
in the official marketplace). Read before the interview: `BLUEPRINT.md` (requirements
R1–R16 with their sources), `README.md`, `skills/tracker/SKILL.md`, `skills/tracker/jira.py`,
`tests/test_jira.py`, `BACKLOG.md` and the reports in `kit-reports/` (what the critic found
in each version, so the new kit does not repeat it).

What to carry over, unless the human decides otherwise:

- A kit with no agents, no flows and no `supervisor:`; it gives exactly one skill named
  **`tracker`**, so it pairs with any process kit: `lado start <repo> --kit sdlc --kit
  tracker-yougile`.
- `dependencies.lado: ">=0.30"`, `expects.commands: [uv]`; one script on Python's standard
  library, run with `uv run --quiet --script`; no MCP server.
- Credentials only from variables of the user's login shell (LADO's agents inherit it);
  never asked for, printed or written to a file; a key kept in the OS keychain, not in
  the profile (README's macOS example).
- Every comment and every created task's description starts with `[LADO: <agent>]`
  (`LADO_AGENT`); none when run by hand.
- Reading is always allowed; writes only when the role, the step or the human asks, and
  only on the tasks named.
- Project settings committed in the project's repository, `.lado/tracker.yaml`, in the
  same strict YAML subset; only what Yougile needs is required.
- Agents write Markdown; the script converts it to what the tracker keeps.
- Exit codes with a line that says what to do; a failed login is never retried.
- Tests of the script against a fake HTTP server (as `tests/test_jira.py`).

## The contract `tracker` must keep (what `sdlc` 0.3.0 asks of it)

`sdlc` (`~/Projects/kit-sdlc`) names no tracker's commands; it asks `tracker` by meaning
(`skills/sdlc-settings/SKILL.md`, "Writing to the tracker"; README, "Install and start"):

1. read a task with its comments, each comment with its id;
2. list the statuses a task can move to, and move it to one ("in progress", "review",
   "done" by meaning);
3. post a comment in Markdown and report the new comment's id;
4. link a URL (a pull request) to a task, else the URL goes as a comment;
5. assign a task, and say which account the skill works as (`whoami`);
6. add or remove a label (sdlc's "waiting for release");
7. find tasks; create a task (only on the human's explicit yes).

Every write must be checkable by reading back what `tracker` reports (an id, the new state,
"already so"). The task key becomes the name of runs, branches and openspec changes
(sdlc's "The task key as a name"), so the key the skill shows must be stable and short.
Keep the action names of `tracker-jira-server` where the meaning is the same, so a
process kit's text fits both trackers; where Yougile cannot do one, the skill says so and
what the agent does instead. The `sdlc` backlog asks for a shared contract of status
words between process and tracker kits (its R16); the interview may decide whether this
kit writes that contract down.

## Where Yougile differs (to check against its API docs, not settled)

From the supervisor's general knowledge of Yougile's REST API v2; verify each point
(yougile.com/api-v2 documentation) before the blueprint relies on it:

- **Login.** A bearer API key, made once from login, password and company id; the
  variables (e.g. `YOUGILE_API_KEY`, and the server address for a self-hosted Yougile, if
  that exists) are for the interview.
- **Statuses** are the columns of a board; a task moves by changing its column.
  `statuses` in `.lado/tracker.yaml` would map words to columns (and boards).
- **Search** has no query language like JQL: filters by column, assignee, title. The
  action keeps its name; its arguments differ.
- **Comments** are the task's chat messages; check that a message has an id to report.
- **Labels**: Yougile has stickers (with fixed values) instead of free labels; decide what
  `label` means here.
- **Links**: probably no remote-link object; a URL as a comment, or a field.
- **Task keys**: tasks have an internal id and a human-readable key; decide which the
  agents see and use.
- **Text format**: descriptions and messages are HTML, not Jira wiki markup.
- **Rate limits** on the API; how the script waits or fails.
- **Self-hosted vs cloud**, API versions to support.

## Open questions for the human

1. Cloud only (ru.yougile.com / yougile.com), or also a self-hosted Yougile?
2. Which Yougile project and board to try the kit on, and with which account?
3. What `label` should map to (a sticker and its value, or nothing).
4. Which task key the agents use (the one people see in Yougile's UI).
5. Whether the action set must equal `tracker-jira-server`'s exactly, or only cover the
   contract above.
6. Publish to github.com/ladohq and the official marketplace, as the Jira kit was?

## Out of scope

Changes to LADO itself, to `sdlc` and to `tracker-jira-server` (each is its own session
and kit; findings for them go to their BACKLOG.md through the human).
