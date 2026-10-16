# More checks

Go through these after the surfaces in step 3. Each one is a fault that a real setup had and that no built-in command shows. The aim is to find what misleads the user or the agent, so use judgment: a match that misleads nobody is not a finding.

`~/.claude.json`, `.mcp.json`, and settings files can hold keys and tokens. Read the names, commands, and paths that a check needs through a filter (for example `jq 'keys'`, or a short `node -e` script), so that values never enter the session, and never quote an `env`, `headers`, or key value.

Each check names its report group (step 4). Every fix waits for the user's yes.

## Broken links

Something points at a thing that is not there. It loads nothing and says nothing.

### A rule names a skill that does not exist
- **Look:** in every loaded `CLAUDE.md` and rules file, at the skills that it tells the agent to use: a moves list or table, "run `x`", "use the `x` skill", `/x`. Check each name against the installed skills (personal, project, plugin).
- **Why:** the agent reaches for a move that is gone, often one that a plugin renamed.
- **Fine:** a built-in command (`/context`, `/doctor`); a name in a quote or an example.
- **Fix:** correct the name, or install the skill. **Group:** Never fires.

### A rule names a record file that does not exist
- **Look:** at the record files that a `CLAUDE.md` or the My setup block names (status file, decision log, tasks file). Check that each one exists where the rule says.
- **Why:** the next session expects the record and starts blind.
- **Fine:** a file that My setup marks "none".
- **Fix:** create the file, or correct the name. **Group:** Never fires.

### A folder map that is out of date
- **Look:** for a file that maps the user's folders with paths (a charter, a registry, a README for a code folder). Compare its rows with the disk: rows for folders that are gone, and real folders with no row. When it calls a scheduled job live, check that the job runs (`launchctl list` on macOS, `crontab -l`).
- **Why:** an agent that reads a wrong map acts on folders and jobs that do not exist.
- **Fine:** a row that the map marks as archived or planned.
- **Fix:** update the map. **Group:** Contradictions.

### An MCP switch with no server, or every project server approved
- **Look:** at `enabledMcpjsonServers` in each settings file: each name needs a server in the project's `.mcp.json`. Then at `enableAllProjectMcpServers`.
- **Why:** a name with no server is a switch for nothing. `enableAllProjectMcpServers: true` removes the prompt that stops a server that someone adds to `.mcp.json` later.
- **Fine:** names that match the servers in `.mcp.json`.
- **Fix:** delete the dead name (Dead weight). Remove the auto-approve, or set it to `false` (Risks).

### An MCP command with a path into a version manager
- **Look:** at each MCP server's `command`: a full path inside a version manager's folder (`.nvm/versions/node/v…`, `mise/installs/…`, `.pyenv/versions/…`, `.asdf/installs/…`).
- **Why:** the next runtime upgrade moves the program. The server then fails to start, and the session shows only a failed server.
- **Fine:** `npx -y <package>`, or a stable path such as `/opt/homebrew/bin/…`.
- **Fix:** start it with `npx -y <package>` or a stable shim. **Group:** Risks.

### Config that the config git does not track
- **Look:** when the config folder is a git repo, at `git -C <config folder> status --porcelain`: untracked skill, command, or agent folders, and changed tracked files. When it is not a git repo, say so once, as information.
- **Why:** work that is not committed is in no history and in no backup: a skill can exist on one machine only.
- **Fine:** a clean tree. Some tools rewrite `settings.json` at each start, so a changed `settings.json` alone is a question, not a fault.
- **Fix:** commit it, or move it to the repo or plugin that owns it. **Group:** Risks.

## Leftovers

Something from an old install, or a removed tool, is still on disk or in a settings file. It costs little today, but it misleads the next reader, and some of it comes back to life.

### A `skillOverrides` entry for a skill that does not exist
- **Look:** at each key in `skillOverrides` (user, project, and local settings). Check it against the installed skills: personal, project, and plugin (`plugin:skill`).
- **Why:** a dead switch hides nothing, but it applies again, without a word, if a skill with that name comes back.
- **Fine:** a key for an installed skill.
- **Fix:** delete the entry; ask first, because the user may plan to bring the skill back. **Group:** Dead weight.

### A third-party skill with no source
- **Look:** for a skill that is not the user's own (a license file, an author or vendor in its frontmatter, a vendor path) and has no record of where it came from: no entry in a lock file (`skills-lock.json`, `~/.agents/.skill-lock.json`) and no source and version in its frontmatter. Note a copy of a skill that an installed plugin also ships.
- **Why:** a copy with no source never updates, and nobody can check what changed in it.
- **Fine:** the user's own skills; a skill with a lock entry.
- **Fix:** record the source and the version, or install the plugin instead. Teach the trade-off: a plugin from a marketplace that updates by itself changes with no review. **Group:** Risks.

### A skills lock entry with no skill folder
- **Look:** at each entry in `~/.agents/.skill-lock.json` and in a repo's `skills-lock.json`: its skill folder must exist.
- **Why:** the lock and the disk disagree, and the next update can bring back a skill that the user removed.
- **Fine:** an entry whose folder exists.
- **Fix:** `npx skills remove -g <name>`, or install it again. **Group:** Dead weight.

### Project entries in `~/.claude.json` for folders that are gone
- **Look:** at the paths under `projects` in `~/.claude.json` that hold `mcpServers`: each path must still exist. Read the paths and the server names only.
- **Why:** dead MCP config. It comes back to life when a folder is made at that path again.
- **Fine:** an entry whose folder exists.
- **Fix:** remove the entry. The file also holds account data, so the user makes the change, or you change only that entry after their yes. **Group:** Dead weight.

### Plugin leftovers
- **Look:** in the plugins folder (`installed_plugins.json`, `known_marketplaces.json`, `cache/`) and at `enabledPlugins` in each settings file: cache folders for a marketplace that is not known, `*.bak` marketplace folders, several cached versions of a plugin that is off, and an `enabledPlugins` key whose marketplace is not known.
- **Why:** old copies confuse which version runs, and a switch for an unknown marketplace never loads anything.
- **Fine:** one cached version of each enabled plugin, from a known marketplace.
- **Fix:** clean up with `claude plugin`. **Group:** Dead weight; an `enabledPlugins` key that never loads goes under Never fires.

### Permission rules with paths that are gone
- **Look:** at each `permissions.allow` and `permissions.deny` rule that holds a path: the path must exist.
- **Why:** dead rules grow with no end and hide the live ones.
- **Fine:** a rule whose path exists; a rule with no path, such as `Bash(git status)`.
- **Fix:** delete the dead rules. **Group:** Dead weight.
