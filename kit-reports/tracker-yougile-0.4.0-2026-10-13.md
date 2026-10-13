# Отчёт о ките: tracker-yougile 0.4.0

- Дата: 2026-10-13
- Кит: корень worktree рана `improve/tracker-yougile` (задача называет этот репозиторий)
- Коммит: `0f10f20` (blueprint `0851070`)
- Оценил: критик kit-builder (слои a и b)
- Режим: повторная оценка. Предыдущий отчёт — `kit-reports/tracker-yougile-0.4.0-2026-10-13-assess.md`
  (полная оценка `d4cc21f`), а база берётся из плана: `git diff d4cc21f -- kit.yaml README.md
  BLUEPRINT.md agents flows skills`. В изменении два коммита. `0851070` правит BLUEPRINT:
  R3 и строку 0.4.0 в разделе 5. `0f10f20` правит SKILL.md в трёх местах: **edit**,
  **attach** и «Writing in Yougile».
- Проходы: изменение маленькое (≈10 строк), поэтому три прохода критик сделал сам, без
  суб-агентов. (1) От плана и build-report к diff. (2) От изменённых абзацев SKILL.md к тем
  местам, на которые они ссылаются: общий абзац о записи (SKILL.md:31–32), **A new task
  with files** (SKILL.md:166–168), строка exit 2 в таблице, `cmd_edit`/`_show` в
  yougile.py. (3) От BLUEPRINT R3 и раздела 5 к SKILL.md. После них — проверка вырезанного
  (`--word-diff`) и полный проход по двум файлам из diff, SKILL.md и BLUEPRINT.md, целиком.
  Находок одного прохода нет, отброшенных нет.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет («Flow skeletons: none») |
| b. Рубрика | 0 открытых находок; F5.1, F6.1, F6.2 оценки — RESOLVED; 12 из 12 критериев без находок |
| Охват | повторная оценка изменённого текста; полный проход по 2 файлам из diff (skills/tracker/SKILL.md, BLUEPRINT.md) |
| Правило остановки | выполнено: 0 high, 0 medium в изменённом тексте |

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
# Complexity budget: tracker-yougile 0.4.0

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
$ flow_diagram.py . --out …
no flows in .: nothing to do (код выхода 0)
$ flow_diagram.py . --compare BLUEPRINT.md
no flows in . or BLUEPRINT.md: nothing to do (код выхода 0)
```

Тесты: `uv run --no-project python -m unittest discover -s tests` — `OK`.

## Вердикт

`approved`. `lado kits check` прошёл без ошибок, бюджет зелёный, `--compare` расхождений
не показал, открытых high нет. Все три находки оценки исправлены, правила при сокращении
текста не потерялись. Правило остановки выполнено.

## Исправить в первую очередь

Нечего: открытых находок нет.

## Находки

### 1. Границы ролей

Не применимо: ролей нет. Правило записи для `attach` осталось в одном месте: «Create,
transition, comment, assign, label, link or attach only / when your role, your step or the
human asks for it, and only on the tasks named.» (SKILL.md:31–32).

### 2. Передача между шагами

Не применимо: потоков нет (R2).

### 3. Готовность и исходы

Изменение не затрагивает исходы. Код выхода для `create` с `attachment:` остался:
«(refused there, / exit 2: the task has no files yet)» (SKILL.md:166–167), строка exit 2
в таблице не тронута.

### 4. Независимая проверка

Не применимо: потоков нет.

### 5. Противоречия

SKILL.md:74 «**edit** prints the task as `get` does, without its files and comments»
сходится с кодом: `cmd_edit` печатает через `_show`, а `Files:` печатает только `cmd_get`.
С BLUEPRINT R3 (BLUEPRINT.md:50) тоже сходится.

### 6. Дублирование

Повторы F6.1 и F6.2 убраны, на их месте теперь указатели: «Attaching is a write (see
above).» (SKILL.md:160), «`create`: see **A new task with files**.» (SKILL.md:190).
Похожих абзацев скрипт не нашёл.

### 7. Когда звать человека

Не изменилось. Вопрос оценки об `attach` без отдельного «да» человек решил на triage:
оставить, как в Y6 (план, «Answers»; BLUEPRINT раздел 5, строка 0.4.0).

### 8. Циклы при повторном визите

Не применимо: потоков нет.

### 9. Краткость и «почему»

Текст стал короче на два правила, теперь они даны ссылками. «see above» указывает на общий
абзац о записи; та же форма уже есть в SKILL.md:220.

### 10. Описания скиллов

description не меняли.

### 11. Нейтральность к провайдеру

В изменении нет названий инструментов, CLI или моделей.

### 12. Безопасность и границы

Жирный абзац о публичности файла и запрет на секреты остались: «**An / uploaded file is
public: … Never attach secrets (`.env`, keys, tokens, passwords), personal data, or /
database or memory dumps.**» (SKILL.md:160–163).

## Известные дыры

| Известная дыра | Находка, или как кит её закрывает |
|---|---|
| 1. Красная проверка без учёта причины в окружении | Изменение не трогает. Сбой хранилища файлов отделён от сбоя трекера: «only it is unreachable: report it … and go on using the tracker» (SKILL.md, **download**). |
| 2. Работа вне потока, слияние без ворот | Не применимо: потоков и слияний нет. |
| 3. Путь вне worktree рана | Изменение не трогает. Временная папка для `download` вне репозитория выбрана намеренно (см. оценку). |
| 4. Вердикт без порога важности | Не применимо: рецензента нет. |
| 5. Зависимый скилл пишет или спрашивает там, где роли нельзя | Не применимо: зависимых скиллов нет. |
| 6. Команды не в ладу с `expects.commands` | `expects commands: uv`, предупреждения нет. Изменение команд не добавляет. |
| 7. Read-only роли не в ладу с тем, что делают | Не применимо: ролей нет. |

## Не прослежено

Новых элементов нет. R3 и строка 0.4.0 в разделе 5 описывают изменение. Бюджет зелёный,
скелетов нет, расхождений нет.

## Прошлые находки

- **F5.1** RESOLVED — SKILL.md:74 «prints the task as `get` does, without its files and
  comments»; BLUEPRINT.md:50 то же.
- **F6.1** RESOLVED — SKILL.md:160 «Attaching is a write (see above).»; правило в
  SKILL.md:31–32.
- **F6.2** RESOLVED — SKILL.md:190 «`create`: see **A new task with files**.»; правило в
  SKILL.md:166–167, строка exit 2 в таблице на месте.
- Вопрос 1 (`attach` без отдельного «да») — решён человеком: оставить (план, «Answers»).
- Список «fixed» в build-report совпадает с diff `d4cc21f..0f10f20`; BLUEPRINT R3 и
  раздел 5 соответствуют плану; версия 0.4.0 не менялась, как и сказано в плане.

## Вырезанные правила

| Удалённое правило (файл:строка в базе) | Где оно теперь |
|---|---|
| SKILL.md:74 «prints the task as `get` does, without comments» | SKILL.md:74, уточнено: «without its files and comments» (F5.1) |
| SKILL.md:160–161 «Attaching is a write: only when your role, your step or the human asks for it, and only to the tasks named.» | SKILL.md:31–32 «link or attach only when your role, your step or the human asks for it, and only on the tasks named» |
| SKILL.md:191–192 «in `create` any `attachment:` link is refused (exit 2)» | SKILL.md:166–167 «`create` it without `attachment:` links (refused there, exit 2: the task has no files yet)»; строка exit 2 таблицы «`attachment:` links in `create`» |
| BLUEPRINT.md:50 «Prints the task as `get` does, without comments.» | BLUEPRINT.md:50, уточнено (F5.1) |

Ничего не потеряно.

## Пропущено ранее

Нет. Полный проход по SKILL.md и BLUEPRINT.md целиком новых находок не дал.

## Left by the plan

Нет (план: «Leave: none»).
