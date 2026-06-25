---
name: research-to-paper-scope
description: >-
  Decide the direction of a paper BEFORE searching or writing, by researching the field first and then
  discussing with the user one question at a time. Given a broad topic, it reads a few authoritative sources
  (recent high-impact reviews + seminal works), then proposes 2-3 concrete angles with trade-offs, and locks the
  entry mode (build-from-materials vs rewrite), angle, scope, target scene (journal/conference/report/review/
  competition), target journal, research depth (flash/pro), word count, output language (中文/English), and core
  themes through step-by-step confirmation.
  Once the target journal is set, it looks up that journal's author requirements online. Use whenever the user
  says 帮我定研究方向, 我有个大方向想缩成题目, 这个综述/论文该从哪个角度写, 帮我选切入点, 我想投X期刊先确定方向和要求,
  "help me scope this", "narrow my topic", "what angle should I take", "figure out the direction before I start".
  Produces a scope_brief.md that feeds research-to-paper-curate (categories) and research-to-paper-write (motivation + journal limits).
---

# Scope — decide the direction (research first, then discuss)

The point of this stage is to avoid the most expensive mistake in academic writing: searching and drafting in
the wrong direction. So the order is deliberate — **understand the field before proposing anything, and let the
user steer every decision.** Do not jump to a title or start collecting references until the direction is locked.

## Step 1 — Understand the field first (don't propose yet)

Take the user's broad direction and read enough to speak about it credibly. Use the bundled search
(`../research-to-paper-curate/scripts/search_papers.py`) or web search to find a small, high-signal set, scaled to
the research depth (Step 2): **flash** ≈ 3 recent/seminal in-field works plus a couple of target-scene exemplars;
**pro** ≈ 6 + 6 (default to flash for this first pass, then read more if the user picks pro). This is orientation
reading, not the full library search (that's CURATE's job) — you want the lay of the land: what's established,
what's contested, where the open questions are, and how the best papers frame the topic.

Read enough to answer, for yourself: what are the live debates, what gaps keep getting named, and what framings
do strong papers use? If you cannot answer these, read more before continuing. Proposing directions from a thin
understanding is how scopes go wrong.

Tell the user briefly what you learned (a few sentences, with the key sources), so they see the basis for the
options you're about to offer.

## Step 2 — Propose directions, one decision at a time

Now offer **2-3 concrete angles / research questions**, each with its trade-offs and your recommendation, grounded
in what you just read (e.g., "Angle A occupies the gap that Reviews X and Y both flag, but needs data you may not
have; Angle B is safer and still novel because…"). Lead with the one you'd pick and say why.

Ask about **one decision at a time** — do not dump a questionnaire. Wait for the user's choice before moving to the
next decision. The decisions to lock, in order:

1. **Entry mode** — Rewrite Existing (improve a draft they already have) or Build From Materials (draft from notes,
   data, figures, partial drafts).
2. **Angle / research question** — the specific claim or question, not the broad topic.
3. **Scope boundaries** — what's in and what's explicitly out (this prevents an unfocused review).
4. **Target scene** — `journal` / `conference` / `report` / `review` / `competition`; this sets the structure.
5. **Target journal / venue** — which one they're aiming at. If unsure, suggest 2-3 fits for the angle.
6. **Research depth** — `flash` (3 scene exemplars + 3 recent in-field papers + the venue's requirements) or `pro`
   (6 + 6).
7. **Word count / length** — their target, or the venue's limit once known.
8. **Output language** — English or Chinese.
9. **Core themes / sub-topics** — the 3-6 threads the paper will develop; these become the literature categories
   in CURATE and the section spine in writing.

For each, present options or a recommendation, let them decide, then confirm back what was chosen before the next
question. If a choice contradicts an earlier one, surface it rather than silently proceeding.

## Step 3 — Once the journal is set, look up its requirements

As soon as the target journal is confirmed, go find that journal's actual author guidance — do not rely on memory,
journal requirements change and vary a lot. Use web search/fetch to pull the journal's *Guide for Authors* / *Author
Instructions* and capture what will constrain the writing:

- aims & scope (does the angle fit? flag early if it's a stretch),
- accepted article types (does "review" / "report" / "research article" match what the user wants?),
- length limits (word count, figure/table caps, reference caps),
- required structure (IMRaD? structured abstract? specific sections),
- reference/citation style.

Summarize these back to the user and reconcile them with the earlier decisions (e.g., if their word count exceeds
the journal's limit, raise it now). If the angle doesn't fit the journal's scope, say so before any drafting.

## Step 4 — Write the direction brief

Capture everything in **`scope_brief.md`** so the later stages don't re-litigate decisions:

```
# Scope brief: <short title>
Entry mode: <Rewrite Existing | Build From Materials>
Target scene: <journal | conference | report | review | competition>
Research question / angle: ...
Scope:
  - in:  ...
  - out: ...
Target journal / venue: <name>
  Article type: ...   Length limit: ...   Structure: ...   Citation style: ...   Scope fit: ...
Research depth: <flash | pro>
Target word count: ...
Output language: <English | Chinese>
Core themes (→ literature categories): 1) ... 2) ... 3) ...
Key sources read for orientation: <a few with DOIs>
Open questions still to resolve: ...
```

Hand this brief to `research-to-paper-curate` (its themes become the search categories) and to `research-to-paper-write`
(the angle becomes the motivation, the journal requirements become hard constraints). The brief is a contract: later
stages follow it, and any change to direction comes back through this stage, not improvised downstream.

## Principles

- Research before you propose; propose before you ask; confirm before you proceed.
- One decision per question. The user steers; you inform and recommend.
- Journal requirements are looked up live, never recalled, and reconciled with the user's choices immediately.
