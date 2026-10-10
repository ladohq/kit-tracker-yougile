# Отчёт о ките: tracker-yougile 0.1.0

- Дата: 2026-10-10
- Кит: корень worktree рана `create/tracker-yougile` (путь, данный задачей)
- Коммит: `0a75b2c`
- Оценил: критик kit-builder (слои a и b)
- Режим: повторная оценка относительно прошлой версии этого отчёта (коммит `021c2e6`, отчёт в
  `29c4123`), `git diff 021c2e6 -- kit.yaml README.md BLUEPRINT.md agents flows skills`
- Проходы: три независимых суб-агента, у каждого рубрика, `lado-kit-format`, папка кита, diff
  и прошлый отчёт. Старт: (1) SKILL.md, затем yougile.py; (2) изменённые функции yougile.py
  против R3/R4/R6/R11; (3) README/kit.yaml, BLUEPRINT, проверка вырезанных правил. Я отбросил
  2 находки одного прохода и оставил 3 как подтверждённые. Полный проход не нужен: в `create`
  весь текст новый, и первая оценка уже была полной.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 (потоков нет, R2); в BLUEPRINT.md нет скелетов |
| b. Рубрика | 8 находок (0 high, 1 medium, 7 low), плюс 1 под «Пропущено ранее»; 9 из 12 критериев без находок |
| Охват | повторная оценка изменённого текста (kit.yaml, README.md, BLUEPRINT.md, SKILL.md, yougile.py) и его окружения, без полного прохода (`create`) |
| Правило остановки | не выполнено: 0 high, 1 medium (F12.2). Это совет к гейту релиза, а не блок |

Число находок относится только к тому, что названо в строке «Охват». Его нельзя сравнивать с 11
находками полной оценки.

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

У кита нет потоков (R2), в BLUEPRINT.md нет скелетов, поэтому диаграмм нет. Скрипт потоков
на таком ките падает (см. «Найдено по пути»):

```
$ flow_diagram.py . --compare BLUEPRINT.md
error: kit.yaml: states must be a non-empty mapping   (exit 2)
```

Тесты (не текст кита, для сведения): `python -B -m unittest discover -s tests` — `Ran 62 tests`, `OK`.
Проба на облачной доске polygon (артефакт `trial`) прошла для всех 9 действий на скрипте
`d989e40`. После него `0a75b2c` менял только README.

## Исправить в первую очередь

1. README:53: `security add-generic-password` без `-U`, поэтому замена отозванного ключа по
   README падает (F12.2).
2. README:35: пароль попадает в argv `curl`, а фраза утверждает обратное (F12.1).
3. BLUEPRINT R3/R6/R11/R12, раздел 2 и таблица трассировки отстали от исправлений (F5.1).
4. yougile.py:815: заголовок в совете `search --text` не экранирован (F12.3).
5. yougile.py:770: `get` прячет все метки из-за одной устаревшей (F5.2).

## Находки

### 1. Границы ролей

Не применимо: ролей нет. Права записи не менялись (SKILL.md:29–31).

### 2. Передача между шагами

Не применимо: потоков нет.

### 3. Готовность и исходы

Строки 3, 5 и 7 таблицы кодов совпадают с новыми путями скрипта. Проба подтвердила exit 3, 4,
5 и 7. SKILL.md:134: «task not found, or not on the project's board».

### 4. Независимая проверка

Не применимо: потоков нет. Проба R12 на облаке проведена, её итог есть в README.md:14–17 и в
артефакте `trial`.

### 5. Противоречия

- **F5.1** [low] `BLUEPRINT.md:53`
  > `    sticker state (R6); add sets that state, remove takes the sticker off the task; other`
  Исправления изменили SKILL.md и скрипт, но не блюпринт, и копии уже расходятся:
  - R3:53 и SKILL.md:74–75 («when it is in that state»);
  - R6:85 («inline `[a, b]` lists») и SKILL.md:100, где списки убраны;
  - R11:125 («until the human fixes the key») и `STOP_ALL`;
  - R12:142 («until then the script relies only on what the API documents») и новый R4,
    который опирается на факт пробы;
  - раздел 2:162 («the key is `idTaskProject` found on the board (R4)»);
  - таблица трассировки:177 (README «how to write `.lado/tracker.yaml`»), хотя README теперь
    только ссылается на SKILL.md.

  Следующий автор или критик сверит кит с устаревшими требованиями.
  Fix: обновить R3, R6, R11, R12, раздел 2 и строку README в разделе 3. Passes: 3/3 (каждый проход
  нашёл часть мест; объединено).

- **F5.2** [low] `skills/tracker/yougile.py:770`
  > `            resolved = {w: _resolve_label(stickers, config, w) for w in config["labels"]}`
  Исправление F5.1 прошлого отчёта сделало `label` терпимым к устаревшим словам (`_resolvable`,
  :913), а `get` в той же изменённой функции по-прежнему строгий. Одно устаревшее слово, и
  выводится «Labels: not shown»: агент не видит через `get` свою метку, хотя `label` её покажет.
  Fix: в `cmd_get` использовать `_resolvable(stickers, config, config["labels"])`. Passes: 2/3.

- **F5.3** [low] `skills/tracker/yougile.py:57`
  > `            "new key in the login shell's profile and restarts the session")`
  `STOP_ALL` (и строка 5 SKILL.md:132, «puts a new key in the profile») говорят человеку
  положить ключ в профиль. README.md:49 говорит обратное: «Keep the key in the OS keychain,
  not in the profile», а README.md:72 — «put it in the keychain». Человек, получивший строку от
  лида, может записать ключ в профиль открытым текстом.
  Fix: «until the human makes a new key, stores it as the README says and restarts the session».
  Passes: 1/3, confirmed (обе цитаты README.md:49 и :72 на месте).

- **F5.4** [low] `skills/tracker/yougile.py:424`
  > `                raise Failure(CONFIG, "'statuses.%s: %s' in %s %s; its columns: %s; the "`
  Если привязанный заголовок неоднозначен (две колонки с одним названием), новое сообщение
  велит «the user fixes the file». Но в файле это не исправить: id колонки в значении
  `statuses` не принимается, потому что строка 418 сравнивает id со словом, а не со значением
  (`match = [c for c in columns if c.get("id") == target]`). Заглушка с
  `statuses: {review: c2}` дала exit 3 «… is not a column of the board».
  Fix: сравнивать id и с `title` (`c.get("id") in (target, title)`), или для неоднозначного
  случая писать «rename one of the columns». Passes: 1/3, confirmed (вывод заглушки, строка 418).

### 6. Дублирование

Пример настроек теперь только в SKILL.md:102–110, README.md:80–81 на него ссылается.
Расхождения блюпринта собраны в F5.1.

### 7. Когда звать человека

Пути к человеку не менялись (SKILL.md:122–123). Восстановление после exit 5 ведёт к F12.2.

### 8. Циклы при повторном визите

Не применимо: потоков нет.

### 9. Краткость и «почему»

Новых находок нет. Несколько переносов стали длинными (SKILL.md:75, 121, 144; kit.yaml:4), но
это косметика без влияния на поведение.

### 10. Описания скиллов

Описание не менялось, check без предупреждений.

### 11. Нейтральность к провайдеру

Новых путей и имён CLI нет. Синтаксис `read 'VAR?prompt'` в README работает только в zsh, но
помечен «(zsh)».

### 12. Безопасность и границы

- **F12.2** [medium] `README.md:53`
  > `security add-generic-password -s yougile -a "$USER" -w   # once; paste the key`
  Новый README.md:72 после exit 5 велит «make a new one, put it in the keychain, and restart the
  session». Единственная показанная команда без `-U` падает, потому что запись уже есть:
  `security add-generic-password -h` пишет «-U  Update item if it already exists (if omitted,
  the item cannot already exist)». Если человек пропустит ошибку, останется старый ключ, после
  перезапуска снова будет exit 5, и все агенты снова остановятся.
  Fix: `security add-generic-password -U -s yougile -a "$USER" -w`, а в README.md:72 сказать
  «run that line again with the new key». Passes: 3/3 (импакт: в двух проходах low, в одном
  medium; взят medium).

- **F12.1** [low] `README.md:35`
  > `read without echo and never put on a command line, so it stays out of the shell's history`
  В историю пароль действительно не попадает. Но README.md:42 и :45 раскрывают `$YG_PASS` в
  argv `curl`, где его видно в `ps`, пока curl работает, так что «never put on a command line»
  неверно. Пароль с `"` или `\` ломает JSON, и Yougile отказывает без понятной причины.
  Fix: `printf '{"login":"%s","password":"%s"}' "$YG_LOGIN" "$YG_PASS" | curl … -d @-`
  (`printf` — встроенная команда) и оговорка про `"`/`\`, либо убрать слова «never put on a
  command line». Passes: 3/3.

- **F12.3** [low] `skills/tracker/yougile.py:815`
  > `            "look for it with search --text '%s' before running create again" % args.title)`
  Заголовок подставляется в одинарные кавычки без экранирования. Заглушка с `--title "Don't
  crash"` напечатала `search --text 'Don't crash'`: такую команду шелл не выполнит, и агент может
  пропустить проверку на дубликат или исказить её.
  Fix: `shlex.quote(args.title)` без своих кавычек. Passes: 2/3.

## Известные дыры

| Известная дыра | Находка или как кит с ней справляется |
|---|---|
| 1. Красная проверка без учёта окружения | Потоков нет. SKILL.md:118–121 отделяет сбой `uv`/Python: «so nothing reached Yougile … report all of it (nothing was sent)». |
| 2. Работа вне потока, merge без гейта | Потоков нет. Запись только по просьбе (SKILL.md:29–31). |
| 3. Путь вне worktree | Нет: настройки ищутся до первого `.git`, файлы кита доступны через `${SKILL_DIR}`. |
| 4. Вердикт без порога | Не применимо: ревьюеров нет. |
| 5. Зависимый скилл, пишущий где нельзя | Не применимо: `dependencies.skills` нет. |
| 6. Команды вне `expects.commands` | В порядке: `uv` объявлен. `read`, `curl`, `security` нужны только для разовой настройки ключа человеком. |

## Не прослежено

Все элементы кита названы в таблице трассировки. Жёлтых и красных мер нет. Скелетов потоков
нет, различий тоже. Текст блюпринта отстал от кита в R3, R6, R11, R12, разделе 2 и строке
README таблицы (F5.1): это не новые элементы, а неисправленные описания. Изменение R4 (0152a25)
имеет источник: решение человека на гейте релиза.

## Прошлые находки

| Id | Статус | Доказательство |
|---|---|---|
| F3.1 | RESOLVED | `_on_board` удалён; yougile.py:445–446 даёт `NOT_FOUND`, если колонки задачи нет на доске; SKILL.md:134 «task not found, or not on the project's board» |
| F5.1 | RESOLVED | yougile.py:911 `named = {w: _resolve_label(stickers, config, w) for w in add + remove}`, прочие слова через `_resolvable` (:913); проверено в пробе |
| F5.2 | RESOLVED | yougile.py:423–426 даёт `CONFIG` для слова `statuses`; SKILL.md:130; в пробе exit 3 |
| F5.3 | RESOLVED | SKILL.md:74–75 «takes the sticker off when it is in that state» (блюпринт не обновлён: F5.1) |
| F6.1 | RESOLVED | README.md:80–81 ссылается на SKILL.md «Project settings», пример только там |
| F7.1 | RESOLVED | SKILL.md:132, `STOP_ALL`, README.md:72–73 называют перезапуск (новые изъяны этого места в F5.3 и F12.2) |
| F9.1 | RESOLVED | README.md:14–17 даёт дату и итог пробы; kit.yaml:4 «tried on the cloud, self-hosted untried» |
| F9.2 | RESOLVED | SKILL.md:121 «report all of it (nothing was sent)» |
| F9.3 | RESOLVED | SKILL.md:100 без `[a, b]` (подсказка скрипта осталась: «Пропущено ранее» M5.1) |
| F12.1 | RESOLVED | yougile.py:809–816 заменяет совет и для exit 9, и для 5xx; SKILL.md:142–144 (кавычки: F12.3) |
| F12.2 | RESOLVED | yougile.py:956–957 строит `<a href>` сам; в пробе URL с `_draft_` остался целым |
| (супервизор) пароль и ключ в истории shell | RESOLVED | README.md:39 `read -s`, :46 `unset YG_PASS`, :53 `-w` без значения (остаток про `ps`: F12.1) |

## Вырезанные правила

| Удалённое правило (файл:строка в 021c2e6) | Где оно теперь |
|---|---|
| README: пример `.lado/tracker.yaml` | SKILL.md:102–110 слово в слово; README.md:78–81 — краткое изложение и ссылка |
| README: «The format, a strict subset of YAML, is in …» | README.md:80–81 |
| README: «make a new one.» | README.md:72–73, расширено |
| README: «(… or a company's self-hosted Yougile)», kit.yaml «cloud or self-hosted» | README.md:3, :16–17; kit.yaml:4 |
| BLUEPRINT R4: «a key not on the board is "not found" (exit 7)» | BLUEPRINT.md:72–73 |
| SKILL.md: «by the key … or by its id» | SKILL.md:35–37 |
| SKILL.md: «`--remove` takes the sticker off» | SKILL.md:74–75, уточнено |
| SKILL.md: «`[a, b]` lists» | убрано намеренно (прошлая F9.3) |
| SKILL.md: «report all of it as exit 1» | SKILL.md:121 «(nothing was sent)», намеренно (прошлая F9.2) |
| yougile.py: `_on_board` (exit 11) | `Yougile.task`, exit 7; SKILL.md:36–37, :134 |
| yougile.py: `get` по UUID без настроек | убрано намеренно (build-report, тест `test_get_needs_the_settings`); R4 требует проверку доски |

Ни одно правило не потеряно.

## Пропущено ранее

- **M5.1** [low] `skills/tracker/yougile.py:135`
  > `            raise ValueError(where + "block lists are not supported; write [a, b]")`
  Подсказка предлагает список, но `_validate` отвергает список в любом ключе («must be one plain
  value»), так что пользователь, последовавший ей, получит вторую ошибку.
  Fix: «lists are not supported: every value is one plain value». Passes: 1/3, confirmed
  (yougile.py:182–184).

## Вопросы человеку

1. Medium F12.2 (`-U` в README) и низкие F12.1 и F12.3 правятся в одну-две строки. Релиз они не
   блокируют. Рекомендую поправить до тега, если будет ещё заход автора, иначе завести в
   BACKLOG.
2. Блюпринт (F5.1): обновить сейчас, чтобы следующий `improve` начинал со верного текста.
   Рекомендую да, вместе с п. 1.

## Найдено по пути

- `[kit-builder]` `kit-budget/scripts/flow_diagram.py` на ките без `flows/` (и с `--out`, и с
  `--compare`) падает с ошибкой `error: kit.yaml: states must be a non-empty mapping` (exit 2).
  Для кита-скилла ожидался ответ «0 потоков, различий нет» с кодом 0.
