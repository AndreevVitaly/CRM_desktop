# Excel templates

`encounters.xlsx` is the editable template for exporting patient meetings.

Supported placeholders:

```text
{{ title }}
{{ patient.callsign }}
{{ patient.personal_number }}
```

The first row that contains `{{ row.* }}` is used as the data row template.
PULSAR copies that row's formatting for every exported meeting.

Row placeholders:

```text
{{ row.date }}
{{ row.patient }}
{{ row.personal_number }}
{{ row.doctor }}
{{ row.result }}
{{ row.reason }}
{{ row.status }}
{{ row.patient_info }}
{{ row.document_number }}
{{ row.notes }}
```
