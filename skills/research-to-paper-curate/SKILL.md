---
name: research-to-paper-curate
description: >-
  Build a trustworthy literature library with NO dependency on any other skill: search five literature databases
  (OpenAlex, Europe PMC, PubMed, Semantic Scholar, CrossRef), verify every DOI against CrossRef (catching dead DOIs
  and the worse case of a DOI that resolves to the wrong paper), run a multi-agent adversarial review to reject
  fabricated or mis-attributed references, then either import straight into Zotero (via its Web API, one collection
  per category, when ZOTERO_API_KEY is set) or export a single RIS that imports into both Zotero and EndNote, plus
  BibTeX and a rich color-coded Excel that gives every paper a one-line 中文重点 (Chinese key point) alongside
  category, DOI-verification status, and optional innovation score. It also searches biology RESOURCE databases — any NCBI Entrez db
  (protein, nucleotide, gene, taxonomy, assembly, structure, SRA, BioProject, ...) plus UniProt, RCSB PDB, AlphaFold
  and Europe PMC. Use whenever the user wants to collect, check, search, or export references or bio records, e.g.
  整理文献库, 把这批参考文献核对一下DOI, 核对引用是否真实, 导成能进EndNote或Zotero的库, 直接导入Zotero, 给文献配个分类Excel,
  把每篇文章的重点用中文说明, 整理成带中文重点的Excel,
  搜NCBI/蛋白/序列/结构数据库, "verify these DOIs", "check these citations are real", "export these papers to EndNote",
  "search UniProt/PDB/NCBI", "build me a reference library". Runs the bundled scripts search_papers.py, verify_doi.py,
  export_refs.py, bio_search.py and push_zotero.py; takes optional category themes from a scope_brief.md.
---

# Curate — build a DOI-verified literature library

A reference list is trusted by default in peer review, so a single wrong DOI or fabricated paper does real damage
and is hard to spot later. This stage makes the library trustworthy before it reaches the user's reference
manager. Everything runs from bundled scripts — no other skill is required. Run the steps in order; never skip the
DOI gate or the review gate.

If a `scope_brief.md` exists (from `research-to-paper-scope`), use its core themes as the categories and its angle
to judge relevance. Otherwise infer reasonable categories from the topic and confirm them with the user.

## Step 1 — Search

Run `scripts/search_papers.py "<query>" <papers.json>`. It queries five sources — OpenAlex, Europe PMC, PubMed,
Semantic Scholar, and CrossRef — then merges and de-duplicates by DOI → normalized title, all with stdlib, no
installs, no external skill. If the user already pasted a reference list, skip the search and start from their list.

Then annotate every paper in `papers.json` in ONE pass — edit the file in place; do not call a tool per paper. For
EACH object add these fields:

1. `category` — a string (one scope theme, or an inferred theme). A string, never a list.
2. `key_point_zh` — a string: ONE Chinese sentence giving the paper's core finding or its relevance to this study.
   - Draw it ONLY from that paper's title + abstract. Do not state a result the abstract does not contain.
   - If the abstract is empty or too thin to state a finding, write `摘要缺失/不足，待人工补充` and do NOT infer a
     result from the title alone.
3. *(optional, only when the user wants a scored library)* `innovation_score` (integer 1–10) and
   `innovation_rationale` (one Chinese sentence).

Each annotated object should look like this (keep every field the search produced; just ADD these):

```json
{ "title": "...", "abstract": "...", "doi": "...",
  "category": "极地碳循环", "key_point_zh": "一句中文：该研究的核心发现或与本研究的关联" }
```

The field name must be exactly `key_point_zh`. Write the result as **valid JSON** — a plain array, no ```code
fences, no trailing commas (`verify_doi.py` / `export_refs.py` tolerate a stray fence or comma, but clean JSON is the
contract). `key_point_zh` is a faithful reading aid, not a new claim: keep it short and in Chinese, and state only
what the abstract itself makes explicit — if you mention relevance, it must be a relevance the abstract states, not
one you infer.

For biology **resource** databases (sequences, structures, genes, taxa — not just papers), use
`scripts/bio_search.py <db> "<query>"`: any NCBI Entrez database (protein, nucleotide, gene, taxonomy, assembly,
structure, SRA, BioProject, ...) plus UniProt, RCSB PDB, AlphaFold and Europe PMC. `bio_search.py --list` shows the
interfaces; `--fetch fasta` pulls sequences. Details in `references/bio-sources.md`.

API credentials are optional and read from a `.env` file (see `.env.example` + `references/bio-sources.md`): setting
`CROSSREF_MAILTO` / `NCBI_EMAIL` joins the faster polite pool, and `NCBI_API_KEY` / `S2_API_KEY` raise rate limits.
Nothing here requires a key.

## Step 2 — Verify every DOI

Run this exact command:

```bash
python scripts/verify_doi.py papers.json verified.json
```

It checks every DOI against CrossRef **in parallel** (8 workers; add `--cache cache.json` to skip DOIs seen in a
prior run, or `--no-api` to run offline). For each DOI it confirms the record resolves **and** that CrossRef's title
closely matches the claimed title (blended word + character similarity; a supplied DOI is CONFIRMED only at a strict
**≥ 0.85** bar plus a generic-title guard and a discriminating-token check, so a long title differing by one swapped
strain/species/number cannot pass) — a DOI that resolves to the *wrong* paper is caught, not just a dead one. A
title-search PROPOSAL for a missing/dead/mismatched DOI is offered at a looser **≥ 0.75** bar and is **never trusted**
until the review gate or user confirms it (tagged `candidate` / `mismatch`). Every row gets a `doi_status` of
`verified | candidate | mismatch | dead | no_doi | unverified`, and the script **exits non-zero** when any `mismatch`
or `dead` remains — treat that as blocking. Treat any row that is not `verified` as unresolved until the review gate
or the user confirms it; only a `verified` DOI is exported as a trusted DOI (others travel as a "待人工核对" note).

## Step 3 — Adversarial review gate

Before exporting, spawn 2-3 independent reviewer agents, each with a different lens (existence/fabrication,
DOI-attribution, relevance/categorization). The exact prompts and the pass/fail rule are in
`references/adversarial-review.md`. A paper advances only if no reviewer flags it as fabricated or DOI-mismatched;
off-topic or mis-categorized papers are demoted (kept, marked "needs user confirmation"), not silently dropped.
Show the user a verdict table with a reason for every rejection — the gate informs the user; the user decides.

This gate is where the residual that `verify_doi.py` cannot decide gets resolved — it is not redundant:
- **Title matching has a floor.** The script catches dead DOIs, wrong-paper DOIs, and swapped strain/species/gene/number
  discriminators, but it cannot reliably judge a **translated/transliterated title** (CrossRef in English, the citation in
  中文, or vice versa) or a 1–2-character swap. Any `mismatch`/`candidate`/`unverified` row, and any row whose claimed and
  CrossRef titles are in different languages, must be confirmed here even if the rest looks fine.
- **`key_point_zh` faithfulness is a model judgment, not a script check.** A reviewer must confirm each Chinese key point
  states only what the abstract supports (the script can't verify meaning). A fabricated or over-reaching key point is a
  fabrication finding, same as a bad citation.

## Step 4 — Import or export (branch on credentials)

Two paths, chosen by whether Zotero credentials are present:

- **Direct import to Zotero** — if `ZOTERO_API_KEY` + `ZOTERO_USER_ID` (or `ZOTERO_GROUP_ID`) are set, run
  `scripts/push_zotero.py <verified>`. It creates one Zotero collection per category and pushes the verified items
  straight into the user's library through the Zotero Web API. This writes to their library, so confirm first;
  `--dry-run` previews the payload without posting.
- **Import file** — otherwise (and always for EndNote, which exposes no public item-creation API), run
  `scripts/export_refs.py <verified> <outdir>`. It writes `library.ris` (imports natively into both Zotero and
  EndNote, carrying the 中文重点 as a note), `library.bib` (LaTeX), and `library.xlsx` — a rich, color-coded report
  with one row per paper: 分类 / 标题 / 作者 / 年份 / 期刊 / DOI (hyperlinked) / 核验状态 (colored) / **中文重点** /
  创新评分 / 创新评语 / 影响因子 / 引用数 / 来源 / 摘要, plus a Summary sheet. Re-running **appends** new papers
  (deduped by DOI/title), so the library accumulates across searches instead of being overwritten. Falls back to
  `.csv` if openpyxl is missing (never auto-installs). Tell the user to open `library.xlsx` to read the 中文重点 and
  import `library.ris` into their manager.

## Deliver

Report how many papers passed, how many DOIs were corrected (before/after), and what the reviewers rejected and
why, then point to the three library files. If this was part of the full workflow, pass the verified library to
`research-to-paper-write` together with the `scope_brief.md`.

## Files

- `scripts/search_papers.py` — five-source literature search (OpenAlex + Europe PMC + PubMed + Semantic Scholar + CrossRef).
- `scripts/bio_search.py` — biology resource search: any NCBI Entrez db + UniProt / RCSB PDB / AlphaFold / Europe PMC.
- `scripts/verify_doi.py` — CrossRef DOI cross-verification.
- `scripts/export_refs.py` — RIS + BibTeX + by-category Excel (the no-credentials import file).
- `scripts/push_zotero.py` — direct import into Zotero via its Web API (when credentials are set).
- `scripts/_env.py` — loads optional API credentials from a `.env` file.
- `references/adversarial-review.md` — reviewer-agent prompts, lenses, pass/fail rule.
- `references/bio-sources.md` — every integrated interface + credentials setup.
