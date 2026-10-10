---
name: tracker
description: >-
  The project's task tracker on Yougile: search the board's tasks, get one with its
  comments, create one, transition it to another column, comment, assign it, label it
  (add or remove a label), link a URL to it, and whoami (which account you work as). Use
  whenever your work touches a task in the tracker, e.g. "file a bug", "take the task",
  "assign it to me", "move it to review", "mark it waiting for release", "close it",
  "tell the task what changed".
---

# Tracker: Yougile

You reach Yougile only through the script in this skill's folder, from inside the
project's repository (it reads the project's settings there):

```bash
uv run --quiet --script ${SKILL_DIR}/yougile.py <command> ...      # --help on any command
```

If your CLI does not expand `${SKILL_DIR}`, use the folder this SKILL.md is in. The
script works with the user's `YOUGILE_API_KEY` (and `YOUGILE_URL` for a self-hosted
Yougile); never ask for them, print them or put them in a file. Whatever you write in
Yougile appears in the user's name, so the script starts every comment and every new
task's description with `[LADO: <your agent name>]`; leave that mark to it. In `get` it
is the first line of your comments and the first paragraph (`<p>[LADO: …]</p>`) of a
description.

Reading is always fine. Create, transition, comment, assign, label or link only when your
role, your step or the human asks for it, and only on the tasks named; your process kit's
roles and steps may allow more.

## Actions

A task is named by the key Yougile shows on it (`DEV-484`), by its company-wide number
(`ID-484`) or by its id; the script prints the key everywhere. A task of another board
is not found (exit 7).

| To | Run |
|---|---|
| find tasks | `search [--status S] [--assignee me \| email \| none] [--text '<words>'] [--start N] [--max N]` |
| read a task (each comment with its id) | `get DEV-1 [--comments N]` |
| create a task | `create --title '<text>' [--description -] [--status S]` |
| see where a task can go | `transition DEV-1` |
| change its status | `transition DEV-1 '<status>' [--comment -]` |
| comment | `comment DEV-1 -` (the text on stdin) |
| assign a task | `assign DEV-1 <me \| email \| none> [--reassign]` (`none` unassigns) |
| add or remove labels | `label DEV-1 [--add L ...] [--remove L ...]` |
| link a branch, commit or pull request | `link DEV-1 <url> [--title '<text>']` |
| see which account you work as | `whoami` |

- **Status** is a column of the project's board: a status `S` is a column's title or a
  word of `statuses` in the settings ("review"). `transition` without a target lists the
  columns (a title several columns share with its id), the task's own marked `(current)`;
  run it first when you are unsure. `--comment` needs a target. Moving a
  task does not tick Yougile's "completed" flag; `get` shows it when someone did.
- **search** looks at the board's tasks, archived ones left out; `--text` matches words
  of the title. A full page ends with the `--start` of the next one.
- **create** puts the task in the board's first column unless `--status` names another,
  and prints the new task's key.
- **comment**, **transition --comment**, **link** post a message to the task's chat and
  print its id; `get` shows the same id on each comment, so look for it there to see that
  yours is in. Yougile has no link object: `link` is a comment with the URL. The URL is the
  branch's or commit's page on the repository's host; a repository with no remote has no
  such page, so give the branch and the commit hash in a `comment`.
- **get**, **search** show assignees, and **whoami** your account, as
  `Real Name (email)`; a task with no assignee as `unassigned`. To tell whether a task is
  yours, compare its assignee with what `whoami` prints.
- **assign** leaves the task with exactly that assignee. Use only an email you were
  given: an unknown one is refused (exit 11); report it and do not try another, since a
  guess may assign the task to someone else. A task another account holds is refused
  (exit 11, the holder named) whatever the target: report it, and add `--reassign` only
  when the human or your step says to take it from them.
- **label**: a label is a word of `labels` in the settings, which maps it to a state of a
  sticker on the board; `--add` sets that state, `--remove` takes the sticker off when it
  is in that state. Other stickers stay as they are. A word the settings do not map is refused (exit 3).
- **assign**, **label**, **transition**: when the task is already so, they change nothing
  and say so; that is success.
- Text of more than one line goes on stdin with `-`:

  ```bash
  uv run --quiet --script ${SKILL_DIR}/yougile.py comment DEV-1 - <<'EOF'
  **Done:** the login form checks the password length.
  EOF
  ```

## Writing in Yougile: Markdown

Write descriptions and comments in Markdown; the script converts it to the HTML Yougile
keeps and shows: headings, bold, italic, inline code, fenced code blocks, bullet and
numbered lists (nested by indentation) and links `[text](url)`; in a task's description
Yougile drops inline code, so it shows as plain text there. Anything else, HTML too,
shows as plain text. Write each paragraph on one line: Yougile shows every line break.
`get` shows text as Yougile keeps it: descriptions in HTML, comments as you wrote them.

## Project settings: `.lado/tracker.yaml`

The project's repository keeps its Yougile settings in `.lado/tracker.yaml`; the script
finds it from the current directory up to the repository root. Only `board` is required;
an action that needs a missing setting names it (exit 3). The file is a strict subset of
YAML: `key: value` lines, one level of nesting, `#` comments.

```yaml
board: Development            # the board's title, or its id when the title is not unique
statuses:                     # words process kits use -> a column (title, or id if repeated)
  in progress: In progress
  review: Review
  done: Done
labels:                       # a label word -> 'Sticker: State' of a sticker on the board
  waiting for release: 'Release: Waiting'
```

Read it when you need the project's words; the user changes it, not you.

## When the script fails

It prints one line saying what happened and stops. A Python traceback (`Traceback …`) is
the script crashing: exit 1, and a write may have been applied (the end of this section).
Any other message that does not start with `yougile.py` or `usage: yougile.py` comes from
`uv` or Python before the script ran, so nothing reached Yougile: if it says it cannot
open `yougile.py`, fix the path (see above); otherwise (uv could not get Python or write
its cache; its exit 2 is not wrong arguments) report all of it (nothing was sent). To **report** a
failure: as a worker, send the supervisor that line and the command with `send_message`;
as the lead, tell the human. Then wait for the answer if your step cannot go on without
the tracker; otherwise go on with it. Act on the exit code:

| Exit | What happened | What you do |
|---|---|---|
| 1 | the script crashed | report its last line |
| 2 | wrong arguments, or empty text | fix the command (`--help`) |
| 3 | `.lado/tracker.yaml` missing, invalid, or lacks a setting; the board, a column a word of `statuses` names, or a label's sticker or state, is not found | report it; the user fixes the file |
| 4 | `YOUGILE_API_KEY` is unset, or `YOUGILE_URL` is wrong (not `https://`, a redirect, not Yougile's answer) | report it; the user fixes their shell profile and restarts the session |
| 5 | the API key is refused | stop using Yougile and report it; as the line says, every agent stops using Yougile until the human sets a new key in `YOUGILE_API_KEY` and restarts the session, and the lead tells them |
| 6 | no access to the task or board | report what you tried; look for no way around |
| 7 | task not found, or not on the project's board | check the key; report it if the key came from someone else |
| 9 | Yougile not reachable or did not answer | report it (network or VPN?) and send Yougile nothing more until you are told it answers again |
| 10 | TLS failed | report it: a corporate CA goes in a file named by `SSL_CERT_FILE` |
| 11 | Yougile refused the request, a status is not a column, an email is no account, or `assign` refused a task another account holds | read the line, fix the request once; if it still fails, report it (`assign`: report it, never try another email or `--reassign` on your own) |
| 12 | Yougile itself failed (5xx), or it still limits requests after the script waited once | report it |

A failed write may have been applied. After exit 9 on a write, once you are told Yougile
answers again, `get` before running it again; after exit 1 or a 5xx exit 12 on a write,
there is nothing to wait for: `get` before running it again. A failed `create` has no
key to `get`: look for the task with `search --text '<title>'` before running `create`
again, as its line says. Whatever the code, never
guess the task's state from a failed run: say what failed.
