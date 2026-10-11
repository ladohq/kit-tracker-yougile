# Отчёт о ките: tracker-yougile 0.1.1

- Дата: 2026-10-11
- Кит: корень worktree рана `improve/tracker-yougile-0-1-2` (путь задан задачей)
- Коммит: `5cda9b4`
- Оценил: критик kit-builder (слои a и b)
- Режим: полная оценка (шаг `assess` рана `improve/tracker-yougile-0-1-2`). Отчёт, который
  назвала задача (`kit-reports/tracker-yougile-0.1.1-2026-10-11.md`), не взят вместо оценки
  по двум причинам. Он не полный: это повторная оценка относительно 0.1.0, режим «повторная
  оценка». И текст кита после оценённого им коммита `813090f` менялся не только в строке
  `version:`: `git diff 813090f -- kit.yaml README.md BLUEPRINT.md agents flows skills`
  показывает ещё строку 0.1.1 в журнале BLUEPRINT (раздел 5). Шаг требует в таком случае
  оценивать заново, а тот отчёт служит только фоном.
- Проходы: три независимых суб-агента получили рубрику, `lado-kit-format` и папку кита.
  Каждый начинал со своего места: (1) kit.yaml и README, затем SKILL.md, yougile.py,
  BLUEPRINT; (2) каждая команда yougile.py против SKILL.md, с `--help` и тестами (66, OK);
  (3) требования R1–R12 BLUEPRINT против SKILL.md, README и кода. Находки одного прохода:
  3. Отброшены 2: пересказ «nothing was sent» в SKILL.md:120–122 и тройное «self-hosted
  untried» в README. Это формулировки, вреда в файлах нет, а README читает человек.
  Сохранена как подтверждённая 1: F7.1. Зависимых и ожидаемых скиллов у кита нет.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет («Flow skeletons: none») |
| b. Рубрика | 4 находки (0 high, 2 medium, 2 low); 9 из 12 критериев без находок |
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
# Complexity budget: tracker-yougile 0.1.1

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

Потоков нет (R2), скелетов в BLUEPRINT.md тоже нет, так что рисовать и сравнивать нечего.
На таком ките скрипт падает. Это сбой скрипта, а не кита (см. «Найдено по пути»):

```
$ flow_diagram.py . --out kit-reports/tracker-yougile-0.1.1-2026-10-11-assess
error: kit.yaml: states must be a non-empty mapping   (exit 2)
$ flow_diagram.py . --compare BLUEPRINT.md
error: kit.yaml: states must be a non-empty mapping   (exit 2)
```

Тесты (это не текст кита): `uv run --no-project python -B -m unittest discover -s tests`
дал `Ran 66 tests`, `OK` (проход 2).

## О задаче рана

Просьба человека («перевести вывод в текст») касается `get`: описание задачи печатается как
есть, в HTML. yougile.py:778 `    print("\nDescription:\n%s" % (task.get("description") or "(empty)"))`.
Комментарии печатаются как текст: поле `text`, yougile.py:792. SKILL.md это поведение
описывает честно: SKILL.md:94 «`get` shows text as Yougile keeps it: descriptions in HTML,
comments as you wrote them.», а также SKILL.md:26–27 «the first paragraph
(`<p>[LADO: …]</p>`) of a description». Поэтому по рубрике это не находка: текст и код не
расходятся. Но вред реален. Агент читает описание с тегами, а если перенесёт его кусок в
`comment` или `create`, теги покажутся буквально: SKILL.md:92–93 «Anything else, HTML too,
shows as plain text». Если изменение сделают, вместе с кодом поменяются SKILL.md:26–27
и :94, R-требование BLUEPRINT о выводе `get` и тесты `get`.

## Исправить в первую очередь

1. Показывать в таблице `label` метку в кавычках: `--add '<label>'`. Сейчас метка из
   нескольких слов уходит человеку как ошибка его настроек (F3.1).
2. Слово процесса, которого нет в `statuses`, сообщать человеку, а не угадывать колонку
   (F7.1).
3. Дописать «or id» в `--help` у `search --status` (F5.1).

## Находки

### 1. Границы ролей

Ролей нет. Права агента задаёт сам скилл: SKILL.md:29 «Reading is always fine. Create,
transition, comment, assign, label or link only when your».

### 2. Передача между шагами

Не применимо: потоков нет. Сбои уходят строкой и командой, а не путём к файлу:
SKILL.md:123 «failure: as a worker, send the supervisor that line and the command with `send_message`;».

### 3. Готовность и исходы

- **F3.1** [medium] `skills/tracker/SKILL.md:48` (также :110, :131)
  > | add or remove labels | `label DEV-1 [--add L ...] [--remove L ...]` |
  Пример метки в настройках состоит из нескольких слов (SKILL.md:110
  `  waiting for release: 'Release: Waiting'`), а в таблице `L` стоит без кавычек. У `--add`
  `nargs="+"` (yougile.py:1024), поэтому `label DEV-1 --add waiting for release` даёт три
  слова и exit 3: `label 'waiting' is not in 'labels' of .lado/tracker.yaml (its words:
  waiting for release); the user maps it to 'Sticker: State' there`. Проходы 1 и 2 проверили
  это офлайн. Строка 3 таблицы велит «report it; the user fixes the file», и ошибка
  кавычек агента уходит человеку как неверный файл настроек, а шаг ждёт ответа впустую.
  Fix: в таблице `label DEV-1 [--add '<label>' ...] [--remove '<label>' ...]`, как у
  `transition '<status>'`; по желанию ещё в пункт **label** добавить «a label of several
  words is quoted». Passes: 2/3

### 4. Независимая проверка

Не применимо: потоков нет. Отнять задачу у другого может только человек или шаг:
SKILL.md:73 «when the human or your step says to take it from them.».

### 5. Противоречия

- **F5.1** [low] `skills/tracker/yougile.py:984`
  > p.add_argument("--status", help="a column title, or a word of statuses")
  SKILL.md:52–53 говорит, что статус — это заголовок колонки, её id или слово `statuses`, а
  SKILL.md:18 отсылает к `--help`. У `create` и `transition` help говорит «a column title or
  id», а у `search` id нет, хотя `search` его принимает (тот же `api.column`, yougile.py:736).
  Это остаток исправления F3.3 в 0.1.1: `git show 56ab46f` поменял help только у `create` и
  `transition`. Когда заголовки повторяются, агент по `search --help` решит, что колонку
  по id не найти. Fix: `help="a column title or id, or a word of statuses"`. Passes: 3/3

### 6. Дублирование

- **F6.1** [low] `skills/tracker/SKILL.md:138` (и :69–73)
  > | 11 | Yougile refused the request, a status is not a column, an email is no account, or `assign` refused a task another account holds | read the line, fix the request once; if it still fails, report it (`assign`: report it, never try another email or `--reassign` on your own) |
  Правило `assign` (не пробовать другой email, `--reassign` только по слову человека или
  шага) целиком записано в пункте **assign** (SKILL.md:70 «given: an unknown one is refused
  (exit 11); report it and do not try another, since a») и ещё раз в строке 11. Сейчас копии
  совпадают, но держать их в согласии приходится в двух местах. Проход 3 видел повтор, но не
  счёл его находкой: строка нужна, чтобы отменить «fix the request once» для `assign`.
  Ссылка это тоже делает. Fix: в строке 11 оставить «(`assign`: never retry; see **assign**
  above)». Passes: 2/3

### 7. Когда звать человека

- **F7.1** [medium] `skills/tracker/SKILL.md:100` (код: yougile.py:424)
  > an action that needs a missing setting names it (exit 3). The file is a strict subset of
  Для `statuses` это неверно. Допустим, слово процесса («review») не записано в `statuses`
  и не совпадает с заголовком колонки. Тогда `api.column` бросает
  `raise Failure(REFUSED, "status '%s' %s; its columns: %s"`, то есть exit 11, и строка не
  называет `statuses` (yougile.py:410–425: exit 3 только когда слово в `statuses` есть).
  По строке 11 таблицы («fix the request once») агент сам выберет колонку из списка,
  например `Code review`. Задача уедет в колонку, которую выбрал агент, а не пользователь
  в настройках, и в разных ранах колонки будут разные. Импакт поднят до medium: проход 2
  дал low, но это запись в Yougile от имени пользователя. Fix: когда цель не колонка и не
  слово `statuses`, писать в строке, что слово можно добавить в `statuses`, и перечислять
  его слова; в SKILL.md (пункт **Status**) сказать, что слово процесса без колонки
  сообщают (его добавит пользователь), а не угадывают. Passes: 1/3, confirmed: yougile.py:419–424,
  ветка CONFIG только `if target in config["statuses"]:`, иначе
  `raise Failure(REFUSED, …)`; тест tests/test_yougile.py:431 ждёт
  `"status 'qa' is not a column of the board; its "` (exit REFUSED).

Остальное на месте: SKILL.md:123–125 (воркер пишет супервизору, лид — человеку, ждать,
если шаг без трекера не идёт), правила остановки для exit 5 и 9.

### 8. Циклы при повторном визите

Не применимо: потоков нет. Повторы ограничены: «fix the request once» (SKILL.md:138), 429
повторяется один раз (yougile.py:289).

### 9. Краткость и «почему»

Пустых фраз в SKILL.md нет. У неочевидных правил есть причина: SKILL.md:93 «Write each
paragraph on one line: Yougile shows every line break.», SKILL.md:24–25 (запись идёт от
имени пользователя, отсюда метка).

### 10. Описания скиллов

Скилл один, его описание говорит, когда его брать: SKILL.md:7 «whenever your work touches
a task in the tracker, e.g. "file a bug", "take the task",». `dependencies.skills` и
`expects.skills` нет.

### 11. Нейтральность к провайдеру

Путь к скрипту идёт через `${SKILL_DIR}`, и для CLI без него есть запасной вариант:
SKILL.md:21 «If your CLI does not expand `${SKILL_DIR}`, use the folder this SKILL.md is in.».
Имён инструментов, моделей и конфигов отдельных CLI нет. Строки zsh и macOS в README
обращены к человеку.

### 12. Безопасность и границы

Запись только по просьбе роли, шага или человека (SKILL.md:29–31). Удаления нет.
`--reassign` только по слову человека или шага. Ключ не печатается и не сохраняется
(SKILL.md:23); уходит только по https или на localhost (yougile.py:257); TLS не
отключается.

## Известные дыры

| Известная дыра | Находка или как кит с ней справляется |
|---|---|
| 1. Красная проверка без учёта окружения | Обработано: SKILL.md:119 «Any other message that does not start with `yougile.py` or `usage: yougile.py` comes from» (`uv`/Python до запуска, ничего не отправлено); exit 9 и 10 указывают на сеть и CA. Обратный случай, когда ошибка агента подаётся как ошибка настроек, — F3.1. |
| 2. Работа вне потока, merge без гейта | Не применимо: ролей и потоков нет; запись только по просьбе (SKILL.md:29). Merge нет. |
| 3. Путь вне worktree | Обработано: поиск настроек останавливается на `.git`, в том числе на файле `.git` в worktree, yougile.py:197 `if os.path.exists(os.path.join(here, ".git")):`. Файлы кита — через `${SKILL_DIR}`. |
| 4. Вердикт без порога | Не применимо: ревьюера нет. |
| 5. Зависимый скилл, пишущий где нельзя | Не применимо: зависимых скиллов нет. Отчёт воркера уходит супервизору (SKILL.md:123). |
| 6. Команды вне `expects.commands` | Обработано: kit.yaml `commands: [uv]`, `lado: ">=0.30"`. `curl` и `security` из README нужны только человеку для разовой настройки ключа. |

## Не прослежено

Ничего: каждый элемент (kit.yaml, `uv`, скилл `tracker`, yougile.py, тесты, README) назван
в R1–R12 и в таблице раздела 3 BLUEPRINT. Жёлтых и красных мер нет. Скелетов нет, и
BLUEPRINT это говорит: BLUEPRINT.md:177 «Flow skeletons: none; the kit has no flows (R2), so
there are no diagrams.».

## Вопросы человеку

Нет вопросов. Решение о самом изменении вывода `get` уже принято задачей. Входят ли F3.1,
F7.1, F5.1 и F6.1 в 0.1.2, решается на triage.

## Найдено по пути

- `[kit-builder]` `kit-budget/scripts/flow_diagram.py` на ките без `flows/` и без скелетов
  падает с `error: kit.yaml: states must be a non-empty mapping` (exit 2) и с `--out`, и с
  `--compare`. Должен рисовать ноль диаграмм и сообщать «различий нет» с кодом 0. Это
  уже было в отчёте 0.1.1 и не исправлено.
- `[kit-builder]` Имя отчёта по `kit-rubric` («Report»), `<kit>-<version>-<date>.md`, на
  шаге `assess` совпало с уже слитым отчётом той же версии и того же дня
  (`tracker-yougile-0.1.1-2026-10-11.md`). Чтобы не затирать его, этот отчёт назван с
  суффиксом `-assess`. Рубрике стоит сказать, как называть отчёт в таком случае.
