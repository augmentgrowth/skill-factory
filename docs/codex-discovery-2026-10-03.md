# Codex skill discovery verification — 2026-10-03

Tested the installed Codex CLI 0.154.0 on macOS through a real `codex app-server --stdio` process. After `initialize`, requested `skills/list` with `forceReload: true` at a temporary repository root and its nested folder. Each candidate location held a uniquely named, valid temporary SKILL.md; the response returned the actual loaded path and scope. All probes were removed afterward.

| Location | Root working directory | Nested working directory |
|---|---|---|
| Repository `.agents/skills` | loaded, repo scope | loaded, repo scope |
| Nested `.agents/skills` | absent | loaded, repo scope |
| Sibling `.agents/skills` | absent | absent |
| Ancestor above repository `.agents/skills` | absent | absent |
| Repository `.claude/skills` | absent | absent |
| Personal `~/.agents/skills` | loaded, user scope | loaded, user scope |
| Personal `~/.codex/skills` | loaded, user scope | loaded, user scope |

Both responses exactly matched the expected probe names, with no discovery errors. This verifies the running loader, not merely documentation or a model's recollection. No model execution or network request is needed for this scan. It does not establish symlink behavior, duplicate-name precedence, hot reload, or discovery in other versions/harnesses. The existing authoring and execution notes retain their older test dates where not re-tested.
