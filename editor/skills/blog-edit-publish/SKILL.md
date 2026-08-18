---
name: blog-edit-publish
description: Phase 9 of blog editing. Publication. Metadata and slug, permissions, stripping working sections, build and preview, final rendered read, and distillation of durable lessons into the global docs.
version: 0.1.0
tags: [writing, editing, blog, publishing]
---

# Blog Edit: Publish (phase 9)

Ship it, then learn from it.

## Process

1. **Strip working sections.** Remove the unanswered-questions section and the takeaway-read section, including the `---` separator they sit under.
2. **Metadata.** Frontmatter, description, slug, filename (`YYYYMMDD_slug.md`). Tags via the tag-post skill; tag hierarchy via update-hierarchy if new tags appear.
3. **Permissions.** Every third-party asset (screenshots, slides, figures) has attribution, permission, or anonymization.
4. **Build and preview.** Run the blog build. Confirm the post renders, images load, LaTeX renders, links resolve.
5. **Final rendered read.** Top to bottom in the rendered page, not the source. This read belongs to the human.
6. **Distillation.** Mine the workspace for zero to three durable lessons, lines that would be true for a post not yet written. Append to the global brief.log or workflow.log. Raw debates and findings stay in the workspace, never re-read mid-edit.
7. Close the workspace changelog with a shipped entry.

## Worked example

Candidate distillation from notes/blog/20260806_: "endings on this blog open the question, they do not answer it." (Already covered by the standing aim, so it would not be re-added; a real example would be a lesson the docs do not yet carry.)

## Edge cases

- Publish is a human gate: never push or deploy without the human's go.
- If the build fails, fix the build issue, not the post.
- If distillation finds nothing, record "no new lessons"; do not manufacture one.

## References

- Orchestrator: blog-edit
- Composes: tag-post, update-hierarchy
- Blog build: /home/k1/public/notes/blog/build.py
