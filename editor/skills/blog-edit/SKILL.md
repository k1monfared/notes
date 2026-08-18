---
name: blog-edit
description: Orchestrates the multi-pass editing workflow for a blog post. Use when editing, revising, restructuring, or preparing a blog post for publication. Sequences the blog-edit-* phase skills, manages the per-post workspace, enforces the convergence protocol, and owns the changelog.
version: 0.1.0
tags: [writing, editing, blog, orchestrator]
---

# Blog Edit (orchestrator)

Runs the blog editing workflow end to end on one post. Design docs: `/home/k1/public/notes/editor/docs/*.log`.

## Usage

- "edit this post: notes/blog/20260806_"
- "resume the edit on 20260806_"
- "run the structure pass on this draft"

## The ordering principle

Big to small, cheap to change before expensive. Cut or move paragraphs before polishing sentences. Fact check before line editing. Validate links after the reorder. Never break this order.

## Process

1. **Locate the workspace.** Derive the date prefix from the post filename (`20260806_` gives `20260806`). Workspace is `files/<date>/_editing/` relative to the post. If missing, create it with `debates/` and `escalations/` subdirs, and confirm the repo gitignore covers `blog/files/*/_editing/`.
2. **Find the current phase.** Read the workspace. Which artifacts exist tells you where to resume.
3. **Run phases in order**, dispatching the phase skill for each (as a subagent when the pass is read-only). Phase table below.
4. **Stop at human gates.** Never proceed through a gate without the human. Gates: the spine decision, approval of the structure proposal, voice disputes, publish-or-not.
5. **Apply edits only through the changelog.** Every edit to the draft gets one entry in `changelog.log`: `date | pass | finding id | edit | rationale | decided-by` where decided-by is writer, editor ruling (packet id), or human.
6. **Handle disputes with the convergence protocol** (below).

## Phase table

| # | Phase | Skill | Artifact |
|---|-------|-------|----------|
| 0 | Brief | blog-edit-brief | brief.log |
| 1 | Inventory | blog-edit-inventory | points.log |
| 2 | Clarity | blog-edit-clarity | clarity.log |
| 3 | Spine | HUMAN DECISION | brief.log spine section |
| 4 | Structure | blog-edit-structure | structure.log |
| 5 | Integrity | blog-edit-integrity | integrity.log |
| 6 | Line level | blog-edit-line | lineedit.log |
| 7 | Reader facing | blog-edit-reader | reader.log plus working sections in the draft |
| 8 | Images | blog-edit-images | images.log |
| 9 | Publication | blog-edit-publish | distillation into global docs |

## Convergence protocol

For any writer-reader disagreement:

1. Reader files numbered findings with severity (high, medium, low).
2. Writer responds per finding: accept and change, or defend with a reason.
3. Stop when converged, when a round adds no new findings, or after 3 rounds.
4. No convergence: write an escalation packet to `escalations/NNN-slug.log` (dispute in one sentence, both positions steelmanned, round verdicts, a recommendation per side) and escalate one level. Only spine, voice, and publish-or-not reach the human.
5. Low severity findings never escalate; the writer's call stands.

## Standing rules

- Judges never edit, editors never judge. Evidence agents (fact checker, A/B reader) never take sides.
- On this blog, provocative titles and open endings are deliberate. Never flag them.
- Working sections appended to the draft (unanswered questions, takeaway read) are stripped before publication.
- Agents communicate through workspace files only. If it is not in the workspace, it did not happen.

## Edge cases

- Post has no `files/` dir: create it.
- Workspace exists mid-run: resume at the first phase whose artifact is missing or stale.
- Draft has no date prefix in its name: ask the human for the workspace location.

## References

- Phase skills: blog-edit-brief, blog-edit-inventory, blog-edit-clarity, blog-edit-structure, blog-edit-integrity, blog-edit-line, blog-edit-reader, blog-edit-images, blog-edit-publish
- Design: /home/k1/public/notes/editor/docs/workflow.log, agents.log, workspace.log, brief.log, images.log
