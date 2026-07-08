# Development Kickoff Questionnaire

> **Purpose**: Capture everything needed, in one place, to kick off the definition of a new app. Fill in what you know (leave blank or mark as "TBD" what you don't). This document is the **entry point**: it feeds Step 0 of `agents.md`, from which `spec.md` is drafted.
>
> It does not need to be perfect or complete — the more detail you provide, the fewer follow-up questions will be needed. Mark with `[x]` the checkboxes that apply.

Date: 2026-07-08 · Author: pchinso · Brief version: v1

---

## 1. Project Identity

- **Name (provisional)**: Focus Mode On
- **One-liner** (what it is, who it's for): Personal task management and productivity tool for a solo developer
- **Owner / responsible**: pchinso
- **Expected team** (initials/roles): Solo — user pchinso only

## 2. Problem and Objective (Vision)

- **What problem does it solve?** Task management organized as activity areas containing Initiatives and internal projects. Tasks are structured as hierarchical threads, branching from a root node of primary semantic meaning down to the lowest-level individual task.
- **What decisions does it enable the user to make?** Record completed work and visualize pending items, all within the app UI. The goal is to eliminate manual management of `.md` files — the UI handles this through an AI automation layer.
- **What is done today without this app, and why is that insufficient?** Obsidian was used previously, but it lacks an automation layer for natural-language processing — which is exactly what this app aims to integrate. The intent is for natural-language text input to drive both the creation of new tasks and the completion of existing ones.
- **How will success be measured?** Improved productivity and daily focus through consistent tracking of both work and personal activities.

## 3. Users and Usage Context

- **Who uses it?** (profile, technical level): Solo developer (myself)
- **How many users, and concurrently?** 1
- **Where is it used?**
  - [ ] Windows desktop, offline
  - [X] Web browser
  - [ ] Command line / scripts
  - [ ] Server / service
  - [ ] Embedded in another tool
  - [ ] Other: ...
- **Interface language(s)?** English

## 4. Scope

- **Must-have in V1** (non-negotiable):
  1. Entry dashboard displaying activity threads.
  2. Two top-level activity nodes: **WORK** and **PERSONAL**.
  3. From each node, secondary threads branch off hierarchically, evolving and subdividing until completion. Completing a thread triggers automatic archiving, with an option to restore it if needed.
  4. A list of pending and completed tasks at the end of each thread. Completed tasks appear above pending ones.
  5. An AI layer for updates via natural-language text input (via the OpenAI API).
  6. Ability to generate semantically relevant images or icons for easy visual identification of different activity threads (by initiative and/or project).
  7. All files are Markdown (`.md`), readable and correctly formatted outside the app GUI. Inside the app, they are parsed and rendered into a more visual and interactive UI.
  8. The browser GUI interprets the files visually, presenting them in an attractive, interactive format.
  9. Keyboard-only navigation throughout the UI.
- **Nice-to-have later** (roadmap): Ingestion of external information for context building; online search for relevant information.
- **Explicitly OUT of scope**: Not yet defined.

## 5. Existing Assets to Reuse *(very important)*

- **Is there existing code / prototypes / notebooks?** Paths or repos: Sample daily notes from Obsidian only, located in `references/`.
- **Executables or legacy engines?** Language? No.
- **Excel / planning or calculation documents for reference?** No.
- **Is there an existing GUI or design to use as a base?** No.
- **What should be ignored / discarded from existing assets?** The references are for context only and should not influence the design.

## 6. Architecture and Platform *(preferences and constraints)*

> The final decision is made in `spec_architecture.md`; only include what you already know or require here.

- **Target operating system**: Cross-platform
- **Preferred or required language/stack** (if any): Python / web
- **IT restrictions?** (no server, no internet, antivirus, permissions): Lightweight and fast framework; must support free hosting and straightforward update management via GitHub.
- **Architecture pattern intuition** (non-binding):
  - [ ] Monolithic desktop app
  - [ ] GUI + CLI calculation engines (JSON contract)
  - [ ] Client + service/API
  - [X] Web application
  - [ ] Library / CLI without GUI
  - [ ] Don't know — let it be proposed

## 7. Data: Inputs and Outputs

- **Inputs** (data consumed, formats: JSON/CSV/Excel/DB, volume): `.md` files
- **Outputs** (what it produces: tables, charts, reports, files): `.md` files
- **Time series or large volumes?** Resolution and size: No.
- **Persistence?** Need to save projects/scenarios/history? A database could be valuable — possibly a semantic vector database.
- **Reference data libraries?** (catalogs, manufacturers, lookup tables): Could be relevant for certain projects.

## 8. Key Calculations / Functionality

- **Main calculations or business logic** (list): None initially.
- **Optimization, simulation, statistical analysis?** Not required.
- **Expected calculation times?** (seconds / minutes): Sub-second.
- **Anything that must NOT block the interface?** The UI must always remain fast and fluid.

## 9. Distribution and Protection

- **How is it delivered?**
  - [ ] Standalone executable (installable / portable)
  - [ ] Package / library
  - [X] Web access / service
  - [ ] Other: ...
- **Distributed to third parties outside the team?** [ ] Yes [x] No
- **If yes, is protection/licensing needed?** (expiry, machine binding, traceability): No → activates `spec_licensing.md`.
- UI access protected by password.
- Uploaded data protected by encryption.
- **Support/contact for users?** No.

## 10. Visual Identity

- **Apply standard Cox identity?** [x] Yes (default) [ ] With exceptions: ...
- **Light/dark mode?** [x] Both [ ] Light only [ ] Indifferent
- **Special visual requirements?** (dashboards, maps, 3D, print): Visually rich representation of activity threads.

## 11. Non-Functional Requirements

- **Performance / limits**: Fast and responsive for the user.
- **Security / data confidentiality**: Data encryption and access protection for the app.
- **Accessibility / print / export**: Generation of an HTML report with visual identity applied.
- **Maintenance**: Who will maintain it and for how long? pchinso, indefinitely.

## 12. Planning

- **Target date for first usable version**: As soon as possible.
- **Milestones or key dates**: None.
- **Estimated / available effort**: Claude Max for app development.
- **External dependencies** (data, people, approvals): OpenAI API key.

## 13. Risks, Open Questions, and Unresolved Decisions

- **Risks already identified**: Difficulty finding a UI that is both visually attractive and conceptually well-structured, with intuitive interaction.
- **Open questions you have yourself**: What the interface will look like — leaving this for the AI to propose.
- **Decisions deferred for later**: Inviting external collaborators to contribute to a project or activity thread.

---

## Free Notes

Anything that doesn't fit above: context, examples, screenshots, links…

---

> **Next step**: Submit this completed questionnaire. With it, follow the procedure in `agents.md` to produce the app's `spec.md`, using `spec_vision.md`, `spec_architecture.md`, `spec_visual_id.md`, and (if applicable) `spec_licensing.md`.
