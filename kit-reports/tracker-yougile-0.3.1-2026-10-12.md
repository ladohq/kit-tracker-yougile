# Отчёт о ките: tracker-yougile 0.3.1

- Дата: 2026-10-12
- Кит: корень worktree рана `improve/tracker-yougile` (путь задан задачей)
- Коммит: `3894cf2` (визит 1 шага `evaluate`; blueprint `3868323`)
- Оценил: критик kit-builder (слои a и b)
- Режим: повторная оценка относительно `kit-reports/tracker-yougile-0.3.0-2026-10-12-assess.md`
  (полная оценка `4b24b3c`, база по плану), `git diff 4b24b3c -- kit.yaml README.md
  BLUEPRINT.md agents flows skills`. Изменение: 3 коммита — `3868323` (BLUEPRINT R3, R9,
  R10, R12, разделы 3–5), `2645c2b` и `3894cf2` (SKILL.md, README.md, kit.yaml, тест).
- Проходы: изменение маленькое (≈60 строк текста кита), три прохода критик сделал сам, без
  суб-агентов: (1) от плана и build-report к diff; (2) от нового пункта **A file in a
  task** к таблице кодов выхода, к `cmd_get` в yougile.py и к поведению `curl` (запуск
  `curl -sL` на закрытый порт: вывода нет, только код 7); (3) от BLUEPRINT R3, R9, R10, R12
  к SKILL.md и README. Затем проверка вырезанного (`--word-diff`) и полный проход по
  SKILL.md, README.md, kit.yaml и BLUEPRINT.md целиком. Находок одного прохода: 2,
  обе оставлены как подтверждённые (F3.1, F5.2); отброшенных нет.

Находки — кандидаты для человека, а не оценка «сдал / не сдал».

## Карточка

| Слой | Результат |
|---|---|
| a. `lado kits check` | OK; 0 предупреждений |
| a. Бюджет | зелёный; жёлтых и красных мер нет |
| a. Потоки | 0 нарисовано (потоков нет, R2); скелетов в BLUEPRINT.md нет («Flow skeletons: none») |
| b. Рубрика | 3 находки (0 high, 1 medium, 2 low); F12.1, F5.1, F5.2 оценки — RESOLVED; 10 из 12 критериев без находок |
| Охват | повторная оценка изменённого текста, с полным проходом по 4 файлам из diff (kit.yaml, README.md, BLUEPRINT.md, skills/tracker/SKILL.md) |
| Правило остановки | не выполнено: 0 high, 1 medium (F5.1) — совет для гейта выпуска, не блок |

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
# Complexity budget: tracker-yougile 0.3.1

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

Тесты: `uv run --no-project python -m unittest discover -s tests` — `Ran 107 tests`, `OK`.

## Вердикт

`approved`: `lado kits check` без ошибок, бюджет зелёный, `--compare` без расхождений,
high-находок нет. Все три находки оценки исправлены. Осталась одна medium (F5.1) и две
low, они не блокируют выпуск. Правило остановки не выполнено из-за F5.1: её стоит
исправить до выпуска одной фразой, решать человеку на гейте.

## Исправить в первую очередь

1. SKILL.md:107: тайм-аут скачивания не равен exit 9 — API работает, трекером
   пользоваться дальше (F5.1).
2. SKILL.md:104: `curl -fsSL` вместо `curl -sL` (F3.1).
3. SKILL.md:101–103: про файл в комментарии не утверждать, что `get` покажет `[name](url)`
   (F5.2).

## Находки

### 1. Границы ролей

Не применимо: ролей нет. Новое правило ограничено: «Download no other link of a task's
text by this / rule.» (SKILL.md:106–107).

### 2. Передача между шагами

Не применимо: потоков нет (R2).

### 3. Готовность и исходы

- **F3.1** [low] `skills/tracker/SKILL.md:104`
  > `curl -sL '<url>' -o <a temporary folder outside the repository>/<name>`, then open it

  Без `-f` curl на ответ 404/403/5xx выходит с кодом 0 и сохраняет страницу ошибки под
  именем картинки. `-s` к тому же прячет текст ошибки curl: на закрытый порт
  `curl -sL 'http://127.0.0.1:9/x.png?previews[]=…'` ничего не печатает, только `exit=7`.
  Агент видит «скачано», не может открыть файл и гадает, в чём дело.
  Fix: `curl -fsSL '<url>' -o …`: ошибка HTTP даёт ненулевой код, а `-S` печатает её строку.
  Passes: 1/3, confirmed (вывод запуска выше; `-f` в `man curl`: «Fail fast with no
  output at all on server errors»).

### 4. Независимая проверка

Не применимо: потоков нет. Изменение проверено тестом на HTML из облака
(`test_get_shows_an_image_as_a_link`, проходит) и пробой скачивания (LAD-24, README.md:19–20).

### 5. Противоречия

- **F5.1** [medium] `skills/tracker/SKILL.md:107`
  > rule. A time-out is the network or VPN: report it as exit 9.

  и SKILL.md:184
  > | 9 | Yougile not reachable or did not answer | report it (network or VPN?) and send Yougile nothing more until you are told it answers again |

  «Report it as exit 9» отсылает агента к строке exit 9, а там — не слать Yougile больше
  ничего. Тайм-аут хранилища файлов (`user-data.yougile.com`, отдельный адрес, у человека
  за VPN не открывался, пока его не добавили в split) не значит, что API недоступен. Агент
  перестаёт пользоваться трекером, хотя тот работает, и ждёт ответа, которого шаг мог бы
  не ждать. Это следует из моего совета в оценке («как exit 9»), сформулированного неточно.
  Fix: «A time-out is the network or VPN (`user-data.yougile.com` may need the VPN's
  split): report it as a failure (see "When the script fails"); the tracker's actions
  still work.» Passes: 3/3.

- **F5.2** [low] `skills/tracker/SKILL.md:101`
  > - **A file in a task** (e.g. a screenshot pasted into a description or a comment) is a

  и SKILL.md:103
  > `[name](url)`. To see it, download it without the API key (never send the key there):

  Для комментария обещан вид `[name](url)`, но `get` печатает обычный `text` сообщения без
  преобразования (yougile.py:1033–1034 `print("\n--- comment %s, %s, %s\n%s" % (stamp,
  api.person(message.get("fromUserId")),` … `when, message.get("text")))`). Исследование
  (LAD-24) и тест проверяли только описание. Как выглядит файл в `text` комментария, не
  проверено. Если там нет `[name](url)`, агент решит, что файла в комментарии нет.
  Fix: «in a description `get` shows it as `[name](url)`; in a comment, look for a
  `…/user-data/…` URL in its text», или проверить на облаке и записать в R12.
  Passes: 1/3, confirmed (цитата кода).

### 6. Дублирование

Правило файла одно, в **A file in a task**; описание `edit` и раздел «Writing in Yougile»
дают на него ссылку (SKILL.md:138 «see **A file in a task**»), а не повторяют. README
говорит только про доступ к сети (README.md:32–34). Похожих абзацев скрипт не нашёл.

### 7. Когда звать человека

Сбой скачивания идёт в «report», то есть через супервизора. Что делать дальше, путает
F5.1. Других решений человека изменение не вводит.

### 8. Циклы при повторном визите

Не применимо: потоков нет.

### 9. Краткость и «почему»

Причины названы: «without the API key (never send the key there)»; «The host need not be
`YOUGILE_URL`'s (`en.yougile.com` / redirects to `user-data.yougile.com`)»
(SKILL.md:103–106). Почему ключ не нужен (файлы отдаются без авторизации), записано в
BLUEPRINT R3, агенту это знать не обязательно.

### 10. Описания скиллов

description не меняли. Чтение файла — не новое действие (BLUEPRINT R3), так что десяти
действий в описании достаточно.

### 11. Нейтральность к провайдеру

«then open it / (an image as an image)» (SKILL.md:104–105) — действие, а не инструмент
конкретного CLI. `curl` — общая команда, не завязанная на провайдера.

### 12. Безопасность и границы

Ключ не уходит: «never send the key there» (SKILL.md:103). Файл кладётся вне
репозитория, поэтому в коммит не попадёт. Скачиваются только ссылки `…/user-data/…`
(SKILL.md:106–107). Действие только читает и не пишет в Yougile.

## Известные дыры

| Известная дыра | Находка, или как кит её закрывает |
|---|---|
| 1. Красная проверка без учёта причины в окружении | Тайм-аут скачивания назван сетью или VPN (SKILL.md:107), но отправлен в exit 9 — F5.1. README: «behind a VPN, add that / host to its split» (README.md:33–34). |
| 2. Работа вне потока, слияние без ворот | Не применимо: потоков и слияний нет. |
| 3. Путь вне worktree рана | Временная папка «outside the repository» (SKILL.md:104) — намеренно вне worktree, чтобы файл не попал в коммит. Только чтение, кита не касается. |
| 4. Вердикт без порога важности | Не применимо: рецензента нет. |
| 5. Зависимый скилл пишет или спрашивает там, где роли нельзя | Не применимо: зависимых скиллов нет. |
| 6. Команды не в ладу с `expects.commands` | `curl` нужен только для чтения файла и только когда он есть: «To read a file in a task (a screenshot), they also need … and `curl`» (README.md:32–33). README не требует его для каждого проекта, BLUEPRINT R3 объясняет, почему его нет в `expects` — пункт (a) не нарушен. `expects commands: uv`, предупреждения нет. |
| 7. Read-only роли не в ладу с тем, что делают | Не применимо: ролей нет. |

## Не прослежено

Чтение файла записано в R3, изображение-ссылка — в R9 и R10, тест и проба — в R12. README
теперь покрывает R3 и R12 (раздел 3, обратная проверка), 0.3.1 есть в журнале. Бюджет
зелёный, скелетов нет. Расхождений нет.

## Прошлые находки

- **F12.1** RESOLVED — SKILL.md:101–107, новый пункт **A file in a task** («download it
  without the API key (never send the key there)», временная папка вне репозитория,
  хост не привязан к `YOUGILE_URL`, другие ссылки не качаются); README.md:32–34 «they
  also need a network path to / `user-data.yougile.com`, where Yougile keeps files».
  Формулировка про тайм-аут — новая находка F5.1.
- **F5.1** (оценки) RESOLVED — SKILL.md:75 «`get` shows images as links `[name](url)`»,
  SKILL.md:138 «an image as a link `[name](url)`: see **A file in a task**»; BLUEPRINT
  R9; тест `test_get_shows_an_image_as_a_link` на HTML LAD-24 проходит.
- **F5.2** (оценки) RESOLVED — README.md:17–20: проба `link` на «polygon» и скачивание
  картинки (LAD-24).
- Версия: kit.yaml `version: 0.3.1` — сделано. Список build-report «fixed» совпадает с diff.

## Вырезанные правила

| Удалённое правило (файл:строка в базе) | Где оно теперь |
|---|---|
| SKILL.md:75 «`get` shows images as their URLs» | SKILL.md:75, как ссылки `[name](url)` (исправленный факт) |
| SKILL.md:131 «an image as its URL» | SKILL.md:138, как ссылка, со ссылкой на правило |
| BLUEPRINT R3 «Nothing else (no … files)» (BLUEPRINT.md:107–108) | BLUEPRINT.md:107–108 «no … file uploads» и абзац о чтении файла: запрет действий с файлами остался, разрешено только чтение по решению человека |
| BLUEPRINT R9 «an image shows as its URL», R10 «images become URLs» | R9 и R10, «link» |
| README «and a network path to Yougile.» | README.md:31–34, дополнено |

Без потерь.

## Пропущено ранее

Нет: полный проход по четырём файлам из diff новых находок вне изменения не дал.

## Left by the plan

Нет (план: «Leave: none»).

## Вопросы человеку

1. Исправить F5.1 (и попутно F3.1, F5.2) до выпуска? Рекомендация: да, это одна-две фразы
   в SKILL.md:101–107. Блоком для выпуска это не является.
