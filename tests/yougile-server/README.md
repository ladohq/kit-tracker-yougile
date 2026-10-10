# A local Yougile for trying the kit

Yougile's self-hosted server in Docker, at `http://localhost:8001`: the real Yougile the
kit is tried on before a release, without a cloud account. It is not part of the skill
and is never installed into agents' folders.

Yougile ships the server for Linux x64 only, so the container runs as `linux/amd64`; on
an arm64 Mac Docker emulates it (slower, but enough for a trial). Yougile's install guide:
<https://ru.yougile.com/media/docs/yougile-linux-ru.pdf>.

## Start

The distribution is not in the repository; download it next to this file (it is in
`.gitignore`):

```bash
cd tests/yougile-server
curl -fLo yougile.tar.gz https://dist.yougile.com/linux/latest/yougile.tar.gz
docker compose up --build -d          # first start; later: docker compose up -d
docker compose logs -f yougile        # until the server says it listens
```

Open <http://localhost:8001>. Companies, accounts and tasks are kept in the volume
`database` (Yougile's `database/` folder), so they survive `docker compose down`;
`docker compose down -v` deletes them. If the page does not open while the log shows the
server running, it listens on 127.0.0.1 only: set its address to `0.0.0.0` in `conf.json`
(`docker compose exec yougile sh`, then restart). If the server asks for a license key
that Yougile does not give for tests, stop: the trial moves to the cloud (BLUEPRINT.md,
R12).

## A company, an account and a key

1. In the browser, register the first account and create a company (the server is
   offline, so no email is sent; the first account is the company's admin).
2. Get the company's id and make a key, with the account's email and password:

   ```bash
   export YOUGILE_URL=http://localhost:8001
   curl -s "$YOUGILE_URL/api-v2/auth/companies" -H 'Content-Type: application/json' \
     -d '{"login": "admin@example.com", "password": "<password>"}'
   curl -s "$YOUGILE_URL/api-v2/auth/keys" -H 'Content-Type: application/json' \
     -d '{"login": "admin@example.com", "password": "<password>", "companyId": "<id>"}'
   export YOUGILE_API_KEY=<the key from the answer>
   ```

## A board for the trial

```bash
api() { curl -s "$YOUGILE_URL/api-v2/$1" -H 'Content-Type: application/json' \
          -H "Authorization: Bearer $YOUGILE_API_KEY" "${@:2}"; }
api projects -d '{"title": "LADO trial"}'                         # -> project id
api boards -d '{"title": "Trial", "projectId": "<project id>"}'   # -> board id
for c in "To do" "In progress" "Review" "Done"; do
  api columns -d "{\"title\": \"$c\", \"boardId\": \"<board id>\"}"
done
api string-stickers -d '{"name": "Release", "states": [{"name": "Waiting"}]}'  # -> sticker id
api "boards/<board id>" -X PUT -d '{"stickers": {"custom": {"<sticker id>": true}}}'
```

Then, in a scratch git repository, `.lado/tracker.yaml`:

```yaml
board: Trial
statuses:
  in progress: In progress
  review: Review
  done: Done
labels:
  waiting for release: 'Release: Waiting'
```

## The trial

From that repository, with `LADO_AGENT=trial` set, run each action of the skill
(`uv run --quiet --script <kit>/skills/tracker/yougile.py ...`): `whoami`, `create` (with
a Markdown description), `search` with each filter, `get` by key and by id, `transition`
without and with a target and `--comment`, `comment`, `assign` (`me`, an email, `none`),
`label --add`/`--remove`, `link`. Check in the browser what each one changed, and these
facts the API leaves open:

- whether the board's columns come in the board's order (`create` uses the first);
- that a task's chat id is the task's id (`comment`, `get`);
- whether `GET /api-v2/tasks/{key}` takes a key (the script looks keys up on the board);
- the answers to a wrong key (401) and to more than 50 requests a minute (429,
  `Retry-After`).

Write what was found in the run's notes; a fact that differs from the script is a fix of
the script and its tests.
