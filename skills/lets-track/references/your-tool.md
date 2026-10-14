# Your tool: write a guide with the user

For a task tool that has no guide here (Notion, Asana, Trello, ClickUp, Things, a team's own system). Write a short guide together with the user, once, and save it where every later session finds it.

## 1. Ask, one question at a time

1. **The tool's name**, and a link to its docs for agents or its API.
2. **How to reach it from here:** a connector (MCP) that is already connected, a command on this machine, or an API. A key or token stays in the user's own environment or settings: never write it into the guide, and never ask them to paste it into the chat.
3. **Where this project's tasks live** in it: a board, a list, a database, a project.
4. **Its stable ID** for a task: a URL, a key, a number that never changes.
5. **How the seven steps map**: next, list, add, start, note, park, done. Read the docs or the connector's tool descriptions, and propose the map yourself; the user confirms it.

## 2. Try it

Run one read (list) with the user watching. Write nothing to their tool until they say yes.

## 3. Save the guide

Write it to `${CLAUDE_PLUGIN_DATA}/task-guides/<tool>.md`: the plugin's data folder, which plugin updates do not overwrite. Claude Code fills in that path only for a plugin install. If you see the text `${CLAUDE_PLUGIN_DATA}` itself (the skills were copied, for example with `npx skills`), write to `task-guides/<tool>.md` in the config folder (`$CLAUDE_CONFIG_DIR`, else `~/.claude`) instead. Use the shape of `references/github-issues.md`: before the first call, the stable ID, the seven steps, connect a repo. Then add the tool to My setup, with the full path of the guide, for example "Tasks: Asana, project 'Website' (guide: ~/.claude/plugins/data/dont-run-off-kidamti/task-guides/asana.md)".

Claude Code deletes the data folder when the user uninstalls the plugin. Tell the user, so a guide they want to keep can also live in their own notes.
