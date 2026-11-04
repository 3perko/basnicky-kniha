#!/usr/bin/env python3
"""Zostaví davka_K_vN.md zo zdrojového súboru davky/zdroj_K_vN.txt.

Formát zdroja:
### 01 | JAHODOVÁ | hádanka | T | trochej, 8 slabík | AABB
verš
verš
(prázdny riadok = hranica strofy)

Kód metra (4. pole): T, D, J – slúži na automatickú kontrolu prízvukov.
Výstup: davky/davka_K_vN.md + výpis varovaní na stdout.
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from slabiky import analyze, meter_check  # noqa: E402


def parse(path):
    poems = []
    cur = None
    for raw in open(path, encoding="utf-8").read().splitlines():
        if raw.startswith("### "):
            parts = [p.strip() for p in raw[4:].split("|")]
            cur = {"num": parts[0], "title": parts[1], "form": parts[2],
                   "mcode": parts[3], "meter": parts[4], "rhyme": parts[5],
                   "note": parts[6] if len(parts) > 6 else "", "lines": []}
            poems.append(cur)
        elif cur is not None:
            cur["lines"].append(raw.rstrip())
    for p in poems:
        while p["lines"] and not p["lines"][-1].strip():
            p["lines"].pop()
        while p["lines"] and not p["lines"][0].strip():
            p["lines"].pop(0)
    return poems


def stress_render(line):
    split, n, st = analyze(line)
    return split, n, st


def main():
    src = sys.argv[1]
    out = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else "Dávka"
    poems = parse(src)
    md = [f"# {title}", ""]
    md.append("> Rozbor slabík: slabiky oddelené pomlčkou, za „=“ počet slabík. "
              "Prízvučné pozície (1. slabika viacslabičných slov, jednoslabičné predložky) sú uvedené v hranatých zátvorkách.")
    md.append("")
    warn = []
    for p in poems:
        md.append(f"## {int(p['num'])}. {p['title']}")
        md.append("")
        md.append(f"**Forma:** {p['form']} · **Metrum:** {p['meter']} · **Rýmová schéma:** {p['rhyme']}")
        if p["note"]:
            md.append("")
            md.append(f"*Poznámka autora:* {p['note']}")
        md.append("")
        for l in p["lines"]:
            md.append(f"{l}  " if l.strip() else "")
        md.append("")
        md.append("**Rozbor slabík:**")
        md.append("")
        vn = 0
        for l in p["lines"]:
            if not l.strip():
                continue
            vn += 1
            split, n, st = analyze(l)
            pos = [s[0] for s in st if s[1] == "S"]
            md.append(f"{vn}. {split} = {n}  [{', '.join(map(str, pos))}]")
            bad = meter_check(st, p["mcode"])
            if bad:
                warn.append(f"{p['num']} {p['title']} v{vn}: {split} = {n} -> mimo metra {bad}")
        md.append("")
        md.append("---")
        md.append("")
    open(out, "w", encoding="utf-8").write("\n".join(md))
    print("\n".join(warn) if warn else "bez varovaní")


if __name__ == "__main__":
    main()
