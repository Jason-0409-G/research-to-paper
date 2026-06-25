# research-to-paper

> **English** ｜ [中文](README.md)

Producing a research manuscript spans a series of loosely coupled, individually error-prone stages: fixing the
angle of attack, retrieving the literature and verifying that every citation is real and correctly attributed,
drafting in proportion to the strength of the evidence, pruning over-claims through independent review, governing
readability and the detectable traces of machine authorship, and finally typesetting to a submission format. These
stages are usually handled by a scatter of single-purpose tools or by hand, and the seams between them are where
things break — a mis-attributed DOI, a sentence that runs ahead of its evidence, a paragraph whose uniform cadence
reads as machine-written — any one of which can cost a manuscript its credibility at review.

**research-to-paper consolidates this chain into a single, fully self-contained skill.** As one plugin, it carries
a research idea systematically through all of the stages above while keeping the author in the decision loop
throughout. Its design rests on three principles. **Rigor** — every reference's DOI is checked one by one against
CrossRef, wording is matched to the strength of the evidence (a model or single gene may only *predict*; a measured
whole-system result may *confirm*), and the draft is cross-examined by several mutually independent reviewer agents.
**Self-containment** — search, verification, review, drafting, de-AI, and typesetting are all built in; it depends
on no external skill, so installing this one plugin gives you the whole pipeline. **Auditability** — every writing
judgment and every de-AI edit leaves a traceable record matrix rather than a black-box output.

The full pipeline runs: **research idea → fix the direction (including the target journal and its author
requirements) → build a verified reference library → draft → multi-round adversarial review → de-AI (with long-short
sentence variation) → render LaTeX / Word / PDF**; each stage can also be invoked on its own.

Works in **Claude Code** and **Codex**.

---

## Install

> Don't have Claude Code yet? **Windows users (especially on slow networks in mainland China)** see [Installing Claude Code on Windows (with China mirrors)](docs/install-claude-code-windows.md) — a China-focused, Chinese-language guide.

### Claude Code

**Option 1 · Plugin marketplace (recommended)**

```
/plugin marketplace add https://github.com/Jason-0409-G/scriptorium.git
/plugin install research-to-paper@scriptorium
/reload-plugins
```

**Option 2 · Script (clone, then install locally)**

```bash
git clone https://github.com/Jason-0409-G/scriptorium.git
cd scriptorium
bash install.sh claude          # macOS / Linux
# Windows PowerShell:  .\install.ps1 -Target claude
```
Restart Claude Code, then just ask it to "follow the research-to-paper workflow".

### Codex

```bash
git clone https://github.com/Jason-0409-G/scriptorium.git
cd scriptorium
bash install.sh codex           # macOS / Linux
# Windows PowerShell:  .\install.ps1 -Target codex
```
The script copies the seven skills into `~/.codex/skills/` (Claude Code uses `~/.claude/skills/`). Restart Codex to
use them. `bash install.sh all` installs to both at once.

---

## Update

Every push to this repo is automatically a new version (`plugin.json` pins no version number, so Claude Code uses
the git commit SHA). To update an installed copy to the latest:

**If installed from the marketplace**
```
/plugin marketplace update scriptorium
/reload-plugins
```
`marketplace update` fetches the latest and updates installed plugins; `/reload-plugins` applies it in the current
session, or just restart Claude Code.

**If installed via the script**
```bash
cd scriptorium   # the folder you cloned
git pull
bash install.sh all    # claude / codex / all
```
Then **restart Claude Code / Codex**.

---

## What each sub-skill does

| Sub-skill | Purpose |
|---|---|
| **research-to-paper** | Orchestrator. Detects which stage you're at and routes the request through **scope → curate → write → build** as needed; each stage is also usable on its own. |
| **research-to-paper-scope** | **Decide the direction.** Reads authoritative literature first to understand the field, then confirms — one question at a time — the angle, scope, **target journal**, **word count**, and core themes; once the journal is set it **looks up that journal's author requirements** online (aims & scope, article types, length, structure, citation style). Produces `scope_brief.md`. |
| **research-to-paper-curate** | **Build the library + resource search.** Five-source literature search (OpenAlex / Europe PMC / PubMed / Semantic Scholar / Crossref) → per-paper **CrossRef DOI verification** (catching dead DOIs *and* DOIs that resolve to the wrong paper, recovering the correct one) → **multi-agent adversarial review** that rejects fabricated or mis-attributed references → **direct import into Zotero by category when a Zotero API key is set**, otherwise export **RIS (Zotero/EndNote) + BibTeX + a rich color-coded Excel that gives every paper a one-line 中文重点 (Chinese key point)** (category / DOI-verification status / **中文重点** / innovation score / impact factor / citation count; cumulative de-duplication across searches; only a `verified` DOI is exported as a trusted DOI). DOI verification runs **in parallel** against CrossRef (8 workers, cacheable / offline). Also searches biology **resource** databases: any NCBI Entrez db (protein / nucleotide / gene / taxonomy / assembly / structure / SRA …) plus UniProt / RCSB PDB / AlphaFold / Europe PMC. |
| **research-to-paper-write** | **Draft.** Understands the content first and restates the core argument with you, plans a **per-unit rationale matrix** (not a generic IMRaD template), and drafts with **evidence-matched hedging** (a model/gene only "predicts"; a measured whole-system result may "confirm"). Orchestrates the audit and humanize passes. Scenes: journal / conference / report / review / competition. |
| **research-to-paper-audit** | **Multi-round adversarial review.** Spawns **three independent reviewer agents** (claim-support / logic & structure / citation integrity) plus an Editor Synthesis, and re-runs **until a round is clean**. Catches over-claims, unsupported claims, interpretation leaking into Results, shallow edits, and citations that don't support their sentence. Usable standalone ("review this draft"). |
| **research-to-paper-humanize** | **De-AI.** Reworks prose along **five dimensions**: **D1 sentence length (long–short variation)**, D2 paragraph-structure variety, D3 information-density alternation, D4 connector control (removing AI-frequent connectors), D5 term-context variation — at a light/medium/heavy tier, recording every change in `humanize_matrix.md` and verifying with `humanize_check.py`. Usable standalone ("de-AI this paragraph"). |
| **research-to-paper-build** | **Render formats.** Uses pandoc to turn the finished manuscript into **LaTeX (.tex) / Word (.docx) / PDF**, resolving `[@key]` citations from `library.bib` into a reference list. |

Each piece **triggers on its own**: "verify these DOIs", "de-AI this paragraph", "audit my draft", "export to Word"
all hit the right sub-skill directly.

---

## Documentation

GitHub's top tab bar (README / MIT license) only recognises a **fixed set of standard files**, so arbitrary docs
can't be pinned there. Here is one-click access to all of them instead:

**Reference docs**
- [Biology public interfaces + API credentials](skills/research-to-paper-curate/references/bio-sources.md)
- [Workspace & artifacts spec](skills/research-to-paper/references/artifacts.md)
- [Writing craft: hedging ladder + per-scene structures](skills/research-to-paper-write/references/writing-craft.md)
- [Three-reviewer prompts + Editor Synthesis](skills/research-to-paper-audit/references/audit-prompts.md)
- [Five-dimension de-AI rules](skills/research-to-paper-humanize/references/humanize-rules.md)
- [Adversarial reference-review gate](skills/research-to-paper-curate/references/adversarial-review.md)
- [Credentials template `.env.example`](.env.example)

**Per sub-skill**
- [research-to-paper (orchestrator)](skills/research-to-paper/SKILL.md) · [scope](skills/research-to-paper-scope/SKILL.md) · [curate](skills/research-to-paper-curate/SKILL.md) · [write](skills/research-to-paper-write/SKILL.md) · [audit](skills/research-to-paper-audit/SKILL.md) · [humanize](skills/research-to-paper-humanize/SKILL.md) · [build](skills/research-to-paper-build/SKILL.md)

---

## Modes, scenes & depth

- **Two entry modes**: **Rewrite Existing** (strengthen your draft's argument / structure / hedging — not surface polish) or **Build From Materials** (draft from notes, data, figures, PDFs, partial drafts).
- **Target scenes**: `journal` · `conference` · `report` · `review` · `competition` (each with its own structure).
- **Research depth**: `flash` (3 scene exemplars + 3 recent in-field papers + the venue's requirements) or `pro` (6 + 6).
- **Output language**: `English` or `Chinese` (the de-AI check matches with `--lang`).

`research-to-paper-scope` confirms these one question at a time and records them in `scope_brief.md`; every later stage follows it.

---

## Public data interfaces

`research-to-paper-curate` integrates the public APIs below. **Every search/lookup is key-free** (a key only raises rate limits; only the Zotero *write* import needs one). Literature goes through `search_papers.py` (five sources, merged + de-duplicated); biology resources through `bio_search.py`.

- **Literature**: OpenAlex, Europe PMC, PubMed, Semantic Scholar, Crossref.
- **Biology resources**: any **NCBI Entrez** db (`protein` / `nucleotide` / `gene` / `taxonomy` / `genome` / `assembly` / `structure` / `sra` / `bioproject` / `biosample` …), **UniProt**, **RCSB PDB**, **AlphaFold DB**, **Europe PMC**.

| Interface | Key to read? | Without a key | With a key |
|---|---|---|---|
| OpenAlex / Crossref / Europe PMC | No | free (email → faster polite pool) | — |
| NCBI Entrez (every db) | No | 3 req/s | `NCBI_API_KEY` → 10 req/s |
| Semantic Scholar | No | shared pool (throttleable) | `S2_API_KEY` dedicated limit |
| UniProt / RCSB PDB / AlphaFold | No | fully key-free | — |
| **Zotero direct import** | **Yes — write** | falls back to a `.ris` file | pushed straight in, by category |

```bash
python bio_search.py protein "class IIa bacteriocin" --retmax 10
python bio_search.py uniprot "pediocin"        # -> P29430 Bacteriocin pediocin PA-1
python bio_search.py pdb "bacteriocin"         # -> 1O82 / 5UKZ ...
python bio_search.py alphafold P29430          # query = a UniProt accession
python bio_search.py --list                    # all interfaces
```
Per-interface keys and rate limits: `skills/research-to-paper-curate/references/bio-sources.md`.

---

## Working artifacts (the auditable trail)

A full run leaves more than a final paper — it leaves a traceable writing trail in one workspace (`new_workspace.py` scaffolds it; each stage writes into it):

```
manuscript_workspace/
├── scope_brief.md              # scope: direction contract (angle / target journal + rules / word count / themes)
├── library/
│   ├── library.ris             # curate: Zotero / EndNote
│   ├── library.bib             # curate: pandoc / LaTeX
│   └── library.xlsx            # curate: per-paper Chinese key point + verification-status coloring + cumulative de-dup (.csv fallback without openpyxl)
├── writing_rationale_matrix.md # write: per-unit rationale (claim / evidence / hedge tier / source)
├── draft.md                    # write: the working manuscript (with [@key] citations)
├── audit_report.md             # audit: three reviewers + Editor Synthesis, round by round until clean
├── humanize_matrix.md          # humanize: every de-AI change (tagged D1–D5)
├── final/                      # build: main.tex / manuscript.docx / manuscript.pdf
└── artifact_manifest.md        # index written by artifact_check.py
```

The two artifacts that carry the most reasoning are `writing_rationale_matrix.md` (why the manuscript is shaped as it is) and `audit_report.md` (what independent review found and how it was resolved). A polished `draft.md` with an empty rationale matrix counts as incomplete. Full spec: `skills/research-to-paper/references/artifacts.md`.

---

## Check commands

Each check is a standard-library script (repo-relative paths below; once installed they live under `~/.claude/skills/` or `~/.codex/skills/`):

```bash
# reference DOIs are real and matched (curate; parallel 8 workers, --cache reuse / --no-api offline; non-zero exit on any mismatch/dead)
python skills/research-to-paper-curate/scripts/verify_doi.py <papers.json> <verified.json>

# the draft's [@key] / \cite resolve against library.bib (write -> build)
python skills/research-to-paper/scripts/cite_check.py manuscript_workspace/draft.md manuscript_workspace/library/library.bib

# de-AI signature is within range (humanize; --tier light/medium/heavy)
python skills/research-to-paper-humanize/scripts/humanize_check.py manuscript_workspace/draft.md --lang en --tier medium

# the artifact trail is complete, and refresh the manifest (orchestrator)
python skills/research-to-paper/scripts/artifact_check.py manuscript_workspace --write

# unit tests for the check scripts
python -m unittest discover -s tests
```

---

## Dependencies

Everything is Python **stdlib** except these optional tools (each step degrades gracefully or tells you what to
install):

- **`openpyxl`** (Python) — for the styled `.xlsx`; without it, curate writes a `.csv` instead (RIS/BibTeX unaffected).
- **`pandoc`** — required by `research-to-paper-build` for LaTeX/Word output (`brew install pandoc` / `apt install pandoc` / winget on Windows).
- **A TeX engine** (xelatex/pdflatex) — only for PDF; without it you still get the `.tex` to compile elsewhere.
- **API credentials (all optional)** — copy `.env.example` to `.env` (or `~/.config/research-to-paper/keys.env`): `CROSSREF_MAILTO` / `NCBI_EMAIL` join the faster polite pool; `NCBI_API_KEY` / `S2_API_KEY` raise rate limits; `ZOTERO_API_KEY` + `ZOTERO_USER_ID` enable **direct categorized import into Zotero** (EndNote has no public write API, so it stays a `.ris` import). `.env` is gitignored; everything works with no key at all.

---

## Running on a DeepSeek backend

These skills can be driven by **DeepSeek** through its Anthropic-compatible proxy (point Claude Code's
`ANTHROPIC_BASE_URL` at `https://api.deepseek.com/anthropic`; use the model `deepseek-v4-pro[1m]` — the `[1m]` suffix
denotes its 1M-context tier, per DeepSeek's official documentation; a template is in `templates/settings.json`). The
design is friendly to weaker models: **all fact-checking is performed by deterministic scripts, not by the model** —
`verify_doi.py` does parallel verification and title-matching in the script, so a weak model cannot "pretend" a DOI
is confirmed; the model's only residual tasks are light (assigning a category, writing a one-line Chinese key point),
and the scripts tolerate code fences / field aliases / missing fields and degrade gracefully. Note that under DeepSeek
**sub-agents run on the weaker `deepseek-v4-flash`**, so for the curate adversarial-review gate and the audit
reviewers, the deterministic gate in `verify_doi.py` (blocking on any `mismatch` / `dead`) should be the primary
safeguard on a weak backend. Full checklist: **[DeepSeek compatibility note](docs/deepseek-compatibility.md)**.

---

## DOI-verification performance (parallel)

Verifying DOIs one by one against CrossRef was the serial bottleneck in curate; parallelising it gives (measured on
12 DOIs, single machine):

| Mode | Time for 12 DOIs |
|---|---|
| Serial (`--workers 1`) | 45.1 s |
| **Parallel (`--workers 8`, default)** | **7.0 s (≈6.4× faster)** |
| Parallel + cache reuse (`--cache`) | 0.9 s (≈50×) |

For a 50–100-reference library this brings verification from minutes down to seconds. The verification logic lives
entirely in the script (parallel requests + title-matching + a discriminating-token guard; a supplied DOI is
confirmed only at a strict 0.85 similarity), and the model takes no part in DOI resolution — so on a weaker backend
such as DeepSeek both speed and correctness are unaffected.

---

## Usage

Just ask, for example:

- "I have a research direction but haven't fixed the angle yet — scope it, build a verified library, then write it as a review."
- "Verify the DOIs in these references, drop the fake ones, and give me a RIS for EndNote."
- "De-AI this paragraph, vary the sentence length." / "Audit this draft for over-claims."
- "Export this manuscript to LaTeX and Word."

The orchestrator runs only the stages you need and tells you what each produced before moving on.

---

## Validate (after editing the plugin)

```
claude plugin validate .
```
