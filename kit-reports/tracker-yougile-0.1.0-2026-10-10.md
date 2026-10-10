# Отчёт о ките: tracker-yougile 0.1.0

- Дата: 2026-10-10
- Кит: корень worktree рана `create/tracker-yougile` (путь, данный задачей)
- Коммит: `59cc5c7`
- Оценил: критик kit-builder (слои a и b)
- Режим: повторная оценка относительно прошлой версии этого отчёта (коммит `0a75b2c`, отчёт в
  `d3d550a`), `git diff 0a75b2c -- kit.yaml README.md BLUEPRINT.md agents flows skills`
- Проходы: три независимых суб-агента получили рубрику, папку кита, diff и прошлый отчёт.
  Каждый начинал со своего места: (1) README Credentials, (2) изменённые функции yougile.py,
  (3) BLUEPRINT и проверка вырезанных правил. Отброшена 1 находка одного прохода, оставленных
  как подтверждённые нет. Полный проход не нужен: в `create` весь текст новый, и первая оценка
  была полной.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 (потоков нет, R2); скелетов в BLUEPRINT.md нет |
| b. Рубрика | 3 находки (0 high, 1 medium, 2 low); 10 из 12 критериев без находок |
| Охват | повторная оценка изменённого текста (README.md, BLUEPRINT.md, SKILL.md, yougile.py) и его окружения, без полного прохода (`create`) |
| Правило остановки | не выполнено: 0 high, 1 medium (F12.4). Это совет к гейту релиза, а не блок |

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

У кита нет потоков (R2), в BLUEPRINT.md нет скелетов, диаграмм нет. Скрипт потоков на таком
ките падает (см. «Найдено по пути»):

```
$ flow_diagram.py . --compare BLUEPRINT.md
error: kit.yaml: states must be a non-empty mapping   (exit 2)
```

Тесты (это не текст кита): `python -B -m unittest discover -s tests` — `Ran 63 tests`, `OK`.

## Исправить в первую очередь

1. README:40: `read -s` без `-r` съедает обратные слэши, поэтому совет экранировать `"` и `\`
   не работает. Нужно `read -rs` (F12.4).
2. Сообщение «write its id» и пример в SKILL.md: кит нигде не показывает id колонок (F3.1).
3. BLUEPRINT R6:90 и R3:42: значение `statuses` может быть id колонки (F5.5).

## Находки

### 1. Границы ролей

Не применимо: ролей нет.

### 2. Передача между шагами

Не применимо: потоков нет.

### 3. Готовность и исходы

- **F3.1** [low] `skills/tracker/yougile.py:418`
  > `            problem = ("is the title of several columns: rename one of them, or write its id"`
  Сообщение и SKILL.md:104 («a column (title, or id if repeated)») велят написать id колонки,
  но кит id колонок нигде не печатает. `column_list` (yougile.py:506, `return ", ".join(c.get("title") or "?" for c in columns) or "none"`)
  и `transition` без цели выводят только заголовки. Совет нельзя выполнить средствами кита.
  В ветке exit 11 он к тому же предлагает агенту «rename one of them», а такого действия у
  скилла нет. Для досок так сделано правильно: их id перечислены (yougile.py:396–398).
  Fix: в `column_list` печатать `title (id)` хотя бы для повторяющихся заголовков, а в ветке
  exit 11 убрать «rename one of them». Passes: 3/3.

### 4. Независимая проверка

Не применимо: потоков нет.

### 5. Противоречия

- **F5.5** [low] `BLUEPRINT.md:90`
  > `  the id). Optional: `statuses` (a word process kits use -> a column title of the board;`
  Скрипт теперь принимает в `statuses` и id колонки (yougile.py:414, `c.get("id") in (target, title)`),
  и SKILL.md:104 так и говорит. R6 и R3:42 («a column title or a word of `statuses`»)
  по-прежнему называют только заголовок. Автор сам указал на это в заметке для супервизора.
  Fix: в R6 «a column title of the board, or its id when titles repeat», в R3 добавить «or a
  column id». Passes: 2/3.

### 6. Дублирование

Новых повторов нет.

### 7. Когда звать человека

Путь после exit 5 теперь един во всех местах: README.md:79–82, SKILL.md:132, `STOP_ALL`
(yougile.py:57–58) и BLUEPRINT R11 — «sets a new key in `YOUGILE_API_KEY` and restarts the
session».

### 8. Циклы при повторном визите

Не применимо: потоков нет.

### 9. Краткость и «почему»

Новых находок нет.

### 10. Описания скиллов

Описание не менялось. `shlex` — стандартная библиотека, `expects` прежний.

### 11. Нейтральность к провайдеру

Команды README адресованы человеку и помечены «(zsh)», `security` — как вариант для macOS.

### 12. Безопасность и границы

- **F12.4** [medium] `README.md:40`
  > `read 'YG_LOGIN?Login: '; read -s 'YG_PASS?Password: '; echo`
  README.md:37 советует набирать `"` как `\"` и `\` как `\\` («JSON, so escape those characters
  as `\"` and `\\` when you type it»). Но `read` без `-r` убирает обратные слэши, и экранирование
  до JSON не доходит. Проверено в zsh: ввод `p\"w\\x` с `read -s` даёт `p"w\x`, и JSON не
  разбирается (`JSONDecodeError: Expecting ',' delimiter`); с `read -rs` получается `p\"w\\x`.
  Простой `\` в пароле молча пропадает. В обоих случаях Yougile отказывает без понятной
  причины: человек с таким паролем не сделает ключ по README.
  Fix: `read -r 'YG_LOGIN?Login: '; read -rs 'YG_PASS?Password: '; echo`. Passes: 3/3 (импакт: в
  двух проходах low, в одном medium; взят medium).

## Известные дыры

| Известная дыра | Находка или как кит с ней справляется |
|---|---|
| 1. Красная проверка без учёта окружения | Без изменений: SKILL.md:118–121 отделяет сбой `uv`/Python. |
| 2. Работа вне потока, merge без гейта | Без изменений: запись только по просьбе (SKILL.md:29–31). |
| 3. Путь вне worktree | Новых путей нет. |
| 4. Вердикт без порога | Не применимо. |
| 5. Зависимый скилл, пишущий где нельзя | Не применимо. |
| 6. Команды вне `expects.commands` | Без изменений: `uv`; `read`, `printf`, `curl`, `security` нужны только для разовой настройки человеком. |

## Не прослежено

Новых элементов нет, жёлтых и красных мер нет, скелетов нет. Блюпринт расходится с китом в
одном факте: id колонки в `statuses` (F5.5). Решение хранить ключ в `YOUGILE_API_KEY` в
профиле, а keychain сделать необязательным, принял человек; оно записано в R7 с цитатой.

## Прошлые находки

| Id | Статус | Доказательство |
|---|---|---|
| F5.1 (блюпринт отстал) | RESOLVED | R3:53–57 «when it is in that state», R6:87 «no lists», R11:130 «stores it as the README says», R12:148–152 (итоги пробы), раздел 2:172, таблица:187 «where the format … is (SKILL.md)». Новый остаток — F5.5 |
| F5.2 (`get` прячет все метки) | RESOLVED | yougile.py:766 `resolved = _resolvable(_stickers(api, config), config, config["labels"])` |
| F5.3 (ключ «в профиль» против keychain) | RESOLVED | yougile.py:58 «key in YOUGILE_API_KEY and restarts the session»; README:50 по решению человека кладёт ключ в профиль |
| F5.4 (неоднозначная колонка в `statuses`) | RESOLVED | yougile.py:414 `match = [c for c in columns if c.get("id") in (target, title)]`; тест `test_statuses_column_by_id_and_ambiguous_title`. Остаток — F3.1 |
| F12.1 (пароль в argv `curl`) | RESOLVED | README:42, :45: `printf … | curl … -d @-` (`printf` встроенная). Новый изъян — F12.4 |
| F12.2 (`security` без `-U`) | RESOLVED | README:61 `security add-generic-password -U -s yougile -a "$USER" -w   # paste the key` |
| F12.3 (кавычки в `search --text`) | RESOLVED | yougile.py:808 `% shlex.quote(args.title))` |
| M5.1 («write [a, b]») | RESOLVED | yougile.py:105 `NO_LISTS = "lists are not supported: every value is one plain value"`, используется на :111 и :131 |

## Вырезанные правила

| Удалённое правило (файл:строка в 0a75b2c) | Где оно теперь |
|---|---|
| README: «Keep the key in the OS keychain, not in the profile» | Отменено человеком (цитата в R7, BLUEPRINT:103–106); README:50–58 |
| README: «never put on a command line» | README:35–36 (stdin, не попадает в `ps`) |
| README: `security … -w   # once` | README:61 с `-U` |
| README: «put it in the keychain, and restart the session» | README:80–82 |
| BLUEPRINT R6: «inline `[a, b]` lists» | Убрано намеренно (M5.1): R6:87 «no lists», `NO_LISTS` |
| BLUEPRINT R7: keychain и «Always Allow» | Keychain необязателен по решению человека; правило «Always Allow» в README:66–68 |
| BLUEPRINT R11: «until the human fixes the key» | R11:130–131, SKILL.md:132, `STOP_ALL` |
| BLUEPRINT R12: «until then the script relies only on what the API documents» | Заменено итогами пробы, R12:148–152 |
| yougile.py: разбор inline-списков, «write [a, b]» | Убрано намеренно, `NO_LISTS` |
| yougile.py: `cmd_get` «Labels: not shown, <причина>» | Заменено пропуском устаревших слов, как в `label` (намеренно, прошлая F5.2). Об устаревшем слове теперь сообщает только `label`, если это слово названо (exit 3) |
| yougile.py: «is ambiguous» | yougile.py:418, с советом (F3.1) |

Ни одно правило не потеряно.

## Пропущено ранее

Нет.

## Вопросы человеку

1. F12.4 (`read -rs`) — правка в одну строку README. Релиз она не блокирует, но без неё
   человек с `"` или `\` в пароле не создаст ключ. Рекомендую поправить до тега вместе с F3.1
   и F5.5, иначе записать в BACKLOG.

## Найдено по пути

- `[kit-builder]` `kit-budget/scripts/flow_diagram.py` на ките без `flows/` падает с ошибкой
  `error: kit.yaml: states must be a non-empty mapping` (exit 2), а ожидался ответ «0 потоков,
  различий нет» с кодом 0.
