# Отчёт о ките: tracker-yougile 0.1.1

- Дата: 2026-10-11
- Кит: корень worktree рана `improve/tracker-yougile-0-1-1` (путь задан задачей)
- Коммит: `813090f` (в `kit.yaml` пока `version: 0.1.0`; версию ставят на шаге release)
- Оценил: критик kit-builder (слои a и b)
- Режим: повторная оценка относительно `kit-reports/tracker-yougile-0.1.0-2026-10-10.md`
  (полная оценка `d41dd09`, отчёт в `1070353`; эту базу называет план),
  `git diff 1070353 -- kit.yaml README.md BLUEPRINT.md agents flows skills`
- Визит 2 (813090f): изменение после визита 1 (`git diff 2cf56a0 813090f`) — 3 коммита,
  исправляющие F3.3, F3.4 и F9.2: SKILL.md (пункт Status), yougile.py (`column_name` в
  `get`/`search`/`create`/`transition`, `--help`), BLUEPRINT R4 и R12. Изменение маленькое
  (≈30 строк), поэтому три прохода по нему критик сделал сам, без суб-агентов: (1) от SKILL.md
  к коду, (2) от кода (область видимости `config` и `columns`, кэш `api.columns`) к выводу,
  (3) от BLUEPRINT к журналу. Находок одного прохода нет. Полный проход перед вердиктом не
  повторялся: он был сделан на визите 1 (dcc19e4) по тем же четырём файлам, а с тех пор они
  менялись только в проверенных местах.
- Визит 1 (dcc19e4): три независимых суб-агента получили рубрику, папку кита, diff и прошлый отчёт.
  Каждый начинал со своего места: (1) README, (2) изменённые функции yougile.py с проверкой
  поведения, (3) BLUEPRINT по требованиям и проверка вырезанных правил по `--word-diff`.
  Отброшенных находок одного прохода нет; подтверждена одна (F9.2). Затем, перед вердиктом,
  был сделан полный проход по всем четырём файлам из diff: он дал одну находку в
  «Пропущено ранее».

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет |
| b. Рубрика | 0 открытых находок (визит 1: 2 находки и 1 в «Пропущено ранее», все RESOLVED); 12 из 12 критериев без открытых находок |
| Охват | повторная оценка изменённого текста и полный проход по 4 файлам из diff (README.md, BLUEPRINT.md, skills/tracker/SKILL.md, skills/tracker/yougile.py) |
| Правило остановки | выполнено: 0 high, 0 medium в изменённом тексте |

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

Потоков (R2) и скелетов в BLUEPRINT.md («Flow skeletons: none») нет, сравнивать нечего.
Скрипт на таком ките падает. Это сбой скрипта, а не кита (см. «Найдено по пути»):

```
$ flow_diagram.py . --compare BLUEPRINT.md
error: kit.yaml: states must be a non-empty mapping   (exit 2)
```

Тесты (это не текст кита): `uv run --no-project python -B -m unittest discover -s tests`
дал `Ran 66 tests`, `OK`. Поиск следов проекта
`grep -rnE 'ID-188|polygon|ladohq@|yandex|LAD-[0-9]|#2[0-9]{3}|~/Projects|/Users/|artifact `trial`'` вне
`.git` и `kit-reports/` ничего не находит.

## Вердикт

**approved**. `lado kits check` прошёл без ошибок, красных и жёлтых мер нет, различий со
скелетами нет (скелетов нет), открытых находок нет. Правило остановки выполнено.

## Исправить в первую очередь

Нечего: открытых находок нет. Визит 1 называл F3.3 и F9.2 — обе RESOLVED.

## Находки

### 1. Границы ролей

Не применимо: ролей нет. Права скилла на запись (SKILL.md:29–31) не менялись.

### 2. Передача между шагами

Не применимо: потоков нет.

### 3. Готовность и исходы

- **F3.3** [medium] `skills/tracker/SKILL.md:52`
  > `- **Status** is a column of the project's board: a status `S` is a column's title or a`
  Список колонок теперь показывает id у повторяющегося заголовка (SKILL.md:54). Но ни
  SKILL.md, ни `--help` не говорят, что id можно передать как цель:
  yougile.py:1003 `    p.add_argument("target", nargs="?", help="a column title, or a word of statuses")`.
  BLUEPRINT R3:41 это обещает, и код id принимает. Агент, скопировавший из списка
  `Review (<id>)`, получает exit 11 «is not a column of the board» (проход 2 проверил это
  вызовом `Yougile.column`). Если затем он передаст `Review`, получит «write the id of one»,
  но его единственная попытка исправить запрос уже потрачена. Агенты будут действовать
  по-разному и терять шаг. Это остаток F3.1: прошлый отчёт предлагал именно эту правку, а
  план её не включил.
  Fix: SKILL.md:52–53 — «a column's title, its id (shown by `transition` when titles
  repeat), or a word of `statuses`». В `--help` для `target` и `create --status` —
  «a column title or id, or a word of statuses». Passes: 3/3 (импакт: medium в двух
  проходах, low в одном; взят medium).
  **RESOLVED (визит 2, 56ab46f):** SKILL.md:52–53 «a status `S` is a column's title, its id
  (written after a title several columns share), or a word of `statuses` in the settings»;
  yougile.py:1005 `help="a column title or id, or a word of statuses"`, `create --status` так же.

### 4. Независимая проверка

Не применимо: потоков нет, необратимых действий изменение не добавляет.

### 5. Противоречия

Новые сообщения согласуются с таблицей выходов. `--comment needs a target` даёт exit 2
(«wrong arguments»). Ошибка `statuses` с неоднозначным заголовком даёт exit 3 «the user
fixes the file». BLUEPRINT R3, R4, R7 и R12 совпадают с README, SKILL.md и кодом. Строка
BLUEPRINT:192 «(no project values anywhere)» снова верна.

### 6. Дублирование

Новых повторов нет. Правило про `--comment` стоит в SKILL.md:55 и в `--help`; это
справка CLI, а не второй источник правила.

### 7. Когда звать человека

Изменение пути к человеку не трогает. Для self-hosted README:37–39 велит сначала задать
`YOUGILE_URL`.

### 8. Циклы при повторном визите

Не применимо: потоков нет.

### 9. Краткость и «почему»

- **F9.2** [low] `BLUEPRINT.md:150`
  > `  and 429 answers) are checked there. The trial of 2026-10-10 (artifact `trial` of run`
  F9.1 убрал номера сообщений сессии, потому что читатель опубликованного кита не может их
  открыть. Ссылка на артефакт `trial` локального рана — то же самое, и переписанная строка
  её сохранила. Так же устроена R4 в BLUEPRINT.md:74
  (`  artifact `trial`), so a lookup costs one request under the rate limit; a task whose`),
  которую diff не менял. Найденные пробой факты уже перечислены в R12.
  Fix: в обоих местах убрать «artifact `trial` of run …», оставить «the trial on the cloud
  board». Passes: 1/3, confirmed (`grep -nF` даёт строки 150 и 74; полный проход
  подтвердил).
  **RESOLVED (визит 2, d198520, 813090f):** `grep -nF 'artifact `trial`' BLUEPRINT.md BACKLOG.md`
  ничего не находит; R4 «(found in the trial on the cloud board)», R12 «The trial of 2026-10-10
  (a test board and a test account in the cloud)».

### 10. Описания скиллов

Описание не менялось. `expects.commands: [uv]` при `lado: ">=0.30"`.

### 11. Нейтральность к провайдеру

В новом тексте нет имён инструментов какого-либо CLI. `${YOUGILE_URL:-…}` — синтаксис
оболочки в командах README для человека (zsh).

### 12. Безопасность и границы

Изменение снижает риск. Логин и пароль идут на `${YOUGILE_URL:-https://yougile.com}`
(README:45, :48). `--comment` без цели отказывает до любого запроса (yougile.py:829–831).
Следов проекта в тексте кита нет.

## Известные дыры

| Известная дыра | Находка или как кит с ней справляется |
|---|---|
| 1. Красная проверка без учёта окружения | Без изменений: SKILL.md:119 отделяет сбой `uv`/Python от сбоя скрипта. |
| 2. Работа вне потока, merge без гейта | Без изменений: запись только по просьбе роли, шага или человека (SKILL.md:29–31). Merge нет. |
| 3. Путь вне worktree | Новых путей нет. Путь `~/Projects` ушёл вместе с BRIEF.md. |
| 4. Вердикт без порога | Не применимо. |
| 5. Зависимый скилл, пишущий где нельзя | Не применимо. |
| 6. Команды вне `expects.commands` | Без изменений: `uv`. `curl` и `read` нужны только человеку для разовой настройки. |

## Не прослежено

Новых элементов нет: каждое изменение названо в R3, R4, R7 и R12 и в журнале раздела 5.
Жёлтых и красных мер нет, скелетов нет. Расхождений кита с блюпринтом нет: R3:41 («a column
title, a column id, or a word of `statuses`») теперь совпадает с SKILL.md. Строка 0.1.1 в
журнале (BLUEPRINT:227) не называет F3.3, F3.4 и F9.2. Её «Repeated column titles shown with
their ids» по смыслу покрывает F3.4, но не F3.3 и F9.2. Это неполнота журнала, а не
расхождение: агентов она не меняет. Дописать строку может супервизор при релизе.

## Прошлые находки

| Id | Статус | Доказательство |
|---|---|---|
| F3.1 (id колонок не показываются) | RESOLVED | yougile.py:418 `problem = ("is the title of several columns: write the id of one"`; `column_name()` (yougile.py:505) используется в `column_list` и в `transition` без цели (:839); тест `test_transition_lists_repeated_titles_with_ids`. Остаток в SKILL.md — F3.3 |
| F3.2 (`--comment` без цели теряется) | RESOLVED | yougile.py:829–831 `if args.comment is not None and not args.target: raise Failure(USAGE, "--comment needs a target…`; exit 2 до запросов (тест `test_transition_comment_needs_a_target`) |
| F9.1 (номера сообщений сессии) | RESOLVED | `grep -nE '#2[0-9]{3}' BLUEPRINT.md` ничего не находит; BLUEPRINT:13 «the human's answers in the design round of run `create/tracker-yougile` and at its gates». Родственный остаток — F9.2 |
| F12.1 (`ID-188`) | RESOLVED | SKILL.md:36, yougile.py:12, :433, :990 и BLUEPRINT:70 — `ID-484`; `ID-188` не найден |
| F12.2 (доска и почта) | RESOLVED | BLUEPRINT:151 «a test board and a test account in the cloud»; `polygon` и `ladohq@` не найдены. В публичной истории и теге `v0.1.0` строка осталась — по решению плана |
| F12.3 (`LAD-1`) | RESOLVED | BLUEPRINT:78 `показывая" the project key).` |
| F12.4 (`read` без `-r`) | RESOLVED | README:42 `read -r 'YG_LOGIN?Login: '; read -rs 'YG_PASS?Password: '; echo` |
| F12.5 (ключ запрашивается в облаке) | RESOLVED | README:45, :48 `curl -s "${YOUGILE_URL:-https://yougile.com}/api-v2/auth/…"`; README:37–39; R7:102–104 |

Список автора «fixed / not fixed» (`build-report`) сверен с файлами: всё совпадает. Удаление
BRIEF.md выполнено, и BLUEPRINT:12 ссылается на коммит `ca6bcac`, где файл можно прочесть.
Удаление повторных строк 0.1.1 из разделов 3 и 4 блюпринта подтверждено: в diff от базы
эти разделы не менялись, кроме заголовка раздела 4.

## Вырезанные правила

| Удалённое правило (файл:строка в 1070353) | Где оно теперь |
|---|---|
| BLUEPRINT:12–15 источники: BRIEF.md, номера сообщений #2347… | BLUEPRINT:12–14 (brief по коммиту ca6bcac, ответы человека в design round и на гейтах); номера убраны намеренно (F9.1) |
| BLUEPRINT R3: «`--comment` posts a comment after the move» | BLUEPRINT:43–44, дополнено отказом без цели |
| BLUEPRINT R3 источник «answer to #2363, "Только комментарий"» | BLUEPRINT:66, цитата сохранена |
| BLUEPRINT R4: `ID-188`, «показывая LAD-1» | BLUEPRINT:70 `ID-484`; :78 «показывая" the project key» (намеренно, F12.1, F12.3) |
| BLUEPRINT R7: команды README «with curl» | BLUEPRINT:102–104, с `${YOUGILE_URL:-…}` |
| BLUEPRINT R12: доска, аккаунт, #2439/#2382/#2440 | BLUEPRINT:150–151, 157–160; цитата человека сохранена, кто выбрал доску — R12:146 |
| README:40, 43, 46 | README:42, 45, 48 (правила усилены) |
| SKILL.md:36 `ID-188`; :54 «lists the columns,» | SKILL.md:36 `ID-484`; :54 дополнено id |
| yougile.py:418 «rename one of them, or write its id» | yougile.py:418 «write the id of one»; «rename» убран намеренно (F3.1) |
| yougile.py `--comment` help | yougile.py:1004–1005, добавлено «(needs a target)» |

Ни одно правило не потеряно.

## Пропущено ранее

- **F3.4** [low] `skills/tracker/yougile.py:674` (также :757, :824, :852)
  > `            return column.get("title")`
  Id к повторяющемуся заголовку добавляется только в списке `transition` и в сообщениях об
  ошибках. Строка `Status:` в `get`, `[column]` в `search`, «created in …» в `create` и
  «A -> B» в `transition` печатают голый заголовок. Пример — yougile.py:757
  `        print("%s  [%s]  %s  (%s)" % (key_of(task), column.get("title"), task.get("title"),`.
  На доске с двумя колонками `Done` агент по `get` или `search` не поймёт, в какой из них
  задача. Fix: печатать `column_name(column, columns)` в `_column_title` и в этих трёх
  выводах. Passes: full pass, confirmed (`column_name` используется только на :514 и :839).
  **RESOLVED (визит 2, 56ab46f):** `column_name` теперь на yougile.py:675 (`_column_title`,
  строка `Status:` в `get`), :758 (`search`), :826 (`create`), :847 и :854 (`transition`);
  тест добавлен. `api.columns` кэширует колонки (`self._columns`), поэтому вызов в цикле
  `search` не добавляет запросов.

## Вопросы человеку

Вопросов нет. Визит 1 спрашивал, исправлять ли F3.3, F9.2 и F3.4 до тега: все три
исправлены на этом круге.

## Найдено по пути

- `[kit-builder]` `kit-budget/scripts/flow_diagram.py . --compare BLUEPRINT.md` на ките без
  `flows/` и без скелетов падает с `error: kit.yaml: states must be a non-empty mapping`
  (exit 2), а должен сообщать «различий нет» с кодом 0.
