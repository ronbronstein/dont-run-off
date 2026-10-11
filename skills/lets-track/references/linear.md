# Linear

Tasks are Linear issues, through Linear's connector (an MCP server). The store is remote and shared. It needs the connector and a Linear login.

## Before the first call

Look in your tool list for Linear tools (their names contain `linear`). When there are none, tell the user that the Linear connector is not connected, and point them to Linear's MCP page (linear.app/docs/mcp) to add it. Do not guess tool names, and do not use the Linear API with a key that the user pasted into the chat.

My setup or `TASKS.md` names the team (for example "team ENG"). When it does not, list the teams and ask once.

## The stable ID: the issue key

An issue key (`ENG-123`) never changes. Cite it with the title.

## The seven steps

Map each step to the connector's tools: read their descriptions first, because names and fields change between versions.

| Step | What to do |
|---|---|
| next | Issues assigned to the user in the team, state "Todo" or the team's "next" view; else ask |
| list | Open issues of the team (or of the project that `TASKS.md` names) |
| add | Create an issue in the team, with a title and one or two lines of context |
| start | Set the state to "In Progress"; add a comment with the branch |
| note | Add a comment |
| park | Set the state the team uses for paused work (often "Backlog" or "Blocked"), and add a comment with the reason |
| done | Set the state to "Done", with a comment on what was done |

State names differ per team: read the team's states before you set one.

## Connect a repo

Write `TASKS.md`: "Tool: Linear, team `<KEY>`" (and the project, if any).
