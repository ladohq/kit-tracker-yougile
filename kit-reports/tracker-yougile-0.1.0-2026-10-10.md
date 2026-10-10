# Отчёт о ките: tracker-yougile 0.1.0

- Дата: 2026-10-10
- Кит: корень worktree рана `improve/tracker-yougile-0-1-1` (путь задан задачей)
- Коммит: `d41dd09`
- Оценил: критик kit-builder (слои a и b)
- Режим: полная оценка (шаг `assess` рана `improve`). Прошлый отчёт (оценка `59cc5c7`) не
  переиспользован: после него менялся текст кита (`git diff 59cc5c7 d41dd09 -- BLUEPRINT.md`,
  коммит `114cdcb`, R3 и R6). Он служил только фоном.
- Проходы: три независимых суб-агента. Каждый получил рубрику, `lado-kit-format` и папку кита.
  Начинали с разных мест: (1) kit.yaml и README, (2) yougile.py по функциям, затем SKILL.md,
  (3) BLUEPRINT по требованиям, затем SKILL.md. Отброшенных находок одного прохода нет.
  Подтверждены как находки одного прохода две: F12.5 и F3.2.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет |
| b. Рубрика | 8 находок (2 high, 4 medium, 2 low); 9 из 12 критериев без находок |
| Охват | полная оценка всего кита, 5 файлов: kit.yaml, README.md, BLUEPRINT.md, skills/tracker/SKILL.md, skills/tracker/yougile.py |

Счёт относится только к тому, что названо в строке «Охват».

### `lado kits check .`

```
tracker-yougile: OK (0 agents, 1 skills, 0 packs and 0 flows)
expects commands: uv
```

Expects: `expects commands: uv`. Предупреждения `expects.commands needs LADO …` нет.

### Скрипт бюджета (код выхода 0)

```
# Complexity budget: tracker-yougile 0.1.0

| Measure | Where | Value | Green / yellow up to | Zone |
|---|---|---|---|---|
| Worker roles (not supervisor) | kit | 0 | 3 / 5 | green |
| Work steps in a flow | no flows | 0 | 5 / 8 | green |
| Gates in a flow | no flows | 0 | 2 / 3 | green |
| Words in a role prompt | no roles | 0 | 800 / 1500 | green |
| Words in the lead's prompt | no lead role | 0 | 1000 / 1500 | green |
| Own skills | kit | 1 | 5 / 10 | green |
| MCP servers | kit | 0 | 2 / 4 | green |

## Similar paragraphs (one rule, one place; 55% similar or more)

none

Overall: green
```

### Потоки

У кита нет потоков (R2) и нет скелетов в BLUEPRINT.md, поэтому диаграмм нет. Скрипт потоков
на таком ките падает (см. «Найдено по пути»):

```
$ flow_diagram.py . --out kit-reports/tracker-yougile-0.1.0-2026-10-10
error: kit.yaml: states must be a non-empty mapping   (exit 2)
$ flow_diagram.py . --compare BLUEPRINT.md
error: kit.yaml: states must be a non-empty mapping   (exit 2)
```

Тесты (это не текст кита): `uv run --no-project python -B -m unittest discover -s tests`
дал `Ran 63 tests`, `OK` (проход 2).

## Исправить в первую очередь

1. BLUEPRINT R12: убрать тестовую доску «polygon» и почту аккаунта (F12.2).
2. `ID-188` (номер настоящей задачи с тестовой доски) заменить на условный номер в SKILL.md,
   yougile.py (×3) и BLUEPRINT R4 (F12.1).
3. BLUEPRINT R4: убрать `LAD-1` из цитаты человека (F12.3).
4. README: команды получения ключа шлют логин и пароль на yougile.com даже при self-hosted (F12.5).
5. README: `read -r` / `read -rs` (F12.4); повторяющиеся колонки показывать с id (F3.1).

## Находки

### 1. Границы ролей

Не применимо: ролей нет. Права скилла на запись названы: SKILL.md:29 «Reading is always fine.
Create, transition, comment, assign, label or link only when your».

### 2. Передача между шагами

Не применимо: потоков нет.

### 3. Готовность и исходы

- **F3.1** [medium] `skills/tracker/yougile.py:418`
  > `            problem = ("is the title of several columns: rename one of them, or write its id"`
  Скрипт велит агенту (exit 11) или человеку (exit 3) «write its id». Но кит id колонок нигде
  не печатает: `column_list` (yougile.py:506, `return ", ".join(c.get("title") or "?" for c in columns) or "none"`)
  и `transition` без цели выводят только заголовки. Агент «исправляет запрос один раз»
  (строка 11 таблицы выходов), снова получает отказ и сообщает о нём. Действия «rename» у
  скилла нет. SKILL.md:52 не называет id среди целей, хотя BLUEPRINT R3 его обещает.
  Fix: в `column_list` и в `transition` без цели печатать `title (id)` хотя бы для
  повторяющихся заголовков; убрать «rename one of them»; в SKILL.md:52 добавить «or its id
  (shown by `transition`)». Passes: 3/3 (импакт: medium в одном проходе, low в двух; взят medium).

- **F3.2** [low] `skills/tracker/yougile.py:826`
  > `    if not args.target:`
  `transition DEV-1 --comment -` без цели печатает колонки и возвращает 0, не прочитав
  комментарий. Комментарий молча теряется, а агент считает, что прокомментировал.
  Подтверждено по коду: `read_text(args.comment)` стоит только после этой ветки
  (yougile.py:831, `    comment = read_text(args.comment) if args.comment is not None else None`).
  Fix: при `--comment` без цели выходить с кодом 2 («--comment needs a target»).
  Passes: 1/3, confirmed.

### 4. Независимая проверка

Не применимо: потоков нет, необратимых действий нет. Отобрать задачу у другого аккаунта
можно только с `--reassign` по слову человека или шага (SKILL.md:71–72).

### 5. Противоречия

Таблица выходов SKILL.md:126–138 сверена с кодами `Failure`: 3, 5 (`STOP_ALL`), 7, 11, 12
и совет `search --text` после неудачного `create` совпадают. Путь сообщения о сбое
(«as a worker, send the supervisor … as the lead, tell the human») согласуется с LADO.
Расхождение BLUEPRINT:190 «(no project values anywhere)» с самим блюпринтом учтено в F12.2.

### 6. Дублирование

Правило про `--reassign` есть в SKILL.md:68–72 и в строке 11 таблицы. Строка таблицы —
короткая отсылка, и обе копии совпадают. README «What agents write» отсылает к SKILL.md.

### 7. Когда звать человека

SKILL.md:122–124: «as a worker, send the supervisor that line and the command with
`send_message`; as the lead, tell the human. Then wait for the answer if your step cannot go
on without the tracker». Настройки меняет пользователь: «the user changes it, not you».

### 8. Циклы при повторном визите

Не применимо: потоков нет. Повторы в скрипте ограничены: одно ожидание на 429 (не дольше
минуты), 401 не повторяется.

### 9. Краткость и «почему»

- **F9.1** [low] `BLUEPRINT.md:13`
  > ``create/tracker-yougile` (session `tracker-yougile`, LADO messages #2347, the answers``
  Источники ссылаются на номера сообщений одной локальной сессии LADO (#2347, #2363, #2382,
  #2439, #2440; также строки 66, 155, 158). Читатель опубликованного кита открыть их не может.
  Это следы сессии сборки, а не причины решений.
  Fix: оставить само решение (большинство R уже цитирует ответ), номера сообщений и имя
  сессии убрать или перенести в BRIEF.md / отчёты. Passes: 2/3.

### 10. Описания скиллов

Описание называет все девять действий и говорит, когда использовать: «Use whenever your
work touches a task in the tracker». Скилл один, зависимостей нет. `expects.commands: [uv]`
при `lado: ">=0.30"`.

### 11. Нейтральность к провайдеру

`${SKILL_DIR}` с запасным вариантом (SKILL.md:21 «If your CLI does not expand
`${SKILL_DIR}`, use the folder this SKILL.md is in.»). В скрипте нет абсолютных и домашних
путей. Команды README — для человека, помечены «(zsh)».

### 12. Безопасность и границы

- **F12.1** [high] `skills/tracker/SKILL.md:36`
  > ``(`ID-188`) or by its id; the script prints the key everywhere. A task of another board``
  `ID-188` — номер настоящей задачи с тестовой доски. По артефакту `trial` рана
  `create/tracker-yougile`, `get` по `LAD-1`, `lad-1` и `ID-188` вернул одну и ту же задачу.
  Тот же номер стоит в yougile.py:12 (`number (idTaskCommon, e.g. ID-188) or their id; tasks of other boards are not found.`),
  :433, :979 (`--help`, который видят агенты) и BLUEPRINT.md:70. Это нарушает R1
  («Nothing company- or project-specific … is in the skill's text or the script») и
  требование человека: в ките не должно быть следов проекта. `DEV-484` чистый: это пример из
  описания API Yougile.
  Fix: во всех пяти местах заменить на `ID-484` (пример API, в паре с `DEV-484`).
  Passes: 3/3 (импакт: high в одном проходе, low в двух; взят high по правилу рубрики).

- **F12.2** [high] `BLUEPRINT.md:149`
  > ``  "polygon", account `ladohq@yandex.ru`) passed for all nine actions and found that``
  Блюпринт называет тестовую доску и почту реального аккаунта. Строка уже опубликована:
  `git ls-remote --tags origin` даёт `d41dd09… refs/tags/v0.1.0`, а
  `gh repo view ladohq/kit-tracker-yougile` — `"visibility":"PUBLIC"`.
  Вместе с тем ложной становится BLUEPRINT.md:190 «(no project values anywhere)».
  Fix: «The trial of 2026-10-10 (artifact `trial`, a test board and account the human named)
  passed …». Строку 158 «board and account: answer to #2440» поправить так же.
  Passes: 3/3 (импакт: medium в двух проходах, high в одном; взят high).

- **F12.3** [medium] `BLUEPRINT.md:78`
  > `  показывая LAD-1").`
  `LAD-1` — ключ настоящей задачи с тестовой доски, внутри цитаты человека с гейта.
  Fix: пересказать решение без ключа, например «(rejected: look a key up with a direct
  `GET /tasks/{key}` and accept both kinds of key, showing the project key)».
  Passes: 3/3 (импакт: low в двух проходах, medium в одном; взят medium).

- **F12.4** [medium] `README.md:40`
  > `read 'YG_LOGIN?Login: '; read -s 'YG_PASS?Password: '; echo`
  README.md:37 советует набирать `"` как `\"` и `\` как `\\`. Но `read` без `-r` снимает
  обратные слэши. Проход 2 проверил в zsh: ввод `p\"w\\x` даёт `p"w\x`, а с `read -rs` —
  `p\"w\\x`. JSON ломается, и человек с таким паролем не создаст ключ. Тот же пункт есть в
  BACKLOG.md.
  Fix: `read -r 'YG_LOGIN?Login: '; read -rs 'YG_PASS?Password: '; echo`. Passes: 2/3.

- **F12.5** [medium] `README.md:43`
  > `  curl -s https://yougile.com/api-v2/auth/companies -H 'Content-Type: application/json' -d @-`
  Обе команды получения ключа (то же на README.md:46) жёстко шлют логин и пароль в облако
  yougile.com. При этом README.md:72 предлагает self-hosted Yougile через `YOUGILE_URL`.
  Пользователь своего сервера, выполнив README как написано, отправит корпоративные логин и
  пароль на чужой сервер.
  Подтверждено: `grep -nF 'yougile.com/api-v2/auth' README.md` даёт строки 43 и 46.
  `YOUGILE_URL` в разделе «Credentials» появляется только после этих команд.
  Fix: `"${YOUGILE_URL:-https://yougile.com}/api-v2/auth/companies"` (и так же для `/auth/keys`),
  и перед блоком сказать: для self-hosted сначала задайте `YOUGILE_URL`. Passes: 1/3, confirmed.

## Известные дыры

| Известная дыра | Находка или как кит с ней справляется |
|---|---|
| 1. Красная проверка без учёта окружения | SKILL.md:118 «Any other message that does not start with `yougile.py` or `usage: yougile.py` comes from» — сбой `uv`/Python отделён от сбоя скрипта. |
| 2. Работа вне потока, merge без гейта | Merge и коммитов нет. Запись в трекер — только по просьбе роли, шага или человека (SKILL.md:29–31). |
| 3. Путь вне worktree | Настройки ищутся от текущей папки до первого `.git`, то есть до корня worktree. `~/.zprofile` в README адресован человеку. |
| 4. Вердикт без порога | Не применимо: ревьюера нет. |
| 5. Зависимый скилл, пишущий где нельзя | Не применимо: `dependencies.skills` нет. |
| 6. Команды вне `expects.commands` | `uv` объявлен; `curl`, `read`, `security` нужны только человеку для разовой настройки. `dependencies.lado: ">=0.30"`. |

## Не прослежено

Каждый элемент кита (скилл `tracker`, скрипт, README) назван в R1–R12. Жёлтых и красных
мер нет, потоков и скелетов нет. Блюпринт расходится сам с собой: R1 и строка 190 обещают
отсутствие значений проекта, а R4 и R12 их содержат (F12.1–F12.3).

## Вопросы человеку

1. Почта аккаунта (F12.2) уже лежит в публичном репозитории: в `origin/main` и в
   запушенном теге `v0.1.0`. Правка в 0.1.1 уберёт её из новых версий, но не из истории.
   Рекомендую: если почта не должна быть публичной, в маркетплейс отдавать сразу 0.1.1.
   Переписывать историю и удалять тег — решение только человека.
2. F12.5 (self-hosted в README) и F3.2 (`--comment` без цели) не входят в план задачи.
   Рекомендую: F12.5 включить в 0.1.1 (это одна строка, и она касается паролей), а F3.2
   записать в BACKLOG.
3. Вне текста кита: BRIEF.md:17 содержит путь `~/Projects/kit-tracker-jira-server`, BRIEF.md:96
   и BACKLOG.md:5 — «polygon». Рекомендую: BACKLOG.md поправить по плану; в BRIEF.md
   заменить локальный путь ссылкой на github.com/ladohq/kit-tracker-jira-server.

## Найдено по пути

- `[kit-builder]` `kit-budget/scripts/flow_diagram.py` на ките без `flows/` падает с
  `error: kit.yaml: states must be a non-empty mapping` (exit 2). Ожидалось «0 потоков,
  различий нет» с кодом 0.
