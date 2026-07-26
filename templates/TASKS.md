# Tasks — <project name>

**Namespace:** `<area>.<slug>`

Scope every command explicitly:

```bash
task project:<area>.<slug> +next next
```

## Local tags

| Tag | Means |
|---|---|
| `+next` | Queued to do now |
| `+blocked` | Can't proceed |
| `+waiting` | Waiting on someone else |
| `+backlog` | Deferred |
