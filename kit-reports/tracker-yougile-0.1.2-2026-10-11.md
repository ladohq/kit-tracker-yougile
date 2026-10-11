# Отчёт о ките: tracker-yougile 0.1.2

- Дата: 2026-10-11
- Кит: корень worktree рана `improve/tracker-yougile-0-1-2` (путь задан задачей)
- Коммит: `8df771d`
- Оценил: критик kit-builder (слои a и b)
- Режим: повторная оценка относительно `kit-reports/tracker-yougile-0.1.1-2026-10-11-assess.md`
  (полная оценка `5cda9b4`, отчёт в `a3c8b37`; эту базу называет план),
  `git diff 5cda9b4 -- kit.yaml README.md BLUEPRINT.md agents flows skills`.
  Изменение: 2 коммита, `ece7e64` (BLUEPRINT) и `8df771d` (kit.yaml, SKILL.md, yougile.py,
  тесты).
- Визит 1. Проходы: критик сделал три прохода по изменению сам, без суб-агентов. (1) От
  плана к файлам: каждый пункт плана проверен в diff. (2) Новый код `to_markdown` и
  `column()` проверен запуском: тесты и разбор образцов HTML, в том числе описания из
  задачи. (3) От SKILL.md к коду и к BLUEPRINT R3, R9, R12. Затем вырезанные правила
  проверены по `--word-diff`, и сделан полный проход по SKILL.md, yougile.py
  (изменённые функции и всё, что их вызывает), BLUEPRINT и kit.yaml. Находок одного
  прохода: 1, она оставлена как подтверждённая (F5.2), отброшенных нет.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет («Flow skeletons: none») |
| b. Рубрика | 1 новая находка (0 high, 0 medium, 1 low); 4 находки оценки assess — все RESOLVED; 11 из 12 критериев без находок |
| Охват | повторная оценка изменённого текста и полный проход по 4 файлам из diff (kit.yaml, BLUEPRINT.md, skills/tracker/SKILL.md, skills/tracker/yougile.py) |
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
# Complexity budget: tracker-yougile 0.1.2

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

Потоков (R2) и скелетов в BLUEPRINT.md нет, сравнивать нечего. Скрипт на таком ките падает.
Это сбой скрипта kit-builder, а не кита (уже записан в отчёте assess):

```
$ flow_diagram.py . --compare BLUEPRINT.md
error: kit.yaml: states must be a non-empty mapping   (exit 2)
```

Тесты (это не текст кита): `uv run --no-project python -B -m unittest discover -s tests`
дал `Ran 74 tests`, `OK`.

Описание из задачи через `to_markdown`:
`<p>[LADO: supervisor]</p><p>В README.md нужен раздел <strong>Usage</strong>…</p>` →
`'[LADO: supervisor]\n\nВ README.md нужен раздел **Usage**…'`. Прочие образцы:
вложенный `ol`/`ul` даёт `'1. one\n   - two\n2. three'`, `pre` даёт блок с `x < y`, таблица
даёт `a | b`, `img` даёт свой URL.

## Вердикт

**approved**. `lado kits check` прошёл без ошибок, мер жёлтого и красного нет, различий со
скелетами нет (скелетов нет), высоких находок нет. Правило остановки выполнено.

Чего этот отчёт не проверял: план требует перед релизом прочитать LAD-4 через `get` на
облачной доске (только чтение). Автор этого не сделал и написал об этом. Тесты идут против
фейка, поэтому настоящий HTML Yougile проверит только этот шаг (см. F5.2).

## Исправить в первую очередь

Блокирующих находок нет. Перед тегом стоит прочитать LAD-4 через `get`, как требует план.

## Находки

### 1. Границы ролей

Ролей нет; новых прав скилл не даёт. Новое правило «ask the human (as a worker, through the
supervisor)» (SKILL.md:57–58) идёт по тому же пути, что и SKILL.md:128.

### 2. Передача между шагами

Не применимо: потоков нет.

### 3. Готовность и исходы

Для слова статуса, которого нет ни в колонках, ни в `statuses`, теперь есть оба исхода:
одна колонка подходит — взять её и сказать, какую; ни одной или несколько — спросить.
SKILL.md:57 «so the user can map it in `statuses`; when none or several fit, ask the human (as a».
Строка 11 таблицы отсылает к этому пункту: SKILL.md:143 «(a status: see **Status**)».

### 4. Независимая проверка

Не применимо: потоков нет.

### 5. Противоречия

- **F5.2** [low] `skills/tracker/yougile.py:740` (разбор: :656, :659)
  > for kid in child[2] if not isinstance(child, str) and child[0] == "li" else [child]:
  `_Tree` не закрывает `<li>` и `<p>` неявно, как это делает HTML. Если `</li>` опущен,
  следующий `<li>` попадает внутрь предыдущего. `to_markdown("<ul><li>a<li>b</ul>")`
  даёт `'- a\n  b'` вместо `'- a\n- b'`, и SKILL.md:98 («Markdown made from Yougile's
  HTML») для такого HTML неверен. Текст не теряется, ломается только разметка списка. HTML,
  который пишет сам скрипт, закрывает каждый тег. Пишет ли Yougile без `</li>`, неизвестно:
  это покажет чтение LAD-4 из плана. Fix: в `handle_starttag` закрывать открытый `li` при
  новом `li`, а открытый `p` — при новом блоке; либо оставить как есть, если LAD-4
  покажет закрытые теги. Passes: 1/3, confirmed (вывод выше получен запуском
  `to_markdown` в `skills/tracker`).

Остальное согласовано. SKILL.md:26 («is the first line of your comments and of your tasks'
descriptions.») совпадает с выводом (`[LADO: supervisor]` первой строкой). BLUEPRINT R9
говорит то же, что код: «no option prints the raw HTML».

### 6. Дублирование

Правило `assign` теперь записано только в пункте **assign** (SKILL.md:72–76), а строка 11
даёт ссылку (SKILL.md:143 «(`assign`: never retry; see **assign**)»). Правило про
статусы записано в пункте **Status**, строка 11 и BLUEPRINT R3 ссылаются на него и
пересказывают его как требование (R3 — источник, а не текст для агента).

### 7. Когда звать человека

Путь к человеку для слова без колонки задан: SKILL.md:57–58 (воркер — через супервизора).
Строка скрипта называет `statuses` и его слова: yougile.py:426
`            advice = ("" if match else "; to use this word, map it to a column in 'statuses' "`.

### 8. Циклы при повторном визите

Не применимо: потоков нет.

### 9. Краткость и «почему»

У нового правила есть причина: «so the user can map it in `statuses`» (SKILL.md:57).
BLUEPRINT R9 называет её для `get`: «So an agent that quotes a description in a comment or
a new task carries no tags.».

### 10. Описания скиллов

Описание скилла не менялось и подходит: `get` в нём — «get one with its comments».

### 11. Нейтральность к провайдеру

Новых путей и имён инструментов нет; `html.parser` — стандартная библиотека.

### 12. Безопасность и границы

Новых записей и сетевых действий нет: `to_markdown` работает только на выводе. Слово
статуса без колонки агент берёт сам, только если подходит ровно одна колонка, и сообщает,
какую взял. Это вариант A, выбранный человеком на triage.

## Известные дыры

| Известная дыра | Находка или как кит с ней справляется |
|---|---|
| 1. Красная проверка без учёта окружения | Без изменений: SKILL.md:124 отделяет сбой `uv`/Python от сбоя скрипта. |
| 2. Работа вне потока, merge без гейта | Не применимо: ролей и потоков нет; запись по-прежнему только по просьбе (SKILL.md:29). |
| 3. Путь вне worktree | Новых путей нет. |
| 4. Вердикт без порога | Не применимо: ревьюера нет. |
| 5. Зависимый скилл, пишущий где нельзя | Не применимо: зависимых скиллов нет. |
| 6. Команды вне `expects.commands` | Без изменений: `uv`; новый код использует только стандартную библиотеку. |

## Не прослежено

Ничего. Изменение названо в R3, R9 и R12, в строке `yougile.py` раздела 3 и в журнале
раздела 5 (строка 0.1.2). В разделе 4 указан бюджет сборки 0.1.2, значения те же. Жёлтых и
красных мер нет. Скелетов нет (BLUEPRINT.md: «Flow skeletons: none»).

## Прошлые находки

| Id | Статус | Доказательство |
|---|---|---|
| F3.1 (метка из нескольких слов без кавычек) | RESOLVED | SKILL.md:47 `label DEV-1 [--add '<label>' ...] [--remove '<label>' ...]`; SKILL.md:77 «(quote one of several words)» |
| F5.1 (`search --status` help без id) | RESOLVED | yougile.py:1157 `p.add_argument("--status", help="a column title or id, or a word of statuses")` |
| F6.1 (правило `assign` дважды) | RESOLVED | SKILL.md:143 «(`assign`: never retry; see **assign**)»; правило целиком в SKILL.md:72–76 |
| F7.1 (слово без колонки → агент угадывает) | RESOLVED | yougile.py:426–430: строка exit 11 советует `statuses` и перечисляет его слова (или `none`); SKILL.md:51–58: брать колонку, только если подходит одна, сказать какую, иначе спросить; тест `test_search_unknown_status` (tests/test_yougile.py:479). Строка SKILL.md:105 «an action that needs a missing setting names it (exit 3)» осталась, но она про отсутствующую настройку, а не про незаписанное слово; пункт **Status** теперь описывает этот случай. |
| Изменение плана: `get` показывает описание как Markdown | RESOLVED | yougile.py:951 `print("\nDescription:\n%s" % (to_markdown(task.get("description") or "") or "(empty)"))`; SKILL.md:26, :98–99; BLUEPRINT R9; тесты `HtmlToMarkdownTest` (tests/test_yougile.py:371) и `test_get_shows_a_created_description_as_markdown` (:578). Чтение LAD-4 перед релизом не сделано (по плану — до тега) |

Список автора «fixed / not fixed» (`build-report`) сверен с файлами: всё совпадает.

## Вырезанные правила

| Удалённое правило (файл:строка в 5cda9b4) | Где оно теперь |
|---|---|
| SKILL.md:26–27 метка — «the first paragraph (`<p>[LADO: …]</p>`) of a description» | SKILL.md:26, «first line … of your tasks' descriptions» (намеренно: вывод теперь Markdown) |
| SKILL.md:94 «`get` shows text as Yougile keeps it: descriptions in HTML» | SKILL.md:98–99 (намеренно, по плану) |
| SKILL.md:55–56 «`--comment` needs a target. Moving a task does not tick … "completed" flag» | SKILL.md:58–59, без изменений по смыслу |
| SKILL.md:74–76 пункт **label** | SKILL.md:77–80, перенос строк и вставка «(quote one of several words)» |
| SKILL.md:138 «(`assign`: report it, never try another email or `--reassign` on your own)» | SKILL.md:72–76 (пункт **assign**: «do not try another», «add `--reassign` only when the human or your step says»), ссылка в SKILL.md:143 |
| yougile.py:424–425 `raise Failure(REFUSED, …)` | yougile.py:426–430, тот же код выхода и текст, плюс совет |
| yougile.py:984 help `--status` у `search` | yougile.py:1157, дополнен id |
| BLUEPRINT R9 «`get` shows text as Yougile keeps it, with no reverse conversion» | BLUEPRINT R9 (намеренно, по плану) |

Ни одно правило не потеряно.

## Пропущено ранее

Нет.

## Left by the plan

Нет: план оставляет пустой список («Leave: none»).

## Вопросы человеку

Нет вопросов.

## Найдено по пути

- `[kit-builder]` `flow_diagram.py` на ките без потоков по-прежнему падает (exit 2); см. отчёт
  assess.
