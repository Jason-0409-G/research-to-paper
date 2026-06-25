# Running scriptorium (research-to-paper) on a DeepSeek backend

These skills were authored against Claude's strong instruction-following, but they are designed to
degrade gracefully when Claude Code is pointed at **DeepSeek** (or any non-Claude model) through the
Anthropic-compatible proxy. This note records how the backend is wired, the one config gotcha, and the
design rules that keep the skills working on a weaker model.

## How DeepSeek is wired as the backend

Claude Code reads an `env` block in `settings.json` and redirects all Anthropic API traffic to DeepSeek's
Anthropic-compatible gateway — no code patch, pure environment redirection. The working values
(`templates/settings.json`):

| Variable | Value | Role |
|---|---|---|
| `ANTHROPIC_BASE_URL` | `https://api.deepseek.com/anthropic` | route Messages-API calls to DeepSeek |
| `ANTHROPIC_AUTH_TOKEN` | your DeepSeek `sk-...` key | **use AUTH_TOKEN, not `ANTHROPIC_API_KEY`** |
| `ANTHROPIC_MODEL` | `deepseek-v4-pro[1m]` | primary model (1M-context tier) |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` / `…SONNET_MODEL` | `deepseek-v4-pro[1m]` | map Claude's Opus/Sonnet tiers |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `deepseek-v4-flash` | cheap tier |
| `CLAUDE_CODE_SUBAGENT_MODEL` | `deepseek-v4-flash` | **subagents run on the weakest model** |
| `CLAUDE_CODE_EFFORT_LEVEL` | `max` | force max reasoning effort |
| `hasCompletedOnboarding` | `true` | skip the first-run login wizard |

> **Model id:** use `deepseek-v4-pro[1m]` exactly as DeepSeek's official Claude Code integration doc shows
> (the `[1m]` is its 1M-context tier); `deepseek-v4-flash` is the cheap/sub-agent tier. Match the official
> doc's values — `templates/settings.json` carries them verbatim.

## The one risk that matters most: subagents run on `deepseek-v4-flash`

`CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash` means any work delegated to a subagent runs on the
**weakest** model in the stack. Two stages spawn subagents for *judgment*:

- **curate** — the adversarial review gate (existence / DOI-attribution / relevance).
- **audit** — the three independent reviewers.

On a DeepSeek backend, do **not** rely on those flash subagents as the sole safety net. The deterministic
`verify_doi.py` gate is the primary protection against the dangerous case (a DOI that resolves to the
*wrong* paper): it title-matches every DOI against CrossRef in a script, not in the model, and returns a
non-zero exit code on any `mismatch`/`dead`. Treat that gate as blocking, and run the review reasoning on
the main model rather than delegating it when the backend is weak.

## Why this skill set survives a weak model: scripts own every fact-check

The load-bearing design choice (shared with paper-spine) is that **deterministic Python scripts own every
verifiable fact, never the model**:

- `search_papers.py` does the multi-source search and dedup.
- `verify_doi.py` does DOI resolution + blended title-match (Jaccard·0.5 + SequenceMatcher·0.5, threshold
  0.75) **in the script**, parallelized across CrossRef with an optional cache; the model never looks up or
  judges a DOI, so a weak model cannot hallucinate a "verified" DOI. Run with `--no-api` for offline/CI.
- `export_refs.py` produces and the scripts consume JSON; the model only passes file paths.

The model's residual jobs are kept small and mechanical: assign a `category`, write a one-line `key_point_zh`
(Chinese key point, faithful to the abstract), and read back a verdict. `export_refs.py` accepts field
aliases (`key_point_zh` / `cn_summary` / `cn_keypoint`) and renders blanks for any missing field, so a weak
model that omits or mis-names a field degrades gracefully instead of breaking the pipeline.

## DeepSeek-compatibility checklist (apply to each SKILL.md)

**Structure & length** — active-instruction body lean; long material in `references/*.md`; open with numbered
imperative steps; hard constraints in a short top block; restate the critical rule *at* the step that needs it.

**Determinism over judgment** — push every multi-step decision into a bundled script; give each invocation as a
copy-paste **"Run this exact command:"** block; never ask the model to plan a tool-call sequence from scratch;
do not delegate judgment-heavy steps to subagents (they run on `deepseek-v4-flash`).

**Structured data** — pass data between steps as files; scripts produce/consume JSON; never ask the model to
hand-write large JSON; tolerate code fences / aliases when reading model-produced fields.

**Iteration** — gate multi-round loops on a machine-readable PASS/FAIL (e.g. `verify_doi.py`'s exit code), not
"repeat until it looks good"; add explicit "do not proceed until step N's output exists and validates" gates.

**Language** — keep one instruction language in the active steps; state the **output language explicitly per
step** (don't let the model infer 中文 vs English); keep bilingual trigger keywords in the frontmatter only.
