---
tags: reading, tools, observation
---
# Marginalia

I keep finishing books and forgetting the things they teach. I've had the same issue with math and had looooooooooong discussions with Ehssan about what does it even mean to "learn"/"know" something? Any ways, here is the situation: I remember the broad arc of *Difficult Conversations*, the three-conversation framework, the language of "the third story", the idea that intent and impact are different things. That stuff sticks. What doesn't stick is the moves. The small, specific actions the book was actually trying to give me. Months later, in the middle of an actual difficult conversation, I can't remember whether to acknowledge feelings before problem-solving or after, or what to say when the other person won't disengage from blame, or how to surface the relationship issue that's lurking under the surface complaint. The framework lives in my head as a vibe. The skills the framework was supposed to deliver, don't. Of course the more I read the book over and over and the more I use it it starts to stick more and even becomes the second nature to me, I do lots of things without even thinking about them, or sometimes without even noticing I've read about them in a book, it just feels natural to do it, but those are RARE! These books have a ton of things and it takes a lifetime to learn them, let alone master them.

Reading was the easy part. Translating reading into anything I could actually use is where the loop kept breaking. So I started building a thing for myself.

## What it is

[Marginalia](https://k1monfared.github.io/marginalia/) is a personal library where each book I read produces two artifacts: a conceptual outline of the book, and a set of discrete, actionable skills extracted from it. The outline tells me what's in the book. The skills tell me what to do.

A skill is a small file with a fixed shape. It names the situation in which it should fire, the move (numbered steps), what success looks like, the failure mode it prevents, a worked example from the book itself, and the source. About 200 to 400 words each. Each one is supposed to be a thing I can reach for and apply, not a thing I read once and nod at.

Right now Marginalia has four books across three categories:

- **Literature**: George Saunders, *A Swim in a Pond in the Rain*
- **Communication**: Stone & Heen, *Thanks for the Feedback*; Stone, Patton & Heen, *Difficult Conversations*
- **Relationships**: Jessica Fern, *Polysecure*

That's about 130 atomic skills plus a handful of recipes that combine them.

## What goes in, and what stays out

The thing I keep refusing to do is put feel-good (motivational) books in here. I'm not interested in collecting *Atomic Habits* style life-hack distillations. I want books that actually teach a craft. Saunders teaches you how to look at a draft and know what's wrong with it. Stone and Heen teach you what to do when feedback hurts and you can't tell whether it's also useful. Fern teaches you how to read your own attachment patterns instead of attributing them to your partner(s). These aren't motivation, they're moves.

The test for whether something becomes a skill is pretty strict. I need to be able to write the action concretely, not "be more empathetic" but the specific thing to do. I need to write what success looks like, so I'd know if it worked. I need to write the failure mode it prevents, so I know why I'd reach for it. And the move can't already be obtainable from another skill in the library. If a candidate can't pass all four checks, it gets dropped or folded into an existing skill.

The discipline matters because the alternative is a much bigger pile that's much less useful. A library of 500 vague moves is worse than a library of 130 specific ones. I already have a lot of vague moves. I have whole shelves of books worth of vague moves.

## The reading log alongside the skills

For each book there's also a "log" file: a hierarchical text outline of the book's concepts, organized conceptually rather than by chapter. The skills tell me what to do; the log tells me how the ideas connect. They're complements. The log is the only place I keep extended summary, because once a concept is in the log it doesn't need to be re-explained inside each skill that touches it.

The site has a viewer for both. You can browse the log as a foldable tree, or browse the skills with tag filters and a query language (`emotion AND identity NOT cut`), or search inside any skill's body. Skills cross-reference each other and clicking one navigates you across the library.

## Reflection prompts

*Polysecure* was the book that introduced something I hadn't planned for. Fern ends most chapters with a list of "Questions to Consider", small reflection prompts that you're meant to take into your own relationships. They're not part of the move. They're the prompts that make the move land in your specific case.

I added a "Reflection prompts" section to the skill format to carry these. So now a skill from *Polysecure* not only tells you what to do, it also asks you what state your relationships are currently in, where the move would apply, what's already working, what isn't. The questions don't substitute for the move; they make the move applicable to *you*, not just to the abstract reader the book imagines.

I'd like to do this for the other books too. Saunders has reflection-shaped prompts buried in the essays ("what did you feel and where did you feel it?"); Stone and Heen have them implicit in their worked examples. Going back and surfacing them is the kind of thing that takes a re-read.

## Why this connects to the rest

I've been [writing](https://github.com/k1monfared/notes/blob/main/blog/20251023_from_measurement_to_intention.md) about how we substitute proxies for the things we actually care about, and then optimize for the proxy until we forget the original goal. Reading is one of those proxies. We measure ourselves by books finished. We talk about which ones we've read. We make Goodreads lists. We forget that the point was the change in us, not the count. I re-read "thanks for the feedback" every few years, even though it is a very dense and heavy book. 

A reading list full of titles tells you nothing about whether any of those books rewired how you act. A library of extracted moves at least tries to. I'm not claiming this catches everything: a lot of what books do is happen to you slowly over years, and you can't extract that. But the parts that are *teachable* deserve the dignity of being written down as teachable. AND this is not supposed to be a substitute for reading those books, this is more for a review, a personal notes after I read the books. So if you're interested, I'd highly recommend reading those books.

## On building this with Claude

I built most of this with Claude Code in long sessions. This is something I keep thinking about: it's now actually possible to take a vague aspiration like "I want my reading to compound" and turn it into a piece of working software in an afternoon, where in 2020 it would have taken weeks I never would have spent. The pace at which something like Marginalia can come into existence is almost vertiginous. The bottleneck has moved entirely to knowing what you actually want.

Which is, I think, the same thing I keep writing about. The hard part isn't capability anymore. The hard part is having a stable enough sense of what you're trying to do that the capability can serve it.

## What's next

I'm thinking I want a way of adding my experiences to this too, i.e. as I get into a situation that some of these skills apply, I want to note what I did, what worked, what didn't etc, and accumulate those over time. This will be the real learning and applying part. Though I think the HARD thing is to log all of those. Need another app for that I guess ;)

What I'd actually like is for friends to use it, or fork it, or make their own. The shape generalizes. Pick a book, write the skills, write the log, drop them in. The infrastructure handles the rest. The process doc is a real walkthrough, and reading any existing book's `_book.md` will give you the template.

If you build one and want it to live alongside mine, send me the repo. I might run them all together at some point.
