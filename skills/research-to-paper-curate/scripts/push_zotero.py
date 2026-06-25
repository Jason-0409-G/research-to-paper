#!/usr/bin/env python3
"""Push verified references straight into a Zotero library via the Zotero Web API v3.

The branch this implements: if the user has Zotero API credentials, categorize and import the
references DIRECTLY (one Zotero collection per category); if they do NOT, the caller falls back to
export_refs.py, which writes library.ris for the user to import by hand.

Credentials (from the environment or a .env file via _env.py):
  ZOTERO_API_KEY   - https://www.zotero.org/settings/keys  (needs write access)
  ZOTERO_USER_ID   - your numeric userID (same settings page)         [personal library]
  ZOTERO_GROUP_ID  - a group library id, INSTEAD of ZOTERO_USER_ID    [shared library]

Note on EndNote: EndNote exposes no public item-creation API, so there is no equivalent direct
push — export_refs.py writes a .ris that EndNote imports natively (File > Import). Stdlib only.

Usage:  python push_zotero.py <verified.json>            # creds from env/.env
        python push_zotero.py <verified.json> --dry-run  # build payloads, do not POST
"""
from __future__ import annotations
import sys, os, re, json, time, argparse, urllib.request, urllib.parse, urllib.error

try:
    from _env import load_env; load_env()
except Exception:
    pass

API = "https://api.zotero.org"
HDR = {"Zotero-API-Version": "3", "Content-Type": "application/json"}


def cat_of(r):
    """Category as a hashable string — a weak model may emit it as a list (unhashable as a set/dict key)."""
    c = r.get("category") or "Uncategorized"
    if isinstance(c, list):
        c = ", ".join(map(str, c)) or "Uncategorized"
    return str(c)


def keypoint_of(r):
    """The model's one-line Chinese key point, under any plausible field name."""
    for k, v in r.items():
        if isinstance(v, str) and v.strip() and re.search(
                r"(?:key[_\s-]?point|keypoint)[_\s-]?(?:zh|cn|chinese)"
                r"|(?:zh|cn|chinese)[_\s-]?(?:key[_\s-]?point|keypoint)"
                r"|cn[_\s-]?(?:summary|keypoint|key[_\s-]?point)|key[_\s-]?point[_\s-]?zh", k, re.I):
            return v.strip()
    return ""


def have_credentials():
    return bool(os.environ.get("ZOTERO_API_KEY") and
                (os.environ.get("ZOTERO_USER_ID") or os.environ.get("ZOTERO_GROUP_ID")))


def _base():
    uid, gid = os.environ.get("ZOTERO_USER_ID"), os.environ.get("ZOTERO_GROUP_ID")
    if gid:
        return f"{API}/groups/{gid}"
    return f"{API}/users/{uid}"


def _req(method, url, key, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(HDR); h["Zotero-API-Key"] = key
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8", "replace")
    return json.loads(raw) if raw else {}


def creators(authors):
    """Turn authors (a list, or an 'A, B; C D' string) into Zotero creator dicts."""
    out = []
    if isinstance(authors, list):
        parts = [str(x) for x in authors if x]
    else:
        authors = authors or ""
        parts = authors.split(";") if ";" in authors else ([authors] if authors else [])
    for a in parts:
        a = (a or "").strip()
        if not a:
            continue
        if "," in a:
            last, first = a.split(",", 1)
        else:
            toks = a.split()
            if len(toks) > 1 and re.fullmatch(r"(?:[A-Z]\.?){1,3}", toks[-1]):
                last, first = toks[0], " ".join(toks[1:])         # 'Smith J' → Smith, J (not J, Smith)
            elif len(toks) > 1:
                last, first = toks[-1], " ".join(toks[:-1])
            else:
                last, first = a, ""
        out.append({"creatorType": "author", "firstName": first.strip(), "lastName": last.strip()})
    return out


def make_item(rec, collection_keys):
    verified = rec.get("doi_status") == "verified"
    doi = (rec.get("verified_doi") or rec.get("doi") or "").strip()
    extra = []
    kp = keypoint_of(rec)
    if kp:
        extra.append(f"中文重点: {kp}")
    if doi and not verified:                                       # an unconfirmed DOI never enters the trusted DOI field
        extra.append(f"DOI待人工核对({rec.get('doi_status', '未核验')}): {doi}")
    return {
        "itemType": "journalArticle",
        "title": rec.get("title", ""),
        "creators": creators(rec.get("authors", "")),
        "date": str(rec.get("year", "")),
        "publicationTitle": rec.get("journal", ""),
        "DOI": doi if verified else "",                           # only a CONFIRMED DOI
        "abstractNote": rec.get("abstract", ""),
        "extra": "\n".join(extra),
        "collections": collection_keys,
    }


def ensure_collections(base, key, categories):
    """Return {category: collectionKey}, creating any that don't already exist."""
    existing = {}
    try:
        start = 0
        while True:                                   # paginate: Zotero caps at 100 per page
            page = _req("GET", f"{base}/collections?limit=100&start={start}", key)
            if not page:
                break
            for c in page:
                existing[c["data"]["name"]] = c["key"]
            if len(page) < 100:
                break
            start += 100
    except urllib.error.HTTPError:
        pass
    mapping, to_create = {}, []
    for cat in categories:
        if cat in existing:
            mapping[cat] = existing[cat]
        else:
            to_create.append(cat)
    for i in range(0, len(to_create), 50):
        batch = [{"name": c} for c in to_create[i:i + 50]]
        resp = _req("POST", f"{base}/collections", key, batch)
        for idx, ckey in (resp.get("successful") or {}).items():
            mapping[batch[int(idx)]["name"]] = ckey["key"] if isinstance(ckey, dict) else ckey
        time.sleep(0.2)
    return mapping


def push(records, dry_run=False):
    key = os.environ.get("ZOTERO_API_KEY", "")
    base = _base()
    cats = sorted({cat_of(r) for r in records})
    coll = {} if dry_run else ensure_collections(base, key, cats)
    items = [make_item(r, [coll.get(cat_of(r), "")] if not dry_run else [])
             for r in records]
    if dry_run:
        return {"dry_run": True, "items": len(items), "categories": cats, "sample": items[:2]}
    created, failed = 0, 0
    for i in range(0, len(items), 50):                       # Zotero accepts <=50 items per write
        resp = _req("POST", f"{base}/items", key, items[i:i + 50])
        created += len(resp.get("successful") or {})
        failed += len(resp.get("failed") or {})
        time.sleep(0.3)
    return {"created": created, "failed": failed, "collections": list(coll)}


def main():
    ap = argparse.ArgumentParser(description="Push verified references into Zotero (direct import).")
    ap.add_argument("verified", help="verified.json from verify_doi.py (+ category per record)")
    ap.add_argument("--dry-run", action="store_true", help="build payloads without POSTing")
    a = ap.parse_args()

    if not have_credentials() and not a.dry_run:
        print("[zotero] 未配置 ZOTERO_API_KEY + ZOTERO_USER_ID/ZOTERO_GROUP_ID", file=sys.stderr)
        print("[zotero] → 改用 export_refs.py 生成 library.ris 供手动导入", file=sys.stderr)
        return 3
    records = json.load(open(a.verified, encoding="utf-8"))
    try:
        res = push(records, dry_run=a.dry_run)
    except urllib.error.HTTPError as e:
        # key 无写权限 / 载荷被拒等 → 不崩溃,退回文件导入(调用方改跑 export_refs.py)
        print(f"[zotero] 写入失败 (HTTP {e.code}) — 多半是 key 无写权限或载荷被拒", file=sys.stderr)
        print("[zotero] → 改用 export_refs.py 生成 library.ris 供手动导入", file=sys.stderr)
        return 3
    except urllib.error.URLError as e:
        print(f"[zotero] 网络错误: {e.reason} → 改用 export_refs.py", file=sys.stderr)
        return 3
    if a.dry_run:
        print(f"[zotero] dry-run: {res['items']} 条 · 分类 {res['categories']}")
    else:
        print(f"[zotero] 已导入 {res['created']} 条 (失败 {res['failed']}) · 集合: {', '.join(res['collections'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
