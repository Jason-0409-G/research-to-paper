#!/usr/bin/env python3
"""Self-contained multi-database literature search (no external skill needed).

Queries five sources and merges + de-duplicates by DOI -> normalized title:
  OpenAlex, Europe PMC, PubMed (E-utilities), Semantic Scholar, Crossref.
The first three are free, key-free, and high-coverage, so a query rarely comes back empty even when one
source returns nothing. Output is the JSON the rest of the curate pipeline expects
(title, authors, year, journal, doi, abstract, source). Add `category` later (from the scope themes).

Stdlib only (urllib, json, xml). Be polite: set CROSSREF_MAILTO / NCBI_EMAIL.

Usage: python search_papers.py "<query>" <out.json> [--per-source 25]
"""
import sys, os, json, time, argparse, urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET

try:                                    # optional: load API creds from a .env-style file
    from _env import load_env; load_env()
except Exception:
    pass

MAILTO = os.environ.get("CROSSREF_MAILTO", "research-to-paper@example.com")
UA = {"User-Agent": f"research-to-paper (mailto:{MAILTO})"}
TIMEOUT = 30


def _get(url, tries=3, raw=False, headers=None):
    h = dict(UA)
    if headers:
        h.update(headers)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=TIMEOUT) as r:
                data = r.read().decode("utf-8", "replace")
            return data if raw else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):        # permanent — don't waste retries
                return None
            wait = 2 ** i                             # 429 (rate limit) / 5xx → back off, honor Retry-After
            ra = e.headers.get("Retry-After") if e.headers else None
            if ra:
                try:
                    wait = max(wait, min(int(ra), 10))
                except (TypeError, ValueError):
                    pass
            time.sleep(wait)
        except Exception:
            time.sleep(2 ** i)
    return None


def norm_title(t):
    return "".join(ch.lower() for ch in (t or "") if ch.isalnum() or ch.isspace()).strip()


def clean_doi(d):
    d = (d or "").strip()
    return d.replace("https://doi.org/", "").replace("http://doi.org/", "").lower() if d else ""


# ---- OpenAlex (free, no key, huge coverage) ----
def openalex(q, n):
    key = os.environ.get("OPENALEX_API_KEY", "")
    d = _get(f"https://api.openalex.org/works?search={urllib.parse.quote(q)}"
             f"&per-page={n}&mailto={urllib.parse.quote(MAILTO)}"
             + (f"&api_key={urllib.parse.quote(key)}" if key else ""))
    out = []
    for w in ((d or {}).get("results") or []):
        # abstract is stored as an inverted index {word: [positions]}; rebuild it
        ab = ""
        inv = w.get("abstract_inverted_index")
        if inv:
            try:
                slots = {}
                for word, pos in inv.items():
                    for p in pos:
                        slots[p] = word
                ab = " ".join(slots[i] for i in range(max(slots) + 1) if i in slots)
            except Exception:
                ab = ""
        src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
        out.append(dict(title=w.get("display_name", ""),
                        authors="; ".join((a.get("author") or {}).get("display_name", "")
                                          for a in (w.get("authorships") or [])),
                        year=str(w.get("publication_year") or ""), journal=src,
                        doi=clean_doi(w.get("doi")), abstract=ab, source="OpenAlex"))
    return out


# ---- Europe PMC (free, no key) ----
def europepmc(q, n):
    d = _get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
             f"query={urllib.parse.quote(q)}&format=json&pageSize={n}&resultType=core")
    out = []
    for r in (((d or {}).get("resultList") or {}).get("result") or []):
        out.append(dict(title=r.get("title", ""), authors=r.get("authorString", ""),
                        year=str(r.get("pubYear") or ""),
                        journal=r.get("journalTitle") or ((r.get("journalInfo") or {}).get("journal") or {}).get("title", ""),
                        doi=clean_doi(r.get("doi")), abstract=r.get("abstractText") or "", source="EuropePMC"))
    return out


# ---- PubMed (E-utilities) ----
def pubmed(q, n):
    out, email = [], os.environ.get("NCBI_EMAIL", "")
    key = os.environ.get("NCBI_API_KEY", "")
    auth = ("&tool=research-to-paper"
            + (f"&email={urllib.parse.quote(email)}" if email else "")
            + (f"&api_key={urllib.parse.quote(key)}" if key else ""))
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    ids = _get(f"{base}/esearch.fcgi?db=pubmed&retmax={n}&retmode=json&term={urllib.parse.quote(q)}" + auth)
    idlist = (((ids or {}).get("esearchresult") or {}).get("idlist")) or []
    if not idlist:
        return out
    time.sleep(0.4)
    xml = _get(f"{base}/efetch.fcgi?db=pubmed&retmode=xml&id={','.join(idlist)}" + auth, raw=True)
    try:
        root = ET.fromstring(xml) if xml else None
    except ET.ParseError:
        root = None
    for art in (root.findall(".//PubmedArticle") if root is not None else []):
        te = art.find(".//ArticleTitle")
        doi = next((idn.text.strip() for idn in art.findall(".//ArticleId")
                    if idn.get("IdType") == "doi" and idn.text), "")
        authors = [f"{au.findtext('LastName')}, {au.findtext('ForeName')}".strip(", ")
                   for au in art.findall(".//Author") if au.findtext("LastName")]
        out.append(dict(title="".join(te.itertext()) if te is not None else "",
                        authors="; ".join(authors),
                        year=art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or "",
                        journal=art.findtext(".//Journal/Title") or "",
                        doi=clean_doi(doi),
                        abstract=" ".join("".join(a.itertext()) for a in art.findall(".//AbstractText")),
                        source="PubMed"))
    return out


# ---- Semantic Scholar ----
def semantic_scholar(q, n):
    key = os.environ.get("S2_API_KEY", "")
    d = _get(f"https://api.semanticscholar.org/graph/v1/paper/search?limit={n}"
             f"&fields=title,authors,year,venue,abstract,externalIds&query={urllib.parse.quote(q)}",
             headers={"x-api-key": key} if key else None,
             tries=5 if key else 4)                   # S2's shared pool throttles hardest; give it more tries
    out = []
    for p in ((d or {}).get("data") or []):
        out.append(dict(title=p.get("title", ""),
                        authors="; ".join(a.get("name", "") for a in (p.get("authors") or [])),
                        year=str(p.get("year") or ""), journal=p.get("venue", ""),
                        doi=clean_doi((p.get("externalIds") or {}).get("DOI")),
                        abstract=p.get("abstract") or "", source="SemanticScholar"))
    return out


# ---- Crossref ----
def crossref(q, n):
    d = _get(f"https://api.crossref.org/works?rows={n}&mailto={urllib.parse.quote(MAILTO)}"
             f"&query.bibliographic={urllib.parse.quote(q)}")
    out = []
    for it in (((d or {}).get("message") or {}).get("items") or []):
        year = ""
        for k in ("published-print", "published-online", "issued"):
            dp = (it.get(k) or {}).get("date-parts")
            if dp and dp[0]:
                year = str(dp[0][0]); break
        out.append(dict(title=(it.get("title") or [""])[0],
                        authors="; ".join(f"{a.get('family','')}, {a.get('given','')}".strip(", ")
                                          for a in (it.get("author") or [])),
                        year=year, journal=(it.get("container-title") or [""])[0],
                        doi=clean_doi(it.get("DOI")), abstract=it.get("abstract", ""), source="Crossref"))
    return out


def _norm(rec):
    for k in ("title", "authors", "year", "journal", "doi", "abstract", "source"):
        if rec.get(k) is None:
            rec[k] = ""
    return rec


def merge(lists):
    by_key, order = {}, []
    for src in lists:
        for p in src:
            if not p.get("title"):
                continue
            key = p.get("doi") or norm_title(p.get("title"))
            if key in by_key:
                ex = by_key[key]
                ex["source"] = ",".join(sorted(set(ex["source"].split(",") + p["source"].split(","))))
                for f in ("abstract", "doi", "journal", "authors"):   # keep the fuller value
                    if len(p.get(f) or "") > len(ex.get(f) or ""):
                        ex[f] = p.get(f) or ""
            else:
                by_key[key] = _norm(dict(p)); order.append(key)
    return [by_key[k] for k in order]


SOURCES = [("OpenAlex", openalex), ("EuropePMC", europepmc), ("PubMed", pubmed),
           ("SemanticScholar", semantic_scholar), ("Crossref", crossref)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query"); ap.add_argument("outfile")
    ap.add_argument("--per-source", type=int, default=25)
    a = ap.parse_args()
    print(f"[search] '{a.query}' · 每源 {a.per_source} 篇 · " + " + ".join(n for n, _ in SOURCES))
    results = []
    for name, fn in SOURCES:
        try:
            r = fn(a.query, a.per_source)
        except Exception as e:
            r = []; print(f"  {name} 出错: {e}")
        print(f"  {name} {len(r)}")
        results.append(r); time.sleep(0.4)
    s2n = next((len(r) for (nm, _), r in zip(SOURCES, results) if nm == "SemanticScholar"), 0)
    if s2n == 0 and not os.environ.get("S2_API_KEY"):
        print("[search] 提示: Semantic Scholar 返回 0,多半是免 key 共享池被限速;设 S2_API_KEY(免费)可拿专属限额,其余四源已兜底")
    merged = merge(results)
    json.dump(merged, open(a.outfile, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[search] 合并去重 → {len(merged)} 篇 → {a.outfile}")
    if not merged:
        print("[search] ⚠ 五源都为空: 换更宽的关键词, 或检查网络")
    print("[search] 下一步: 加 category(按 scope 主题)→ verify_doi.py → 对抗审 → export_refs.py")


if __name__ == "__main__":
    main()
