---
name: blog-edit-integrity
description: Phase 5 of blog editing. Fact checks dated, numbered, and named claims; verifies quotes and reported speech against sources; flags verified-but-unsourced claims for linking; steelmans the people critiqued; adversarially attacks the spine; validates links and local files; labels provenance. Use before line editing.
version: 0.1.1
tags: [writing, editing, blog, fact-check]
---

# Blog Edit: Integrity (phase 5)

The piece must survive checking. Read-only pass; reports, never edits.

## Process

1. **Fact check.** Extract every dated, numbered, or named claim, including claims about a specific person: what they said, did, felt, or believed (was scared, did not accept, asked, spent his career). Those are checkable facts, not style. Verify each against a source (web search, the local files in `files/<date>/`). Verdict per claim: verified, wrong, or unverifiable. Unverifiable claims get flagged for the human. A claim verified against a source but carrying no link or citation in the draft is a finding on its own, "verified but unsourced": the reader cannot check it, which defeats the pass. Every verified checkable claim must end up linked in the draft, either directly or through a reviser finding that names the link to insert.
2. **Quote verification.** Every quotation mark in the draft: check exact wording against the source. Paraphrase dressed as quote is a finding. Also check reported speech written without quotation marks: "He asked:", "He wrote", "she said", "he quotes", followed by a first-person clause. Near-verbatim first-person wording attributed to a person is a quote even without marks; it needs a source link and its wording must match the source. "He asked: who would ensure that I did not forget something..." with no marks and no link is the same failure as a misquoted quote.
3. **Fairness pass.** For each person or position the piece critiques: is it represented in its strongest form? Quote what they actually claim before the critique.
4. **Adversarial pass.** State the strongest counterargument to the spine. Report whether the piece answers it, dodges it, or is vulnerable to it.
5. **Link validation.** Every external URL: does it resolve, does it point where the anchor text claims, is it stable (prefer DOI, arXiv, Wikipedia). Every local reference (`files/...`, images): does the file exist.
6. **Provenance labels.** Mark each claim: firsthand anecdote, documented fact, or opinion.
7. Write `integrity.log` with per-claim verdicts and finding ids.

## Worked example

For notes/blog/20260806_: the claim "the atrophying of spatial reasoning under GPS is decently documented" was unsupported; the pass added Dahmani and Bohbot 2020 and Ruginski et al. 2019 citations.

For notes/blog/20260806_: the Voevodsky story was verified against Voevodsky's own IAS essay, but the draft carried no link to it, and "He asked: who would ensure that I did not forget something..." was near-verbatim reported speech presented without quotation marks or link. A corrected run flags both: one "verified but unsourced" finding naming the essay link, one unmarked-quote finding.

## Edge cases

- No web access: mark all external claims "unchecked" and list them for the human.
- Paywalled sources: record the citation even if the full text is unreachable; note the access limit.
- Do not fix claims; report. The reviser applies approved fixes with changelog entries.
- Verified but unsourced is not a pass: confirming a claim in the log while leaving the draft unlinked lets it masquerade as unsourced. Always produce a finding that names the link to insert.
- Reported speech without quotation marks is still attributed speech, and it is still a quote if near-verbatim. "He asked:", "He wrote", "he quotes" followed by a first-person clause goes through the same exact-wording check as text in quotation marks.

## References

- Orchestrator: blog-edit
- Runs before: blog-edit-line
