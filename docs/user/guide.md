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
a description, and the task list. Completed tasks are listed above pending
ones.

- **Toggle a task**: click it (or select it and press <kbd>Space</kbd>).
  Completing a task stamps today's date.
- **Add a task**: type in the box at the bottom and press <kbd>Enter</kbd>.
- **Complete a thread**: press the *Complete & archive* button. The thread
  moves to the archive.

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
| `/` | Jump to the command bar |
| `a` | Jump to the add-task box |
| `c` | Complete the current thread |
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
