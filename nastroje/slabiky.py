#!/usr/bin/env python3
"""Pomocný počítač slabík a prízvukov pre slovenské verše.

Použitie:
  python3 nastroje/slabiky.py subor.md        # rozbor všetkých básničiek (bloky ```verse)
  echo "Pošepla mi jedna muška" | python3 nastroje/slabiky.py -

Pravidlá:
- slabikotvorné jadro: samohlásky, dvojhlásky ia/ie/iu/ô (1 slabika),
  slabikotvorné r/ŕ/l/ĺ medzi spoluhláskami (vlk, prst, slnko),
- prízvuk na 1. slabike slova; jednoslabičné predložky sa spájajú s nasledujúcim slovom,
- ostatné jednoslabičné slová sú „neutrálne“ (môžu stáť na ťažkej aj ľahkej dobe).
Je to pomôcka, výsledok treba vždy prečítať a skontrolovať aj sluchom.
"""
import re
import sys

VOWELS = set("aáäeéiíoóôuúyý")
SYLLABIC = set("rŕlĺ")
DIPH = ("ia", "ie", "iu")
# slová, kde i+samohláska nie je dvojhláska
HIATUS = ("ária", "rádio", "piano", "klavír", "aliga", "kakao", "brioš", "zoo",
          "ananás", "kiwi", "kivi", "mangu", "india", "afrik", "itáli", "austráli",
          "brazíli", "ázi", "ázia", "mária", "olympi", "Indi", "Ázi")
PREP = {"v", "vo", "z", "zo", "k", "ku", "s", "so", "do", "na", "po", "pod", "nad",
        "za", "od", "pri", "pre", "cez", "bez", "o", "u", "zo", "spod", "spoza",
        "pred", "medzi"}
ONSETS = {"pr", "br", "tr", "dr", "kr", "gr", "vr", "fr", "zr", "sr", "šr", "žr", "chr",
          "pl", "bl", "kl", "gl", "vl", "fl", "sl", "zl", "šl", "hl", "hr", "mr", "ml",
          "st", "sk", "sp", "šk", "št", "šp", "zv", "zb", "zd", "sv", "tv", "dv", "kv",
          "čl", "čr", "ťr", "mn", "pn", "sn", "zn", "šn", "žn", "dl", "tl", "cv", "chv", "chl", "hn", "kn", "gn"}


def syllables(word):
    w = word.lower()
    w = re.sub(r"[^a-záäčďéíĺľňóôŕšťúýž]", "", w)
    if not w:
        return []
    hiatus = any(h.lower() in w for h in HIATUS)
    nuclei = []  # indexy jadier
    i = 0
    n = len(w)
    while i < n:
        c = w[i]
        if c in VOWELS:
            if not hiatus and c == "i" and i + 1 < n and w[i:i + 2] in DIPH:
                nuclei.append((i, i + 1))
                i += 2
                continue
            if c in "ao" and i + 1 < n and w[i + 1] == "u":
                # dvojhláska au/ou (au, hau, mňau, kakaou)
                nuclei.append((i, i + 1))
                i += 2
                continue
            nuclei.append((i, i))
            i += 1
            continue
        if c in SYLLABIC and i > 0 and w[i - 1] == c:
            i += 1
            continue
        if c in SYLLABIC:
            prev_cons = i > 0 and w[i - 1] not in VOWELS
            start = i == 0
            next_cons = (i + 1 >= n) or (w[i + 1] not in VOWELS)
            if (prev_cons or start) and next_cons and not (i + 1 >= n and start):
                # slabikotvorné r/l (vlk, prst, slnko, krk)
                if not (i + 1 < n and w[i + 1] in SYLLABIC and False):
                    nuclei.append((i, i))
        i += 1
    if not nuclei:
        return [word]
    # rozdeľ na slabiky: hranica pred poslednou spoluhláskou medzi jadrami
    parts = []
    start = 0
    for k in range(len(nuclei) - 1):
        end_cur = nuclei[k][1]
        start_next = nuclei[k + 1][0]
        cons = start_next - end_cur - 1
        cut = end_cur + 1 if cons <= 1 else start_next - 1
        if cons >= 1 and w[start_next - 1:start_next + 1] in ("ch",):
            pass
        if cons >= 2 and w[start_next - 2:start_next] == "ch":
            cut = start_next - 2
        if cons == 2 and w[start_next - 2:start_next] in ONSETS:
            cut = start_next - 2
        parts.append(w[start:cut])
        start = cut
    parts.append(w[start:])
    return parts


def analyze(line):
    line = re.sub(r"^[A-ZÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ]{2,}( [A-ZÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽ]{2,})*:\s*", "", line.strip())
    tokens = re.findall(r"[A-Za-zÁÄČĎÉÍĹĽŇÓÔŔŠŤÚÝŽáäčďéíĺľňóôŕšťúýž]+", line)
    out = []
    pos = 0
    stresses = []   # (pozícia, typ) typ: S = povinný prízvuk, n = neutrálny
    pending_prep = False
    for t in tokens:
        syl = syllables(t)
        if not syl or (len(syl) == 1 and not any(ch.lower() in VOWELS | SYLLABIC for ch in t)):
            # bezslabičná predložka v, z, k, s
            out.append(t)
            continue
        first = pos + 1
        if pending_prep:
            pending_prep = False
            # prízvuk už bol na predložke
        elif t.lower() in PREP and len(syl) == 1:
            stresses.append((first, "S"))
            pending_prep = True
        elif len(syl) == 1:
            stresses.append((first, "n"))
        else:
            stresses.append((first, "S"))
        pos += len(syl)
        out.append("-".join(syl))
    return " ".join(out), pos, stresses


def meter_check(stresses, meter):
    bad = []
    for p, typ in stresses:
        if typ != "S":
            continue
        if meter == "T" and p % 2 == 0:
            bad.append(p)
        elif meter == "D" and (p - 1) % 3 != 0:
            bad.append(p)
        elif meter == "J" and p % 2 == 1 and p != 1:
            bad.append(p)
    return bad


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    meter = sys.argv[2] if len(sys.argv) > 2 else "T"
    text = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    for line in text.splitlines():
        s = line.strip()
        if not s:
            print()
            continue
        split, n, st = analyze(s)
        bad = meter_check(st, meter)
        mark = "" if not bad else f"   !! prízvuk mimo metra na pozícii {bad}"
        print(f"{split} = {n}{mark}")


if __name__ == "__main__":
    main()
