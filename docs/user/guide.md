# Focus Mode On — User Guide

Focus Mode On keeps your tasks in plain Markdown files and lets you drive
them from a browser, either by clicking or by typing in plain English.

## Getting in

1. Open the app URL (locally, <http://127.0.0.1:8000>).
2. Enter your password. After five wrong tries you are paused for a few
   minutes.

## The dashboard

The dashboard has two areas, **WORK** and **PERSONAL**. Each shows the active
*threads* inside it as cards, with an icon, the thread name, and how many
tasks are still pending.

- Click a card to open its thread.
- Use the **theme** button (top right) to switch between light and dark; your
  choice is remembered.

## Working inside a thread

A thread shows, in order: a breadcrumb back to the dashboard, any sub-threads,
a description, and the task tree. Completed tasks are listed above pending ones
at every level.

- **Toggle a task**: click it (or select it and press <kbd>Space</kbd>).
  Completing a task stamps today's date.
- **Add a task**: type in the box at the bottom and press <kbd>Enter</kbd>.
- **Add a subtask**: hover a task and click the **＋** on its row (or select
  the task and press <kbd>s</kbd>), then type the subtask and press
  <kbd>Enter</kbd>. Subtasks can have their own subtasks, with no limit on
  depth.
- **Collapse / expand**: any task with subtasks shows a caret; click it, or
  select the task and press <kbd>←</kbd> to collapse and <kbd>→</kbd> to
  expand. The number badge on a row shows how many direct subtasks it has.
- **Complete a thread**: press the *Complete & archive* button. The thread
  moves to the archive.

### Deep hierarchy

Two things nest without limit: **threads** (a project inside an initiative
inside WORK, as deep as you like) and **tasks** (a subtask inside a subtask).
The breadcrumb shows where you are in the thread hierarchy; indentation and the
guide line show the task hierarchy. Everything is still a plain Markdown file —
subtasks are just indented checklist items you can read and edit anywhere.

## The command bar

The box at the top of the dashboard understands plain language. Examples:

- "start a new work project called Migration" — creates a thread.
- "finished the supplier call in landing page" — completes a matching task.
- "email the accountant" — adds a task.

If the app is only fairly sure about an action, it asks you to confirm with a
single click before applying it. With an OpenAI key configured the
understanding is sharper; without one, a simpler built-in parser is used and
everything still works.

## The archive

Open **Archive** from the header to see completed threads. Press **Restore**
to move any of them back to its original place.

## Keyboard shortcuts

You can run the whole app without a mouse:

| Key | Action |
| --- | --- |
| `j` / `k` | Move down / up between cards and tasks |
| `Enter` | Open a thread / activate |
| `Space` / `x` | Toggle the selected task |
| `←` / `→` | Collapse / expand the selected task's subtasks |
| `s` | Add a subtask under the selected task |
| `/` | Jump to the command bar |
| `a` | Jump to the add-task box |
| `c` | Complete the current thread |
| `m` | Switch between WORK and PERSONAL mode |
| `?` | Show this shortcut list |
| `Esc` | Close a box or overlay |

## Where your data lives

Every thread is a real Markdown file you can open in any editor or in
Obsidian. Nothing is locked inside the app.

## Trouble?

- **AI features show an error**: the OpenAI key is missing or the service is
  unreachable. Manual editing keeps working; set `OPENAI_API_KEY` to re-enable
  the smart command bar and icons.
- **"Default password" banner**: set the `APP_PASSWORD` environment variable.
