# Отчёт о ките: tracker-yougile 0.3.0

- Дата: 2026-10-12
- Кит: корень worktree рана `improve/tracker-yougile-link` (путь задан задачей)
- Коммит: `9a1a1da` (визит 1 шага `evaluate`; blueprint `dcd8211`)
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

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет («Flow skeletons: none») |
| b. Рубрика | 4 находки (0 high, 1 medium, 3 low); 9 из 12 критериев без находок |
| Охват | повторная оценка изменённого текста и полный проход по 5 файлам из diff (kit.yaml, README.md, BLUEPRINT.md, skills/tracker/SKILL.md, skills/tracker/yougile.py — в части `link`) |
| Правило остановки | не выполнено: 0 high, 1 medium (F5.1) — совет для ворот выпуска, не блок |

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

Тесты: `uv run --no-project python -m unittest discover -s tests` — `Ran 104 tests`, `OK`.

## Вердикт

`approved`: `lado kits check` без ошибок, бюджет зелёный, `--compare` без расхождений,
открытых high нет. F5.1 (medium) и три low не блокируют; правило остановки не выполнено
из-за F5.1 — решать человеку на воротах (вопрос 1).

## Исправить в первую очередь

1. Правило `derived` в SKILL.md: сказать, что оно выбирает слово, а не велит связывать без
   просьбы (или, если человек хотел обратного, внести это в правило записи) (F5.1).
2. Задача без `idTaskProject`: искать связь и по `id` другой задачи (F5.2).

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

Не применимо: потоков нет. Проба на доске «polygon» (R12) — в build-report, с id
комментариев и выводом `get`.

### 5. Противоречия

- **F5.1** [medium] `skills/tracker/SKILL.md:86` 
  > DEV-2). A task that grew out of another, e.g. one you filed while working on it, is
  > linked to it with `derived`. The script writes a comment in each task's chat, one line

  Правило читается и как выбор слова, и как приказ связывать каждую задачу, заведённую
  по ходу работы. Второе прочтение спорит с правилом записи SKILL.md:29–30 «Create,
  transition, comment, assign, label or link only when your / role, your step or the
  human asks for it», ведь скилл — не роль, не шаг и не человек. Одни агенты будут без
  просьбы писать от имени пользователя в две задачи, другие нет. Бриф называет это
  «правило, когда связывать». Но правило kit-sdlc «задача, созданная в ходе прогона,
  связывается с задачей прогона» он выносит в отдельную правку («Вне задачи»). Значит,
  «когда» решает кит процесса, а скилл — какое слово.
  Fix: «When you link a task to the one it grew out of (e.g. one you filed while working
  on it), use `derived`.» Если человек хочет, чтобы связывали всегда, — дописать это
  исключение в правило записи SKILL.md:29–30. Passes: 1/3, confirmed (обе цитаты в файле;
  description SKILL.md:10 добавляет триггер «link it to the task it grew out of»).
- **F5.2** [low] `skills/tracker/yougile.py:1298` 
  > keys = [k for k in (other.get("idTaskProject"), other.get("idTaskCommon")) if k]

  Комментарий пишет ключ `key_of(other)`, а это `return task.get("idTaskProject") or
  task.get("id")` (yougile.py:535). У задачи без `idTaskProject` в строку попадает её
  `id`, а поиск ищет только по `idTaskProject` и `idTaskCommon`. Такая связь никогда не
  станет «already linked», и каждый повтор, который SKILL.md советует после сбоя,
  допишет её ещё раз. Проверено на образце: `_link_comment` для `other={'id':
  '0f0e…0001','idTaskCommon':'ID-5'}` и строки `**Link:** relates to 0f0e…0001 «x»`
  вернул `None`. Бывают ли такие задачи в Yougile, не проверено; запасной вариант в
  `key_of` говорит, что автор это допускал.
  Fix: добавить `other.get("id")` в `keys`. Passes: 1/3, confirmed (запуск на образце).
- **F5.3** [low] `skills/tracker/yougile.py:1319` 
  > rerun = ("send Yougile nothing more until you are told it answers again, then run it "

  При 429 после ожидания (exit 12) `_link_failure` склеивает строку `_http_failure` с
  советом и выдаёт: «linked on DEV-1 (comment c1), not on DEV-2: Yougile is rate
  limiting requests (429) after a wait: nothing of this request was applied; report it;
  run it again». «report it» и «run it again» стоят рядом. Агент, скорее всего, сделает
  и то и другое. Это безопасно, потому что повтор сначала проверяет, но строка
  противоречит себе.
  Fix: убрать «; report it» из reason, когда к нему добавляется совет повторить. Passes:
  1/3, confirmed (вывод `_link_failure` на этом сбое, запуск выше).

### 6. Дублирование

Повторы BLUEPRINT R3 ↔ SKILL.md (фразы, «already linked», ограничения) оправданы:
BLUEPRINT — требования, SKILL.md — текст для агента. Абзац о сбое записи (SKILL.md:185–186)
отсылает к **link** («as its line says (see **link**)»), не повторяя правило. Похожих
абзацев скрипт не нашёл.

### 7. Когда звать человека

Неизвестное слово — «pick the listed word that fits, never invent one» (SKILL.md:92);
сбой — к коду выхода и «report» через супервизора (без изменений). Новых решений,
которые принимает только человек, нет; F5.1 — вопрос 1.

### 8. Циклы при повторном визите

Не применимо: потоков нет. Повтор команды: «it checks first and writes no link twice»
(SKILL.md:97), но см. F5.2.

### 9. Краткость и «почему»

- **F9.1** [low] `README.md:91` 
  > `statuses` maps the words process kits use to columns, and `labels` maps label words to a

  README перечисляет необязательные настройки, а новую `link_types` не называет.
  Пользователь, который настраивает проект по README, о ней не узнает. Формат лежит в
  SKILL.md, и README туда отсылает. Fix: добавить «, and `link_types` gives link words
  their phrases». Passes: 1/3, confirmed (`grep -n link_types README.md` — пусто).

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
| 2. Работа вне потока, слияние без ворот | Не применимо: потоков и слияний нет; `link` ограничен SKILL.md:29–30 (см. F5.1). |
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
  необязательны, любая метка, оба ключа, `(?![\w-])` против более длинного ключа (кроме
  случая F5.2).
- Частичная запись и неясный ответ — RESOLVED: `_link_failure`; тесты
  `test_second_side_fails`, `test_unclear_answer_advises_running_it_again` (оговорка F5.3).
- argparse, тесты (18 в `LinkTasksTest`, всего 104 OK), SKILL.md (описание, таблица,
  пункт **link**, пример, exit 11, абзац о сбое), kit.yaml 0.3.0, README, проба на
  «polygon» — RESOLVED, сверено с файлами. Список build-report «fixed» совпадает с diff.

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

1. Правило `derived` (F5.1): скилл задаёт только слово («связывая задачу с той, из
   которой она выросла, бери `derived`»), а *когда* связывать, решает кит процесса
   (правка kit-sdlc после этой)? Или агент связывает такую задачу всегда, без просьбы?
   Рекомендую первое: так задумано разделение в брифе, и правило записи остаётся
   единственным местом, где сказано, когда писать.
