#!/usr/bin/env python3
"""corpus/ 配下の SKILL.md を測定して構造の統計を出す。

使い方: ./scripts/collect-corpus.sh && ./scripts/analyze-corpus.py
"""
import os, re, json, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "corpus"
SRC = {
 "anthropics_skills":"Anthropic(公式)","obra_superpowers":"obra/superpowers",
 "cloudflare_skills":"Cloudflare","vercel-labs_skills":"Vercel",
 "google_skills":"Google","phuryn_pm-skills":"PM skills",
 "coreyhaines31_marketingskills":"Marketing",
}

def parse_front(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1: return {}, text
    raw, body = text[3:end], text[end+4:]
    out, key = {}, None
    for line in raw.splitlines():
        m = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1); out[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")):
            out[key] += " " + line.strip()
    return out, body

EXCL = re.compile(r"\b(not|don'?t|never|avoid|instead of|rather than|unless|except|do not)\b", re.I)
TRIGGER = re.compile(r"\b(use when|when the user|when you|triggers? on|invoke when|for when)\b", re.I)

rows=[]
for repo, label in SRC.items():
    for p in (ROOT/repo).rglob("SKILL.md"):
        text = p.read_text(errors="replace")
        fm, body = parse_front(text)
        name = fm.get("name","")
        desc = fm.get("description","")
        d = p.parent
        lines = body.count("\n")+1
        rows.append(dict(
            src=label, name=name or d.name, dir=d.name,
            name_match = (name == d.name),
            desc_words = len(desc.split()),
            desc_chars = len(desc),
            has_excl = bool(EXCL.search(desc)),
            has_trigger = bool(TRIGGER.search(desc)),
            body_lines = lines,
            refs = (d/"references").is_dir(),
            scripts = (d/"scripts").is_dir(),
            assets = (d/"assets").is_dir(),
            h2 = len(re.findall(r"^## ", body, re.M)),
            code_blocks = body.count("```")//2,
            tables = len(re.findall(r"^\|", body, re.M))>0,
            extra_fm = sorted(k for k in fm if k not in ("name","description")),
        ))

def med(xs): return st.median(xs) if xs else 0
print(f"総数 {len(rows)}\n")

print("== 提供元別 ==")
print(f"{'提供元':22}{'数':>4}{'desc語数(中央)':>14}{'本文行(中央)':>13}{'除外句%':>9}{'トリガ句%':>10}{'refs%':>7}{'scripts%':>9}")
for label in dict.fromkeys(SRC.values()):
    g=[r for r in rows if r["src"]==label]
    if not g: continue
    n=len(g)
    print(f"{label:22}{n:>4}{med([r['desc_words'] for r in g]):>14}{med([r['body_lines'] for r in g]):>13}"
          f"{100*sum(r['has_excl'] for r in g)//n:>8}%{100*sum(r['has_trigger'] for r in g)//n:>9}%"
          f"{100*sum(r['refs'] for r in g)//n:>6}%{100*sum(r['scripts'] for r in g)//n:>8}%")

n=len(rows)
print("\n== 全体 ==")
print(f"desc 語数  中央値 {med([r['desc_words'] for r in rows])}  平均 {sum(r['desc_words'] for r in rows)//n}  最小 {min(r['desc_words'] for r in rows)}  最大 {max(r['desc_words'] for r in rows)}")
print(f"name とディレクトリ名が一致: {sum(r['name_match'] for r in rows)}/{n}")
print(f"description に除外句あり: {100*sum(r['has_excl'] for r in rows)//n}%")
print(f"description に明示トリガ句(Use when 等)あり: {100*sum(r['has_trigger'] for r in rows)//n}%")
print(f"コードブロックあり: {100*sum(r['code_blocks']>0 for r in rows)//n}%  (中央 {med([r['code_blocks'] for r in rows])}個)")
print(f"表あり: {100*sum(r['tables'] for r in rows)//n}%")
print(f"H2見出し 中央値 {med([r['h2'] for r in rows])}")

from collections import Counter
c=Counter(k for r in rows for k in r["extra_fm"])
print("\n== frontmatter の追加フィールド ==")
for k,v in c.most_common(10): print(f"  {k:24}{v}")

print("\n== desc 語数の分布 ==")
b=Counter()
for r in rows:
    w=r['desc_words']
    b["  1-20語" if w<21 else "  21-40語" if w<41 else "  41-60語" if w<61 else "  61-100語" if w<101 else "  101語以上"]+=1
for k in ["  1-20語","  21-40語","  41-60語","  61-100語","  101語以上"]:
    print(f"{k:12}{b[k]:>4}  {'█'*(b[k]//4)}")
json.dump(rows, open(Path(__file__).resolve().parent.parent / "corpus" / "rows.json", "w"), ensure_ascii=False)
