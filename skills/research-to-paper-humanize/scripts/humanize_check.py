#!/usr/bin/env python3
"""Quantitative de-AI check for a draft. Measures the signals that distinguish AI prose from human prose
and flags what still needs work. It is a floor, not the goal — passing means the text is no longer obviously
uniform; it does not replace reading the prose aloud.

Checks:
  D1  sentence-length variability — human prose varies (stddev > ~10 for zh chars / ~6 for en words);
      uniform AI prose is flatter.
  D4  connector density — AI text leans on many connectors at paragraph starts; flag > threshold per 1000 chars.
  --  long dash / line separators (runs of 3+) — an AI/decoration tell; academic papers don't use them.
  --  matrix coverage (optional) — if a humanize_matrix.md is given, rows should roughly cover the paragraphs.

Stdlib only. Usage:
  python humanize_check.py <draft.md> [--lang zh|en] [--matrix humanize_matrix.md]
"""
import sys, re, argparse, statistics

MIN_SENT_STDDEV = {"zh": 10.0, "en": 6.0}     # below this = too uniform
MAX_CONNECTOR_PER_1K = 6.0                      # light/medium ceiling
MIN_MATRIX_COVERAGE = 0.5

CONNECTORS = {
    "zh": ["首先", "其次", "再次", "最后", "综上所述", "总而言之", "此外", "另外", "不仅如此",
           "值得注意的是", "需要指出的是", "总的来说", "由此可见", "换句话说", "一方面", "另一方面"],
    "en": ["firstly", "secondly", "thirdly", "moreover", "furthermore", "in addition", "additionally",
           "in conclusion", "to summarize", "it is worth noting", "it is important to note",
           "on the one hand", "on the other hand", "overall"],
}
SENT_SPLIT = {"zh": r"[。！？；…\n]", "en": r"[.!?]\s"}  # 含 … 省略号; 不含 ～(多为数值区间 3～5℃, 非句末)
EN_ABBR = re.compile(r"\b(?:Dr|Mr|Mrs|Ms|Prof|Fig|Eq|No|al|vs|cf|etc|e\.g|i\.e)\.", re.I)


def strip_noise(text):
    """Drop code/LaTeX/markup so we measure prose, not markup."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)       # code fences
    text = re.sub(r"`[^`]*`", " ", text)                     # inline code
    text = re.sub(r"\$[^$]*\$", " ", text)                   # math
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", text)         # md links
    text = re.sub(r"^(#{1,6}\s|>\s|[-*+]\s|\|).*$", " ", text, flags=re.M)  # headings/lists/tables
    return text


def sentences(text, lang):
    if lang == "en":
        text = EN_ABBR.sub(lambda m: m.group(0).replace(".", "\x00"), text)
    parts = re.split(SENT_SPLIT[lang], text)
    if lang == "en":
        parts = [p.replace("\x00", ".") for p in parts]
    return [p.strip() for p in parts if len(p.strip()) >= 2]


def sent_len(s, lang):
    return len(s) if lang == "zh" else len(s.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    ap.add_argument("--matrix", default=None)
    ap.add_argument("--tier", choices=["light", "medium", "heavy"], default="medium")
    a = ap.parse_args()
    max_conn = 4.0 if a.tier == "heavy" else 6.0

    raw = open(a.draft, encoding="utf-8").read()
    prose = strip_noise(raw)
    nchar = len(re.sub(r"\s", "", prose))
    flags, ok = [], []

    # D1 sentence-length variability
    lens = [sent_len(s, a.lang) for s in sentences(prose, a.lang)]
    if len(lens) > 3:
        sd = round(statistics.pstdev(lens), 2)
        short_frac = sum(1 for x in lens if x <= (12 if a.lang == "zh" else 8)) / len(lens)
        thr = MIN_SENT_STDDEV[a.lang]
        (ok if sd >= thr else flags).append(
            f"D1 句长 stddev={sd} (人类>{thr}); 短句占比={short_frac:.0%}"
            + ("" if sd >= thr else " → 太均匀,加长短句对比"))
    # D4 connector density
    if nchar >= 200:
        conn = sum(len(re.findall(re.escape(c), prose, flags=re.I)) for c in CONNECTORS[a.lang])
        dens = round(conn / (nchar / 1000), 2) if nchar else 0
        (ok if dens <= max_conn else flags).append(
            f"D4 连接词密度={dens}/千字 (上限{max_conn})"
            + ("" if dens <= max_conn else " → 删 AI 高频连接词,别放段首"))
    else:
        ok.append("D4 连接词密度: 文本过短(<200字)跳过")
    # dash separators
    dash = len(re.findall(r"—{3,}|-{4,}", prose))
    (ok if dash == 0 else flags).append(
        f"长横线分隔符={dash}" + ("" if dash == 0 else " → 删掉,用空行/标题代替"))
    # matrix coverage
    if a.matrix:
        try:
            mt = open(a.matrix, encoding="utf-8").read()
            rows = sum(1 for l in mt.splitlines() if l.strip().startswith("|")
                       and not set(l.replace("|", "").strip()) <= {"-", ":", " "})
            rows = max(0, rows - 1)  # 假设恰好一行表头
            paras = len([p for p in re.split(r"\n\s*\n", prose) if len(p.strip()) > 40])
            cov = rows / paras if paras else 1.0
            (ok if cov >= MIN_MATRIX_COVERAGE else flags).append(
                f"humanize_matrix 覆盖={cov:.0%} ({rows}行/{paras}段)"
                + ("" if cov >= MIN_MATRIX_COVERAGE else " → 覆盖偏低，已改动的段落都要在矩阵里记一行"))
        except OSError:
            flags.append(f"找不到 matrix: {a.matrix}")

    print(f"=== humanize_check: {a.draft} (lang={a.lang}, ~{nchar}字) ===")
    for x in ok:    print(f"  ✓ {x}")
    for x in flags: print(f"  ✗ {x}")
    print(f"\n{'通过 ✓' if not flags else f'{len(flags)} 项待改 ✗ — 迭代后重跑'}")
    sys.exit(1 if flags else 0)


if __name__ == "__main__":
    main()
