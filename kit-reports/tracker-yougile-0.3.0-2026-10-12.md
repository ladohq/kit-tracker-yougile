# Отчёт о ките: tracker-yougile 0.3.0

- Дата: 2026-10-12
- Кит: корень worktree рана `improve/tracker-yougile-link` (путь задан задачей)
- Коммит: `d020dc1` (визит 2 шага `evaluate`; визит 1 — `9a1a1da`; blueprint `dcd8211`)
- Оценил: критик kit-builder (слои a и b)
- Режим: повторная оценка относительно `kit-reports/tracker-yougile-0.2.0-2026-10-12.md`
  (оценка `aa5f135`; эту базу называет план, она же — оценка `assessment` этого рана),
  `git diff aa5f135 -- kit.yaml README.md BLUEPRINT.md agents flows skills`.
  Изменение: 2 коммита — `dcd8211` (BLUEPRINT: R3, R6, R12, раздел 2, журнал) и `9a1a1da`
  (yougile.py, тесты, SKILL.md, kit.yaml, README, строка сборки в разделе 4 BLUEPRINT).
  `.lado/tracker.yaml` (6cd0c9c, из main) — настройки репозитория, не текст кита.
- Проходы: изменение среднее (≈250 строк текста кита), три прохода критик сделал сам,
  без суб-агентов. (1) От плана, брифа `/lad-21-yougile-brief.md` и build-report к diff:
  каждый пункт сверен с файлами. (2) От кода: `cmd_link`, `_link_comment`, `_link_failure`,
  `link_phrases`, `_validate` — чтением и запуском (тесты; разбор примера настроек из
  SKILL.md через `load_config`; сообщения `_link_failure` и `_link_comment` на образцах).
  (3) От SKILL.md (пункт **link**, правило записи, таблица кодов, абзац о сбое записи) к
  R3, R6, R10, R12 BLUEPRINT и README. Затем вырезанные правила проверены по
  `--word-diff`, и сделан полный проход по SKILL.md, README.md, kit.yaml, BLUEPRINT.md
  целиком и по yougile.py в части, которую трогает `link` (`cmd_link` и всё, что он
  вызывает: `api.task`, `api.pages`, `_send_message`, `load_config`/`_validate`, коды
  ошибок `_network_failure`/`_http_failure`). Остальной код yougile.py не менялся с
  полного прохода `aa5f135`. Находок одного прохода: 4, все оставлены как
  подтверждённые (с доказательством в находке); отброшенных нет.
- Визит 2 (`d020dc1`). Изменение после визита 1 (`git diff 5463dc2 d020dc1`): один коммит,
  README.md, SKILL.md, yougile.py, тесты (≈25 строк). Три прохода критик сделал сам:
  (1) от находок визита 1 к diff, (2) от кода (`REPORT_IT`, `_link_comment`,
  `_link_failure`) к двум новым тестам и к остальным местам с «report it» в yougile.py,
  (3) от SKILL.md к правилу записи и к BLUEPRINT R3. Полный проход перед вердиктом: README.md
  и SKILL.md целиком, yougile.py в части `link` (как в визите 1). Находок одного прохода: 1,
  оставлена как подтверждённая (F5.4); отброшенных нет.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет («Flow skeletons: none») |
| b. Рубрика | 1 открытая находка (0 high, 0 medium, 1 low: F5.4); визит 1: F5.1, F5.2, F5.3, F9.1 — RESOLVED; 11 из 12 критериев без открытых находок |
| Охват | повторная оценка изменённого текста; визит 1 — полный проход по 5 файлам из diff (kit.yaml, README.md, BLUEPRINT.md, skills/tracker/SKILL.md, skills/tracker/yougile.py — в части `link`); визит 2 — по README.md, SKILL.md, yougile.py (в части `link`) |
| Правило остановки | выполнено: 0 high, 0 medium в изменённом тексте (визит 1 — не выполнено из-за F5.1, теперь RESOLVED) |

Счёт относится только к тому, что названо в строке «Охват».

### `lado kits check .`

```
tracker-yougile: OK (0 agents, 1 skills, 0 packs and 0 flows)
expects commands: uv
```

Expects: `expects commands: uv`. Предупреждения `expects.commands needs LADO …` нет.

Read-only: строки `read-only roles: …` нет (у кита нет ролей); `dependencies.lado: ">=0.30"`.

### Скрипт бюджета (код выхода 0)

```
# Complexity budget: tracker-yougile 0.3.0

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

```
no flows in . or BLUEPRINT.md: nothing to do (код выхода 0)
```

Тесты (визит 2): `uv run --no-project python -m unittest discover -s tests` — `Ran 106 tests`, `OK`.
`lado kits check`, бюджет и `--compare` визита 2 дают тот же вывод, что выше.

## Вердикт

`approved` (визит 2): `lado kits check` без ошибок, бюджет зелёный, `--compare` без
расхождений, открытых high нет. Находки визита 1 исправлены; осталась одна low (F5.4,
формулировка BLUEPRINT R3), она не блокирует. Правило остановки выполнено.

## Исправить в первую очередь

1. BLUEPRINT R3: та же формулировка `derived`, что в SKILL.md (F5.4; правит владелец
   блюпринта, не автор).

## Находки

### 1. Границы ролей

Не применимо: ролей нет. Права скилла: SKILL.md:29–30 «Create, transition, comment,
assign, label or link only when your / role, your step or the human asks for it, and only
on the tasks named.» — `link` двух задач пишет только в две названные задачи.

### 2. Передача между шагами

Не применимо: потоков нет (R2).

### 3. Готовность и исходы

Не применимо: потоков нет. Исходы команды: «already linked … nothing changed» — exit 0;
частичная запись — строка `linked on KEY (comment …), not on KEY2: …; run it again` с
кодом сбоя; самосвязь — exit 2 до запросов и после GET; неизвестное слово — exit 11.

### 4. Независимая проверка

Не применимо: потоков нет. Проба на доске «polygon» (R12) — в build-report визита 1, с id
комментариев и выводом `get`. В визите 2 её не повторяли: правки касаются задачи без
ключа проекта и текста ошибки 429, и оба случая покрыты тестами на фейковом API.

### 5. Противоречия

- **F5.4** [low] `BLUEPRINT.md:102`
  > A task that grew out of another is linked to it with `derived`.

  SKILL.md после F5.1 говорит только о выборе слова: «When you link a task to the one it
  grew out of, e.g. one you filed while working / on it, use `derived`» (SKILL.md:86–87).
  BLUEPRINT R3 по-прежнему звучит как приказ связывать. Агенты BLUEPRINT не читают, но
  следующий автор, сверяясь с ним, может вернуть в SKILL.md старое прочтение. Автор
  оставил R3 как есть сознательно: менять блюпринт сверх раздела 4 ему нельзя.
  Fix: в R3 написать «A task linked to the one it grew out of uses `derived`; when to
  link is the write scope's and the process kit's». Править аналитику или человеку.
  Passes: 1/3, confirmed (`grep -nF` находит обе строки).

### 6. Дублирование

Повторы BLUEPRINT R3 ↔ SKILL.md (фразы, «already linked», ограничения) оправданы:
BLUEPRINT — требования, SKILL.md — текст для агента; расхождение одной фразы — F5.4.
Абзац о сбое записи (SKILL.md:185–186) отсылает к **link**, не повторяя правило. Похожих
абзацев скрипт не нашёл.

### 7. Когда звать человека

Неизвестное слово — «pick the listed word that fits, never invent one» (SKILL.md:92);
сбой — к коду выхода и «report» через супервизора (без изменений). Новых решений для
человека нет: вопрос визита 1 решён (F5.1, «только слово»).

### 8. Циклы при повторном визите

Не применимо: потоков нет. Повтор команды: «it checks first and writes no link twice»
(SKILL.md:97); после F5.2 это верно и для задачи без `idTaskProject`.

### 9. Краткость и «почему»

Новые строки кода несут свой «почему»: «# The id too: a task without idTaskProject is
written by its id (key_of).», «# the rerun is the advice, not a report». README назвал
`link_types` (F9.1 RESOLVED).

### 10. Описания скиллов

Один свой скилл; description называет обе формы `link` и триггер «link it to the task
it grew out of» (SKILL.md:6–10). Зависимых и ожидаемых скиллов нет.

### 11. Нейтральность к провайдеру

Без изменений: `${SKILL_DIR}` с запасным правилом (SKILL.md:22), имён CLI нет.

### 12. Безопасность и границы

Связь пишет только в две названные задачи (SKILL.md:29–30); снять её можно только
удалением комментариев, о чём SKILL.md говорит прямо (SKILL.md:97–99). Проба на облаке
(R12) шла на доске «polygon» из отдельной папки с `board: polygon`. Человек разрешил:
«Можешь взять любые задачи на доске polygon. Или создать новые» (BLUEPRINT R12).
Задачи LAD-23 и LAD-24 остались на доске.

## Известные дыры

| Известная дыра | Находка, или как кит её закрывает |
|---|---|
| 1. Красная проверка без учёта причины в окружении | Без изменений: SKILL.md отделяет сообщения `uv`/Python от кодов скрипта; `link` двух задач различает сбой с неясным ответом (exit 9, 12) и отказ. |
| 2. Работа вне потока, слияние без ворот | Не применимо: потоков и слияний нет; `link` ограничен SKILL.md:29–30; правило `derived` задаёт только слово (F5.1 RESOLVED). |
| 3. Путь вне worktree рана | Без изменений: `${SKILL_DIR}`, настройки ищутся до корня репозитория. |
| 4. Вердикт без порога важности | Не применимо: рецензента нет. |
| 5. Зависимый скилл пишет или спрашивает там, где роли нельзя | Не применимо: зависимых скиллов нет. |
| 6. Команды не в ладу с `expects.commands` | Без изменений: только `uv`, `dependencies.lado: ">=0.30"`, предупреждения нет. |
| 7. Read-only роли не в ладу с тем, что делают | Не применимо: ролей нет. |

## Не прослежено

`link` двух задач назван в R3, `link_types` — в R6, проба — в R12; раздел 2 («a link (to
a URL or between tasks) is a comment»), строка 0.3.0 журнала. Элементы раздела 3 те же
(действий по-прежнему десять), бюджет зелёный; скелетов нет («Flow skeletons: none»).
Расхождений нет.

## Прошлые находки

В отчёте 0.2.0 открытых находок нет. Пункты плана:

- LAD-21, `link KEY KEY2 [--type]` (R3) — RESOLVED: yougile.py:1247–1293 `cmd_link`;
  exit 2 до запросов (`--type` с URL, `--title` с ключом, одна строка), после GET «are the
  same task»; тесты `test_wrong_arguments_before_any_request`, `test_self_link`,
  `test_task_not_on_the_board`.
- Слова и фразы, `link_types` (R3, R6) — RESOLVED: `LINK_TYPES`, `CONFIG_MAPS`,
  `_validate` (больше одного ` / ` или пустая фраза — exit 3 с путём и строкой),
  `link_phrases` (exit 11 со списком). Пример из SKILL.md разобран: `('блокирует',
  'заблокирована') ('связана с', 'связана с')`.
- Текст комментария — RESOLVED: «**Link:** » + фраза, `key_of(other)`, «название»;
  `textHtml` с `html.escape`; URL задачи нет.
- «Уже связано» — RESOLVED: `_link_comment` — `api.pages`, без удалённых, `**`
  необязательны, любая метка, оба ключа, `(?![\w-])` против более длинного ключа (после
  F5.2 — и по `id`).
- Частичная запись и неясный ответ — RESOLVED: `_link_failure`; тесты
  `test_second_side_fails`, `test_unclear_answer_advises_running_it_again` (оговорка F5.3).
- argparse, тесты (18 в `LinkTasksTest`, всего 104 OK), SKILL.md (описание, таблица,
  пункт **link**, пример, exit 11, абзац о сбое), kit.yaml 0.3.0, README, проба на
  «polygon» — RESOLVED, сверено с файлами. Список build-report «fixed» совпадает с diff.

- Визит 1, **F5.1** RESOLVED — SKILL.md:86–87 «When you link a task to the one it grew out
  of, e.g. one you filed while working / on it, use `derived`»: только слово, когда — по
  правилу записи SKILL.md:29–30. Остаток в BLUEPRINT R3 — F5.4.
- Визит 1, **F5.2** RESOLVED — yougile.py:1300–1301 «keys = [k for k in
  (other.get("idTaskProject"), other.get("idTaskCommon"), / other.get("id")) if k]»; тест
  `test_task_without_project_key_is_found_by_its_id` проходит.
- Визит 1, **F5.3** RESOLVED — yougile.py:1325 «reason = reason.replace(REPORT_IT, "")» только
  при частичной записи. Другие строки с «report it» не задеты: `grep -n "report it"` находит
  только константу и yougile.py:1156 (без «; »). Тест
  `test_rate_limit_on_the_second_side_advises_only_a_rerun` проходит.
- Визит 1, **F9.1** RESOLVED — README.md:92 «and `link_types` gives link words their phrases
  in the two tasks».

## Вырезанные правила

| Удалённое правило (файл:строка в базе) | Где оно теперь |
|---|---|
| R3 `link`: «posts the URL … as a comment and prints its id; Yougile has no link object. A branch or commit not pushed … never pushes to make a link.» (BLUEPRINT.md:72–75) | BLUEPRINT.md:74–77, дословно, внутри формы URL |
| R6 «An action that needs a missing setting names it.» (BLUEPRINT.md:107–108) | BLUEPRINT.md:141–142 |
| SKILL.md description «link a URL to it» (SKILL.md:6) | SKILL.md:6–7 «link a URL or another task to it» |
| Exit 11, «fix the request once (a status: see **Status**)» (SKILL.md:157) | SKILL.md:178, расширено |
| «again, as its line says. Whatever the code, never» (SKILL.md:163) | SKILL.md:183–185, без потерь |
| yougile.py `cmd_link` для URL (`args.url`) | `_link_url`, то же поведение (`args.target`); тесты URL проходят |
| README «links a URL to them», kit.yaml description | расширено, ничего не потеряно |

## Пропущено ранее

Нет.

## Left by the plan

Нет (план: «Leave: none»).

## Вопросы человеку

Нет (вопрос 1 визита 1 решён: вариант «только слово», F5.1).
