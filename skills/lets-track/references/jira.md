# Jira

Tasks are Jira issues, through Atlassian's connector (an MCP server) or a Jira command-line tool that the user already has. The store is remote and shared. It needs a login.

## Before the first call

Look in your tool list for Jira or Atlassian tools. When there are none, check for a command-line tool the user names (for example `acli`). When there is neither, tell the user what is missing and stop. Do not use an API token that the user pasted into the chat.

My setup or `TASKS.md` names the Jira project key (for example `WEB`). When it does not, ask once.

## The stable ID: the issue key

An issue key (`WEB-42`) never changes. Cite it with the summary.

## The seven steps

Map each step to the connector's tools or the command: read their descriptions first.

| Step | What to do |
|---|---|
| next | Issues assigned to the user in the project, in the "To Do" status, highest priority first |
| list | Open issues of the project |
| add | Create an issue (type "Task" unless the project uses another), with a summary and a short description |
| start | Move it to "In Progress"; add a comment with the branch |
| note | Add a comment |
| park | Move it to the status the project uses for paused work, and comment with the reason |
| done | Move it to "Done" (the project's final status), with a comment |

Jira workflows differ per project: read the available transitions before you move an issue.

## Connect a repo

Write `TASKS.md`: "Tool: Jira, project `<KEY>`", and how to reach it (connector or command).
