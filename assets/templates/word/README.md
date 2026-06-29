# Word templates

Шаблоны Word лежат в этой папке и заполняются общим движком
`utils.word_export.render_word_template`.

## Плейсхолдеры

Обычные значения пишутся в формате:

```text
{{ patient.callsign }}
{{ encounter.started_at }}
{{ doctor.full_name }}
{{ document.location }}
```

Движок заменяет такие значения в абзацах и таблицах.

## Динамические блоки

Для таблиц и повторяющихся секций используется блок:

```text
{{ block:informants }}
```

Обработчик блока передается из Python-кода при вызове `render_word_template`.

## Текущие шаблоны

- `encounter.docx` - экспорт выбранной встречи категории АА.
- `plan_work.docx` - экспорт выбранного плана работы категории АА.
- `planning_year.docx` - экспорт годового набора мероприятий из раздела "Планирование".
