# Backlog

- Report `kit-reports/tracker-yougile-0.1.0-2026-10-10.md` (e5489a4), F12.4 [medium]: README's key setup reads the password with `read -s` without `-r`, so a `\` or an escaped `"` in the password is lost and the JSON breaks; use `read -r 'YG_LOGIN?Login: '; read -rs 'YG_PASS?Password: '`.
- Same report, F3.1 [low]: on a column title repeated on the board the script advises "write its id", but the kit never prints column ids; print `title (id)` for repeated titles in `column_list`, and drop "rename one of them" from the exit 11 branch (the skill has no such action).
- Trial of 0.1.0 on the cloud board "polygon" (artifact `trial` of run `create/tracker-yougile`): a 429 did not occur, so the wait-and-repeat-once path (R11) is checked only against the fake Yougile in the tests.
