#!/usr/bin/env python3
"""Cross-verify each paper's DOI against CrossRef.

Why this exists: a DOI can be (a) missing, (b) dead (resolves to nothing), or
(c) the worst case — resolvable but pointing at the WRONG paper (a transposed or
fabricated DOI). Only (b) is caught by a naive "does it resolve" check; (c) silently
corrupts a bibliography. This script catches all three by comparing the title CrossRef
returns for the DOI against the title we claimed, and by searching CrossRef by title to
propose the correct DOI when ours is missing/dead/mismatched.

Stdlib only (urllib, json, csv, difflib) so it runs anywhere without installs.

Input  : papers file (.json array of objects, or .tsv/.csv with a header row).
         Recognized fields/columns: title, doi, authors, year, journal, category, abstract.
Output : same rows + appended fields:
         doi_status   verified | mismatch | dead | candidate | no_doi
         verified_doi the confirmed-correct DOI (or a proposed candidate)
         cr_title     the title CrossRef returned (for the verified/candidate DOI)
         title_sim    0..1 similarity between claimed and CrossRef title

Usage: python verify_doi.py <papers.json|tsv|csv> <out.json|tsv|csv> [--mailto you@uni.edu]
       (mailto also read from $CROSSREF_MAILTO; CrossRef's "polite pool" is faster/kinder.)
"""
import sys, os, re, json, csv, time, argparse, threading, urllib.request, urllib.parse, urllib.error
import concurrent.futures as cf
from difflib import SequenceMatcher

try:                                    # optional: load API creds from a .env-style file
    from _env import load_env; load_env()
except Exception:
    pass

CR_WORK = "https://api.crossref.org/works/"
CR_QUERY = "https://api.crossref.org/works"
# Two bars, on purpose. CONFIRMING a user-supplied DOI is safety-critical (a wrong-but-resolving
# DOI is the dangerous case), so it needs a STRICT bar — a single content-word swap ("marine" vs
# "soil" bacteria) blends to ~0.78, which must NOT count as the same paper. Merely PROPOSING a DOI
# from a title search is lower-stakes (it still goes to the review gate), so it uses a looser bar.
SIM_VERIFIED = 0.85    # confirm a supplied DOI only when its title this-closely matches ours
SIM_PROPOSE = 0.75     # accept a title-search-proposed DOI at this bar (still routed to review)
MIN_TITLE_WORDS = 4    # a Latin title shorter than this is too generic to trust on similarity alone
THROTTLE = 0.2         # seconds between a worker's requests (bounded concurrency keeps us in the polite pool)
TIMEOUT = 25
UNREACHABLE = object()  # sentinel: transient failure (429/5xx) — NOT a dead DOI


def norm(s):
    return " ".join((s or "").lower().split())


def _words(s):
    # Unicode-aware: keep CJK/Greek/Cyrillic word chars so a correct non-Latin title still
    # scores a real similarity (a stripped-to-ASCII title would score 0.0 and falsely "mismatch").
    return re.sub(r"[^\w]+", " ", norm(s), flags=re.UNICODE).split()


def sim(a, b):
    """Blended word-Jaccard (0.5) + char-sequence ratio (0.5).

    Pure SequenceMatcher over-penalizes reordered/abbreviated titles and
    under-penalizes shared boilerplate; the blend (paper-spine's gate) is the
    more reliable "is this the same paper" signal. 0..1, higher = more similar.
    """
    aw, bw = _words(a), _words(b)
    if not aw or not bw:
        return 0.0
    sa, sb = set(aw), set(bw)
    jac = len(sa & sb) / len(sa | sb)
    seq = SequenceMatcher(None, " ".join(aw), " ".join(bw)).ratio()
    return round(jac * 0.5 + seq * 0.5, 3)


def _specific_enough(a, b):
    """True only if BOTH titles carry enough signal to trust a similarity match.

    Generic one/two-word titles ('Krill', 'Editorial', 'Data') hit Jaccard 1.0 against any
    same-word record, which would auto-verify a fabricated DOI. Latin titles need >= a few
    content words; CJK titles (no spaces, so few 'words') are judged by character length.
    """
    def signal(s):
        n = norm(s)
        # no-space scripts (CJK ideographs, kana, Hangul) → judge by character length, not word count
        if any(("一" <= ch <= "鿿") or ("぀" <= ch <= "ヿ") or ("가" <= ch <= "힣") for ch in n):
            return len(n.replace(" ", "")) >= 8
        return len(_words(s)) >= MIN_TITLE_WORDS
    return signal(a) and signal(b)


STOPWORDS = {"the", "a", "an", "of", "and", "or", "in", "on", "for", "to", "with",
             "by", "from", "de", "la", "le", "des", "und", "von", "el", "und"}


def _content(s):
    return [t for t in _words(s) if t not in STOPWORDS]


def _near(t, words):
    """t has a near-match among words — tolerates morphological drift (acid≈acids,
    transcription≈transcriptional) but NOT a swap (bgla↛bglb, transcriptome↛transcription)."""
    for w in words:
        if t == w:
            return True
        if len(t) >= 4 and len(w) >= 4 and (t.startswith(w) or w.startswith(t)):
            return True
    return False


def _discriminators_ok(a, b):
    """True only if neither title swaps a discriminating token the other can't account for.

    Blended similarity rates a long title differing by ONE swapped strain / species / gene / number
    ("...vesiculosa strain L5" vs "...M7", "bglA" vs "bglB") as the same paper (~0.87 > the verified
    bar), which would CONFIRM a wrong-paper DOI — the exact prime-directive failure. This guard blocks
    it: number tokens (strain ids, years) must match EXACTLY, and every >=3-char content word of the
    shorter title must have a near-match in the longer one. Near-match tolerates a dropped subtitle
    and morphological drift (acid≈acids); a swapped epithet/gene/strain (vesiculosa↛livingstonensis,
    bglA↛bglB) has none, so it fails. The 3-char floor reaches short gene/locus codes; below it a few
    1-2 char swaps (roman numerals) remain the review gate's job. Verify-confirm path only."""
    ca, cb = _content(a), _content(b)
    sca, scb = set(ca), set(cb)
    diga = {t for t in sca if any(c.isdigit() for c in t)}
    digb = {t for t in scb if any(c.isdigit() for c in t)}
    if diga != digb:
        return False
    short, long_ = (sca, scb) if len(ca) <= len(cb) else (scb, sca)
    for t in short:
        if len(t) >= 3 and not any(c.isdigit() for c in t) and not _near(t, long_):
            return False
    return True


def _get(url, mailto, tries=3):
    """GET JSON with polite-pool mailto + light retry. Returns dict or None."""
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}mailto={urllib.parse.quote(mailto)}"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"research-to-paper (mailto:{mailto})"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None          # dead DOI / no record
            wait = 2 ** i
            ra = e.headers.get("Retry-After") if e.headers else None
            try:
                wait = max(wait, min(int(ra), 60))
            except (TypeError, ValueError):
                pass
            if i < tries - 1:                       # don't sleep after the final, give-up attempt
                time.sleep(wait)
        except Exception:
            if i < tries - 1:
                time.sleep(2 ** i)
    return UNREACHABLE             # exhausted on transient errors — not dead


def cr_title_of(msg):
    t = (msg or {}).get("title") or []
    return t[0] if t else ""


def lookup_doi(doi, mailto):
    """Return (cr_title, ok, reachable) for a DOI.

    ok=False means not verified; reachable=False means CrossRef was never
    reached (transient 429/5xx) so the DOI must NOT be called dead.
    """
    if not doi:
        return "", False, True
    data = _get(CR_WORK + urllib.parse.quote(doi.strip()), mailto)
    if data is UNREACHABLE:
        return "", False, False
    if not data or "message" not in data:
        return "", False, True
    return cr_title_of(data["message"]), True, True


def search_title(title, mailto):
    """Search CrossRef by title; return (best_doi, best_title, similarity)."""
    if not title:
        return "", "", 0.0
    url = f"{CR_QUERY}?query.bibliographic={urllib.parse.quote(title)}&rows=3"
    data = _get(url, mailto)
    items = ((data or {}).get("message") or {}).get("items") or []
    best = ("", "", 0.0)
    for it in items:
        ct = cr_title_of(it)
        s = sim(title, ct)
        if s > best[2]:
            best = (it.get("DOI", ""), ct, s)
    return best


def _cached_lookup(doi, mailto, cache, lock):
    """lookup_doi() with a {doi: [cr_title, ok, reachable]} cache. Caches only the RAW CrossRef
    result for the DOI — never a per-row verdict — so two different papers that share one DOI (a
    copy-paste error this tool exists to catch) are each scored against THEIR OWN title."""
    key = (doi or "").strip().lower()
    if cache is not None and lock is not None and key:
        with lock:
            ent = cache.get(key)
        if isinstance(ent, list) and len(ent) == 3:
            return ent[0], ent[1], ent[2]
    res = lookup_doi(doi, mailto)
    if cache is not None and lock is not None and key:
        with lock:
            cache[key] = list(res)
    return res


def classify(row, mailto, cache=None, lock=None):
    """Decide doi_status + verified_doi + cr_title + title_sim for one paper.

    cr_title/title_sim always describe the SAME record as verified_doi (the supplied DOI on
    'verified', the proposal on 'mismatch'/'candidate', blank when nothing was accepted)."""
    title = row.get("title", "")
    doi = (row.get("doi", "") or "").strip()

    def propose(t):
        bdoi, bct, bs = search_title(t, mailto); time.sleep(THROTTLE)
        # the same discriminating-token guard applies to a proposal, so a candidate DOI can't point
        # at a near-title with a swapped strain/gene/number either
        if bdoi and bs >= SIM_PROPOSE and _specific_enough(t, bct) and _discriminators_ok(t, bct):
            return bdoi, bct, bs
        return "", "", 0.0                       # reject cleanly — never surface a non-accepted title

    if doi:
        ct, ok, reachable = _cached_lookup(doi, mailto, cache, lock)
        time.sleep(THROTTLE)
        if ok:
            s = sim(title, ct)
            # CONFIRM only at the strict bar, with a specificity floor AND a discriminating-token
            # guard so a single swapped strain/species/number on a long title can't pass as verified.
            if s >= SIM_VERIFIED and _specific_enough(title, ct) and _discriminators_ok(title, ct):
                return dict(doi_status="verified", verified_doi=doi, cr_title=ct, title_sim=s)
            pdoi, pct, ps = propose(title)       # wrong paper / swapped discriminator / too generic → propose
            return dict(doi_status="mismatch", verified_doi=pdoi, cr_title=pct, title_sim=ps)
        status = "dead" if reachable else "unverified"
        pdoi, pct, ps = propose(title)
        return dict(doi_status=status, verified_doi=pdoi, cr_title=pct, title_sim=ps)
    pdoi, pct, ps = propose(title)               # no DOI → propose one from a title search
    if pdoi:
        return dict(doi_status="candidate", verified_doi=pdoi, cr_title=pct, title_sim=ps)
    return dict(doi_status="no_doi", verified_doi="", cr_title="", title_sim=0.0)


def classify_noapi(row):
    """Offline structural pass (no network): only distinguishes has-DOI from no-DOI.
    Lets the whole curate step run in CI / offline without hitting CrossRef."""
    doi = (row.get("doi", "") or "").strip()
    return dict(doi_status=("unverified" if doi else "no_doi"),
                verified_doi=doi, cr_title="", title_sim=0.0)


def cached_classify(row, mailto, cache, lock, no_api):
    """One paper's verdict. The DOI→CrossRef lookup is cached (see _cached_lookup) so duplicate
    DOIs don't re-hit the network, while the title comparison is ALWAYS recomputed against THIS
    row's title — a paper sharing another's DOI is never handed the other's verdict."""
    if no_api:
        return classify_noapi(row)
    res = classify(row, mailto, cache, lock)
    return res


def crossref_batch(dois, mailto):
    """One CrossRef request for many DOIs (filter=doi:A,doi:B,...). Returns {doi_lower: cr_title},
    or None if the request itself failed (so a transient failure isn't mislabeled as 'dead').
    Collapses per-call latency — the big win on a high-latency link (e.g. from China)."""
    flt = ",".join("doi:" + d.strip() for d in dois if d.strip())
    if not flt:
        return {}
    url = f"{CR_QUERY}?filter={urllib.parse.quote(flt, safe=':,/()')}&rows={len(dois)}&select=DOI,title"
    data = _get(url, mailto)
    if data is UNREACHABLE or not data or "message" not in data:
        return None
    out = {}
    for it in (data["message"].get("items") or []):
        d = (it.get("DOI") or "").strip().lower()
        if d:
            out[d] = cr_title_of(it)
    return out


def run_batch(rows, mailto, batch_size, workers):
    """Batch-verify supplied DOIs (one request per chunk), then resolve the non-verified minority
    (mismatch / dead / no-DOI) with parallel title searches. Same verdict semantics + output schema
    as the per-DOI path, but the supplied-DOI latency is paid once per chunk instead of per paper."""
    results = [None] * len(rows)
    have = [(i, d) for i, r in enumerate(rows) for d in [(r.get("doi", "") or "").strip()] if d]
    need = []                                          # rows still needing a title-search proposal

    for k in range(0, len(have), batch_size):          # Pass 1 — batched DOI lookups
        chunk = have[k:k + batch_size]
        meta = crossref_batch([d for _, d in chunk], mailto)
        time.sleep(THROTTLE)
        for i, d in chunk:
            title = rows[i].get("title", "")
            if meta is None:                           # batch request failed → not 'dead', just unverified
                results[i] = dict(doi_status="unverified", verified_doi=d, cr_title="", title_sim=0.0)
                continue
            cr = meta.get(d.lower())
            if cr is None:                             # DOI absent from CrossRef → dead
                results[i] = dict(doi_status="dead", verified_doi="", cr_title="", title_sim=0.0)
                need.append(i)
            else:
                s = sim(title, cr)
                if s >= SIM_VERIFIED and _specific_enough(title, cr) and _discriminators_ok(title, cr):
                    results[i] = dict(doi_status="verified", verified_doi=d, cr_title=cr, title_sim=s)
                else:
                    results[i] = dict(doi_status="mismatch", verified_doi="", cr_title="", title_sim=0.0)
                    need.append(i)

    nodoi = [i for i, r in enumerate(rows) if not (r.get("doi", "") or "").strip()]

    def propose_row(i, base):                          # Pass 2 — parallel proposals for the minority
        title = rows[i].get("title", "")
        bdoi, bct, bs = search_title(title, mailto); time.sleep(THROTTLE)
        ok = bool(bdoi) and bs >= SIM_PROPOSE and _specific_enough(title, bct) and _discriminators_ok(title, bct)
        st = "candidate" if (base == "no_doi" and ok) else base
        return dict(doi_status=st, verified_doi=(bdoi if ok else ""), cr_title=bct, title_sim=bs)

    jobs = [(i, results[i]["doi_status"]) for i in need] + [(i, "no_doi") for i in nodoi]
    if jobs:
        with cf.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            futs = {ex.submit(propose_row, i, base): i for i, base in jobs}
            for fut in cf.as_completed(futs):
                results[futs[fut]] = fut.result()
    return results


# ---- IO: support .json array or .tsv/.csv with header ----
def loads_lenient(text):
    """Parse JSON tolerantly — a weak model (e.g. a DeepSeek-flash subagent) often wraps its
    JSON in ```json fences or leaves a trailing comma. Strip those rather than crash the run."""
    t = text.strip()
    t = re.sub(r"^```[A-Za-z0-9]*\s*", "", t)
    t = re.sub(r"\s*```$", "", t).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return json.loads(re.sub(r",(\s*[}\]])", r"\1", t))   # drop trailing commas, retry once


def read_rows(path):
    if path.lower().endswith(".json"):
        data = loads_lenient(open(path, encoding="utf-8").read())
        return data if isinstance(data, list) else data.get("papers", [])
    delim = "\t" if path.lower().endswith(".tsv") else ","
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f, delimiter=delim)]


def write_rows(path, rows):
    if path.lower().endswith(".json"):
        json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return
    if not path.lower().endswith((".tsv", ".csv")):    # don't write CSV bytes under a .xlsx/other name
        sys.exit(f"[verify_doi] 输出扩展名须为 .json / .tsv / .csv（收到 {path}）")
    delim = "\t" if path.lower().endswith(".tsv") else ","
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=delim)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile"); ap.add_argument("outfile")
    ap.add_argument("--mailto", default=os.environ.get("CROSSREF_MAILTO", "research-to-paper@example.com"))
    ap.add_argument("--workers", type=int, default=8,
                    help="concurrent CrossRef lookups (default 8; the polite pool tolerates this)")
    ap.add_argument("--cache", default="",
                    help="optional JSON cache path; skips re-querying DOIs/titles seen in a prior run")
    ap.add_argument("--no-api", action="store_true",
                    help="offline: skip CrossRef, only mark has-DOI vs no-DOI (CI / no network)")
    ap.add_argument("--batch", action="store_true",
                    help="batch-verify supplied DOIs (one CrossRef request per chunk) — much faster on a high-latency link (e.g. from China)")
    ap.add_argument("--batch-size", type=int, default=25, help="DOIs per batched request (default 25)")
    a = ap.parse_args()

    rows = read_rows(a.infile)
    if not rows:
        sys.exit("[verify_doi] 输入为空 / empty input")

    cache, lock = {}, threading.Lock()
    if a.cache and os.path.isfile(a.cache):
        try:
            cache = json.load(open(a.cache, encoding="utf-8"))
        except Exception:
            cache = {}

    mode = ("offline (--no-api)" if a.no_api else
            f"CrossRef batch (size {a.batch_size}) + {a.workers} workers for proposals" if a.batch else
            f"CrossRef polite pool mailto={a.mailto} · {a.workers} workers")
    print(f"[verify_doi] {len(rows)} 篇 · {mode}")

    # Verify concurrently — each paper makes 1-3 CrossRef calls, so this is I/O bound;
    # a bounded thread pool turns minutes of sequential throttling into seconds while
    # staying inside CrossRef's polite-pool rate. Results re-aligned to input order.
    counts, results = {}, [None] * len(rows)
    workers = 1 if a.no_api else max(1, a.workers)
    if a.batch and not a.no_api:
        results = run_batch(rows, a.mailto, max(1, a.batch_size), workers)
        for res in results:
            counts[res["doi_status"]] = counts.get(res["doi_status"], 0) + 1
        print(f"  批量核完 {len(rows)} 篇 · 统计 {counts}")
    else:
        done = 0
        with cf.ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(cached_classify, r, a.mailto, cache, lock, a.no_api): i
                    for i, r in enumerate(rows)}
            for fut in cf.as_completed(futs):
                i = futs[fut]
                res = fut.result()
                results[i] = res
                done += 1
                counts[res["doi_status"]] = counts.get(res["doi_status"], 0) + 1
                flag = "" if res["doi_status"] == "verified" else "  <-- 需人工确认 review"
                print(f"  [{done}/{len(rows)}] {res['doi_status']:9} sim={res['title_sim']}  "
                      f"{(rows[i].get('title', '') or '')[:60]}{flag}")

    for r, res in zip(rows, results):
        r.update(res)
    write_rows(a.outfile, rows)

    if a.cache:
        try:
            json.dump(cache, open(a.cache, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass

    print(f"\n[verify_doi] 写出 → {a.outfile}")
    print(f"[verify_doi] 统计: {counts}")
    bad = sum(v for k, v in counts.items() if k != "verified")
    if bad:
        print(f"[verify_doi] ⚠ {bad} 篇非 verified(mismatch/dead/candidate/no_doi/unverified)→ 进对抗审查门,勿直接导入")
    # Exit code as a loop signal (paper-spine pattern): the *dangerous* states — a DOI that
    # resolves to the wrong paper (mismatch) or a dead DOI — fail the run so an orchestrator
    # can route back automatically. candidate/no_doi/unverified are "needs review", not failures.
    dangerous = counts.get("mismatch", 0) + counts.get("dead", 0)
    return 1 if dangerous else 0


if __name__ == "__main__":
    raise SystemExit(main())
