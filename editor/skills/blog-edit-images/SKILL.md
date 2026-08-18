---
name: blog-edit-images
description: Phase 8 of blog editing. The image pass. Scouts spots where an image does work, states a job per image, sources or creates it, verifies correctness, tests function by reading with and without, and audits globally. Every image must do a job the text cannot do as well.
version: 0.1.0
tags: [writing, editing, blog, images]
---

# Blog Edit: Images (phase 8)

An image with no job is decoration, and decoration in an essay is noise.

## Roles (see blog-edit for the convergence protocol)

- Scout: finds candidate spots
- Sourcer: finds or commissions the asset, records provenance and permissions
- Verifier: opens the asset, confirms it shows what the job requires
- A/B reader: reads with and without, reports the difference as evidence, takes no side
- Advocate and critic: argue keep vs cut
- Image editor: rules on the dispute; never argues a side itself

## Process

1. **Scout.** Mark where the text does visual work in words: a flow, a structure, an object the reader cannot see, more than three moving parts the reader must hold.
2. **Job.** Per candidate, one sentence: what the reader gets from the image that the paragraph does not give. No statable job, no image.
3. **Source or create.** Screenshots and slides: record provenance and permissions. Created diagrams and charts: value axis starts at zero, no emojis, text labels or SVG icons only.
4. **Verify correctness.** Open the image. Does it show what the job requires? Readable at render size? Provenance real?
5. **Verify function by removal.** A/B read the section. The image stays only if the with-version reads clearly better. Disagreement goes to the convergence protocol.
6. **Global audit.** Count and density, long imageless deserts, consistency of treatment (sizing, captions, attribution format; deliberate breaks allowed if they mean something), each image right after the text that motivates it.
7. Write `images.log` with candidates, jobs, verdicts, and the audit.

## Worked example

For notes/blog/20260806_: the "Tao's pipeline" section describes a five-step refinement chain in prose. Job: let the reader see the flow as a network. Source: page 43 of files/20260806/Tao_slides.pdf, the "Goal (final attempt?)" slide showing generation, verification, exposition, publication, digestion, canonicalization. Extracted with `pdftoppm -f 43 -l 43 -png` and verified visually.

## Edge cases

- Never embed an unlicensed image; when in doubt, redraw and attribute the idea.
- If the piece has zero candidate spots, say so; do not invent one.

## References

- Orchestrator: blog-edit
- Design: /home/k1/public/notes/editor/docs/images.log
