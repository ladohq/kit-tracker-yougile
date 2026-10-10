# kit-tracker-yougile

A LADO kit for Yougile (yougile.com, or a company's self-hosted Yougile) through its REST
API v2. It gives the roles of any process kit a skill named `tracker` that searches,
reads, creates, moves, comments on, assigns and labels tasks, links a URL to them and
says which account it works as, through a script on Python's standard library, run by
`uv` (no MCP server). The skill's actions have the names of `tracker-jira-server`'s, so a
process kit's text fits both.

The kit has no agents and no flows: it adds the skill to a session led by a process kit.
A process kit's roles say "use the tracker skill"; a role that cannot work without it
lists `skills: [tracker]`, so a session without a tracker kit refuses to start.

Where it was tried: so far only against a fake Yougile in its tests. The trial on a live
board in Yougile's cloud comes before the first release. Only the cloud is tried: a
self-hosted Yougile (`YOUGILE_URL`) serves the same API but has not been tried.

## Install and start

```bash
lado kits add https://github.com/ladohq/kit-tracker-yougile
lado start <repo> --kit <process-kit> --kit tracker-yougile
```

The agents need `uv` on their PATH (it runs the script and finds or installs the Python
3.9 or newer it names; a session without `uv` does not start) and a network path to
Yougile.

## Credentials

The script works with an API key from a variable of the user's login shell, which LADO's
agents inherit; it never sees your password. Make the key once, with your Yougile login
and password (an account has at most 30 keys; a key does not expire):

```bash
# the companies your account is in, with their ids
curl -s https://yougile.com/api-v2/auth/companies -H 'Content-Type: application/json' \
  -d '{"login": "you@example.com", "password": "<password>"}'
# a key for one of them
curl -s https://yougile.com/api-v2/auth/keys -H 'Content-Type: application/json' \
  -d '{"login": "you@example.com", "password": "<password>", "companyId": "<id>"}'
```

Keep the key in the OS keychain, not in the profile. On macOS:

```bash
security add-generic-password -s yougile -a "$USER" -w '<the key>'   # once
# ~/.zprofile
export YOUGILE_API_KEY="$(security find-generic-password -s yougile -a "$USER" -w)"
```

LADO reads the profile through the login shell with a time limit, so a keychain prompt
stalls every agent's start: run the line once in a new terminal and allow `security` to
read the item ("Always Allow") before the first session.

`YOUGILE_URL` is optional: it defaults to `https://yougile.com`. For a self-hosted
Yougile, set it to that server's address (it serves the same API v2; not tried, see above),
e.g. `export YOUGILE_URL=https://yougile.example.com`. The script refuses an
address that is not `https://` (or `http://` to localhost, for tests), since the key goes
with every request. If the certificate is from a corporate CA, point `SSL_CERT_FILE` at a
file with that CA; verification is never turned off.

Check the key once before a session, from the project's repository:
`uv run --quiet --script <kit>/skills/tracker/yougile.py whoami`, where `<kit>` is the
kit's folder (`lado kits show tracker-yougile` prints it). A refused key is never
retried: make a new one.

## Project settings: `.lado/tracker.yaml`

Each project commits its settings to its own repository, so every worktree has them. Only
`board` is required:

```yaml
board: Development            # the board's title, or its id when the title is not unique
statuses:                     # words process kits use -> a column of the board
  in progress: In progress
  review: Review
  done: Done
labels:                       # a label word -> 'Sticker: State' of a sticker on the board
  waiting for release: 'Release: Waiting'
```

Statuses are the board's columns; write column, sticker and state names as Yougile shows
them. The skill's `transition` action without a target lists the columns. The format, a
strict subset of YAML, is in [`skills/tracker/SKILL.md`](skills/tracker/SKILL.md).

## What agents write

Agents write descriptions and comments in Markdown; the script converts it to HTML
(headings, emphasis, code, lists, links). Every comment and every created task's
description starts with `[LADO: <agent>]`, the name of the agent that wrote it. Run by
hand (no `LADO_AGENT` in the environment), the script adds no mark. By default agents only
read; they create, transition, comment, assign, label or link when their role, their step
or the human asks (`skills/tracker/SKILL.md`). A process kit says which roles touch the
tracker and when, and may allow more.

Yougile allows 50 API requests a minute per company; when it limits one, the script waits
once (at most a minute) and sends it again.

## Development

```bash
uv run --no-project python -m unittest discover -s tests   # the script against a fake Yougile
lado kits check .
```

`BLUEPRINT.md` says why each part of the kit exists.
