# Отчёт о ките: tracker-yougile 0.1.0

- Дата: 2026-10-10
- Кит: корень worktree рана `create/tracker-yougile` (путь, данный задачей)
- Коммит: `021c2e6`
- Оценил: критик kit-builder (слои a и b)
- Режим: полная оценка (первый отчёт об этом ките, предыдущего нет)
- Проходы: три независимых суб-агента, у каждого рубрика, `lado-kit-format` и папка кита;
  старт с SKILL.md, с `yougile.py` и с README/kit.yaml соответственно. Зависимых и
  ожидаемых скиллов у кита нет. 6 находок одного прохода отброшено, 6 оставлено как
  подтверждённые.

Находки — кандидаты для человека, не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 (потоков нет, R2); скелетов в BLUEPRINT.md нет — сравнивать нечего |
| b. Рубрика | 11 находок (0 high, 4 medium, 7 low); 6 из 12 критериев без находок |
| Охват | полная оценка всего кита: kit.yaml, README.md, BLUEPRINT.md, skills/tracker/SKILL.md, skills/tracker/yougile.py (5 файлов; tests/ прочитаны для проверки, но не текст кита) |

Счёт относится только к тому, что названо в строке «Охват».

### `lado kits check .`

```
tracker-yougile: OK (0 agents, 1 skills, 0 packs and 0 flows)
expects commands: uv
```

Expects: `expects commands: uv`. Предупреждения `expects.commands needs LADO …` нет
(`dependencies.lado: ">=0.30"`).

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

У кита нет потоков (R2), в BLUEPRINT.md нет скелетов («Flow skeletons: none»), диаграмм нет.
Скрипт потоков на ките без `flows/` падает (см. «Найдено по пути»):

```
$ flow_diagram.py . --out kit-reports/tracker-yougile-0.1.0-2026-10-10
error: kit.yaml: states must be a non-empty mapping   (exit 2)
$ flow_diagram.py . --compare BLUEPRINT.md
error: kit.yaml: states must be a non-empty mapping   (exit 2)
```

## Исправить в первую очередь

1. `label` проверяет все слова `labels`, а не только названные: одна устаревшая привязка
   ломает любой `label` (F5.1).
2. Слово `statuses`, указывающее на несуществующую колонку, даёт exit 11 («исправь запрос»)
   вместо exit 3 («пользователь чинит файл») (F5.2).
3. Сбой `create` (5xx / нет ответа) советует `get`, но ключа нет — агент может создать
   дубликат задачи (F12.1).
4. Exit 5: «until the human fixes the key» — без перезапуска сессии новый ключ агентам не
   дойдёт (F7.1).
5. README:14 и kit.yaml:4 — статус пробы и «self-hosted» перед релизом (F9.1, связано с
   вопросом 1).

## Находки

### 1. Границы ролей

Не применимо: ролей нет. Права записи скилла заданы одним местом, SKILL.md:29–30:
«Create, transition, comment, assign, label or link only when your role, your step or the human asks for it».

### 2. Передача между шагами

Не применимо: потоков нет.

### 3. Готовность и исходы

Потоков нет; критерий приложим к таблице кодов выхода SKILL.md (каждый код — что делать).

- **F3.1** [low] `skills/tracker/yougile.py:801`
  > `        raise Failure(REFUSED, "%s is not on board '%s': moving it there is not this "`
  Этот случай exit 11 (задача по id с другой доски) не назван в строке 11 таблицы SKILL.md:135,
  а та велит «fix the request once» — исправить тут нечего, агент потратит попытку.
  Fix: добавить в строку 11 «a task (by id) of another board: report it». Passes: 1/3, confirmed
  (цитата есть; строка 11 SKILL.md перечисляет «a status is not a column, an email is no account, or `assign` refused…» без этого случая).

### 4. Независимая проверка

Не применимо: потоков нет. Проверки кита — 57 тестов против фейкового Yougile и проба на
облачной доске (R12), которая ещё не проведена (вопрос 1).

### 5. Противоречия

- **F5.1** [medium] `skills/tracker/yougile.py:890`
  > `    resolved = {w: _resolve_label(stickers, config, w) for w in config["labels"]}`
  `label` разрешает каждое слово `labels`, а не только `--add`/`--remove`; один переименованный
  стикер или состояние — и любой `label` падает с exit 3 по слову, которого агент не называл.
  Это расходится с SKILL.md:74 («A word the settings do not map is refused (exit 3).») и с `get`,
  который тот же случай переживает (yougile.py:748–753, «Labels: not shown»).
  Fix: разрешать только `add + remove`; остальные слова для вывода — как в `get`, пропуская
  неразрешимые. Passes: 3/3 (импакт: в одном проходе low, в двух medium — взят medium).

- **F5.2** [medium] `skills/tracker/yougile.py:422`
  > `            raise Failure(REFUSED, "status '%s' %s; its columns: %s"`
  Слово `statuses`, привязанное к колонке, которой нет на доске, даёт exit 11 с одним только
  словом в сообщении, хотя ошибка в файле настроек. SKILL.md:97 обещает exit 3 («an action that
  needs a missing setting names it (exit 3)»), а строка 11 таблицы велит «fix the request once» —
  агент подберёт колонку из списка наугад, задача может уехать не туда.
  Fix: если `target` — ключ `statuses` и его колонка не найдена, `CONFIG` (exit 3) с
  `statuses.<word>: <title>` и списком колонок. Passes: 2/3 (один проход отнёс к критерию 3,
  оставлен 5 — ближе к исправлению).

- **F5.3** [low] `skills/tracker/SKILL.md:73`
  > `  sticker on the board; `--add` sets that state, `--remove` takes the sticker off. Other`
  Скрипт снимает стикер только если он в привязанном состоянии (yougile.py:898–902; тест
  `test_label_remove_leaves_another_state` ждёт «nothing changed»); буквально текст обещает снять
  всегда. Fix: «`--remove` takes the sticker off when it is in that state». Passes: 1/3, confirmed.

### 6. Дублирование

- **F6.1** [low] `README.md:74` (то же в `skills/tracker/SKILL.md:101`)
  > `board: Development            # the board's title, or its id when the title is not unique`
  Пример `.lado/tracker.yaml` скопирован дословно в оба файла, хотя README.md:84–85 уже ссылается
  на SKILL.md за форматом; копии разойдутся. Fix: оставить пример в одном месте, из другого —
  ссылка. Passes: 3/3.

### 7. Когда звать человека

Путь к человеку задан: SKILL.md:120 «as a worker, send the supervisor that line and the command with `send_message`; as the lead, tell the human».

- **F7.1** [medium] `skills/tracker/SKILL.md:130`
  > `| 5 | the API key is refused | stop using Yougile and report it; as the line says, every agent stops using Yougile until the human fixes the key, and the lead tells them |`
  Скрипт читает ключ только из окружения, унаследованного агентом при старте
  (yougile.py:246 `key = os.environ.get("YOUGILE_API_KEY", "").strip()`), так что новый ключ в
  профиле работающим агентам не дойдёт: после «fixes the key» они снова получат exit 5 и снова
  позовут человека. Строка 4 той же таблицы перезапуск называет («restarts the session»), строка 5
  и `STOP_ALL` (yougile.py:55) — нет; README.md:65–66 тоже.
  Fix: в строке 5, `STOP_ALL` и README — «until the human puts a new key in the profile and
  restarts the session». Passes: 1/3, confirmed (цитаты yougile.py:246 и SKILL.md:129).

### 8. Циклы при повторном визите

Не применимо: потоков нет.

### 9. Краткость и «почему»

- **F9.1** [low] `README.md:14`
  > `Where it was tried: so far only against a fake Yougile in its tests. The trial on a live`
  Это план, а не факт: после пробы перед релизом строка станет неверной и уйдёт в тег 0.1.0, если
  её не переписать. Рядом kit.yaml:4 («The tracker skill for Yougile (cloud or self-hosted, REST API v2)…»)
  обещает в маркетплейсе self-hosted без оговорки «не проверялось», которую README делает.
  Fix: после пробы переписать README.md:14–16 (дата, итог); в kit.yaml — «self-hosted: untried»
  или убрать. Passes: 2/3 (часть про kit.yaml — один проход, цитата проверена).

- **F9.2** [low] `skills/tracker/SKILL.md:118`
  > ``open `yougile.py`, fix the path (see above); otherwise (uv could not get Python or write``
  Предложение заканчивается «report all of it as exit 1», сразу после «nothing reached Yougile»;
  exit 1 по SKILL.md:139 ведёт к «`get` before running it again» — лишняя проверка и смешение
  сбоя окружения со сбоем скрипта. Fix: «report all of it (nothing was sent)». Passes: 2/3.

- **F9.3** [low] `skills/tracker/SKILL.md:98`
  > `YAML: `key: value` lines, one level of nesting, `[a, b]` lists, `#` comments.`
  Ни одна настройка не принимает список: `board` — строка (yougile.py:174), элементы карт — строки
  (yougile.py:182); пользователь, поверивший фразе, получит ошибку. Fix: убрать «`[a, b]` lists».
  Passes: 1/3, confirmed.

### 10. Описания скиллов

Описание называет все девять действий и когда звать: «Use whenever your work touches a task in
the tracker»; соседних скиллов нет; `expects.commands: [uv]` при `lado: ">=0.30"`, check без
предупреждений.

### 11. Нейтральность к провайдеру

Только `${SKILL_DIR}` с запасным путём (SKILL.md:21 «If your CLI does not expand `${SKILL_DIR}`, use the folder this SKILL.md is in.»);
имён инструментов CLI нет; абсолютных и домашних путей в скрипте нет.

### 12. Безопасность и границы

Сильные стороны: ключ только по https или на loopback (yougile.py:260), редиректы не
следуются, TLS не отключается, 401 не повторяется, `--reassign` только по слову человека или
шага, незнакомый email не угадывается.

- **F12.1** [medium] `skills/tracker/yougile.py:54`
  > `APPLIED_ANSWERED = "; the change may have been applied: check with get before running it again"`
  Для неудачного `create` (5xx или нет ответа на POST, yougile.py:787) это сообщение и
  SKILL.md:138–140 советуют `get`, но ключа у агента нет; скорее всего он запустит `create` снова,
  и в Yougile от имени пользователя появится дубликат, а удалять скилл не умеет.
  Fix: для `create` — сообщение и строка SKILL.md «look for it with `search --text '<title>'`
  before running create again». Passes: 1/3, confirmed (yougile.py:374 применяет его ко всем не-GET,
  `create` печатает ключ только после успешного POST, yougile.py:787–794).

- **F12.2** [low] `skills/tracker/yougile.py:931`
  > `    text = "[%s](%s)" % (args.title, args.url) if args.title else args.url`
  Без `--title` голый URL идёт через Markdown: он не становится `<a>`, а разметка внутри
  срабатывает — `to_html('https://github.com/o/r/tree/fix/_draft_/x')` дал
  `<p>https://github.com/o/r/tree/fix/<em>draft</em>/x</p>`. Ссылка на ветку в `textHtml`
  искажается. Fix: в `cmd_link` строить `<a href>` напрямую, тест на URL с `_x_`.
  Passes: 1/3, confirmed (вывод выше).

## Известные дыры

| Известная дыра | Находка или как кит с ней справляется |
|---|---|
| 1. Красная проверка без учёта окружения | Потоков нет. Скилл отделяет сбой `uv`/Python от сбоя скрипта: SKILL.md:116–118 «comes from `uv` or Python before the script ran, so nothing reached Yougile»; формулировку размывает F9.2. |
| 2. Работа вне потока, merge без гейта | Потоков нет; записи — только по просьбе роли, шага или человека (SKILL.md:29–30). |
| 3. Путь вне worktree | Нет: настройки ищутся от текущей папки до первого `.git` (yougile.py:200), что в worktree — его собственный `.git`; файлы кита — через `${SKILL_DIR}`. |
| 4. Вердикт без порога | Не применимо: ревьюеров нет. |
| 5. Зависимый скилл, пишущий где нельзя | Не применимо: `dependencies.skills` нет. |
| 6. Команды вне `expects.commands` | В порядке: `uv` в kit.yaml и в README.md:25 как обязательный; `curl` и `security` — только разовая настройка ключа человеком; `dependencies.lado: ">=0.30"`. |

## Не прослежено

Ничего: каждый элемент (kit.yaml, `uv`, скилл `tracker`, `yougile.py`, тесты, README) назван в
таблице трассировки BLUEPRINT.md с требованиями; жёлтых и красных мер нет; скелетов потоков в
блюпринте нет (у кита нет потоков, R2), различий нет. Требования R1–R11 реализованы, как
заявлено (проверено всеми тремя проходами по скрипту). R12: тесты есть (57, OK); проба на
облачной доске не проведена (см. вопрос 1).

## Вопросы человеку

1. **Проба R12 на облачной доске до релиза.** Блюпринт требует её до релиза, а шага для неё в
   потоке нет; сейчас её делает автор параллельно, без коммитов (по словам супервизора). От неё
   зависят факты, на которые скрипт уже опирается (id чата = id задачи, `yougile.py:647`; порядок
   колонок; вид ответов 401/429) и строка README.md:14. Рекомендую: на гейте релиза не тегировать
   0.1.0, пока проба не пройдена и README.md:14–16 не переписан с её итогом (F9.1).
2. Medium-находки F5.1, F5.2, F7.1, F12.1 не блокируют релиз. Рекомендую исправить их до тега
   одним заходом автора вместе с итогом пробы — они мелкие и локальные.

## Найдено по пути

- `[kit-builder]` `kit-budget/scripts/flow_diagram.py` на ките без `flows/` (и с `--out`, и с
  `--compare`) падает с `error: kit.yaml: states must be a non-empty mapping` (exit 2): похоже,
  при отсутствии потоков он читает как поток `kit.yaml`. Для кита-скилла ожидалось «0 потоков,
  различий нет» с кодом 0.
