#!/usr/bin/env python3
"""Vygeneruje tracker_kniha.html z hodnotení (hodnotenia/*.md) a meta údajov."""
import glob
import html
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = json.load(open(os.path.join(ROOT, "nastroje", "meta.json"), encoding="utf-8"))
FORMY = {"P": "príbehová", "S": "štvorveršie", "H": "hádanka", "D": "dialóg",
         "R": "rečňovanka", "K": "kumulatívna", "Z": "zvukomaľba"}
FCOL = {"P": 1, "S": 2, "H": 3, "D": 4, "R": 5, "K": 6, "Z": 7}
CASTI = {"I": "I – Záhradka", "II": "II – Cesta do sveta", "III": "III – Návrat: zelenina"}
PRAH = {"A": 7, "B": 7, "C": 8}
KRIT = {"A": "A – Zmysluplnosť", "B": "B – Humor", "C": "C – Rýmovanosť"}


def load_records():
    recs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "hodnotenia", "*.md"))):
        m = re.search(r"davka_(\w+)_kolo_(\d+)_([ABC])\.md$", f)
        if not m:
            continue
        txt = open(f, encoding="utf-8").read()
        blocks = re.findall(r"```json\s*(\{.*?\})\s*```", txt, re.S)
        if not blocks:
            continue
        data = json.loads(blocks[-1])
        for h in data["hodnotenia"]:
            recs.append(dict(davka=m.group(1), kolo=int(m.group(2)), kritik=m.group(3),
                             cislo=int(h["cislo"]), skore=float(h["skore"]),
                             funguje=h.get("funguje", ""), zmenit=h.get("zmenit", ""),
                             subor=os.path.relpath(f, ROOT)))
    return recs


def order_key(r):
    d = r["davka"]
    return (int(d) if d.isdigit() else 99, r["kolo"])


def final_scores(recs):
    """Pre každú básničku posledné skóre od každého kritika."""
    last = {}
    for r in sorted(recs, key=order_key):
        last[(r["cislo"], r["kritik"])] = r
    out = {}
    rounds = defaultdict(set)
    for r in recs:
        rounds[r["cislo"]].add((r["davka"], r["kolo"]))
    for b in META["basne"]:
        n = b["cislo"]
        sc = {k: last.get((n, k), {}).get("skore") for k in "ABC"}
        out[n] = dict(sc=sc, kola=len(rounds[n]))
    return out


def status(n, sc):
    if str(n) in META.get("pod_prahom", {}):
        return "pod prahom"
    if all(sc[k] is not None for k in "ABC"):
        if all(sc[k] >= PRAH[k] for k in "ABC"):
            return "zamrazená"
        return "v práci"
    return "nenapísaná"


def esc(s):
    return html.escape(str(s))


def line_chart(series, title, xlabels, w=300, h=170):
    """series: list of (label, slot, [values or None])"""
    pl, pr, pt, pb = 30, 10, 12, 26
    iw, ih = w - pl - pr, h - pt - pb
    n = max(len(xlabels), 1)
    def x(i):
        return pl + (iw * (i / (n - 1)) if n > 1 else iw / 2)
    def y(v):
        return pt + ih - (v - 1) / 9 * ih
    g = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{esc(title)}">']
    for t in (1, 4, 7, 10):
        g.append(f'<line x1="{pl}" x2="{w-pr}" y1="{y(t):.1f}" y2="{y(t):.1f}" class="grid"/>'
                 f'<text x="{pl-6}" y="{y(t)+3:.1f}" class="ax" text-anchor="end">{t}</text>')
    for i, lab in enumerate(xlabels):
        g.append(f'<text x="{x(i):.1f}" y="{h-8}" class="ax" text-anchor="middle">{esc(lab)}</text>')
    for lab, slot, vals in series:
        pts = [(x(i), y(v), v) for i, v in enumerate(vals) if v is not None]
        if len(pts) > 1:
            d = " ".join(f"{'M' if j == 0 else 'L'}{p[0]:.1f},{p[1]:.1f}" for j, p in enumerate(pts))
            g.append(f'<path d="{d}" class="ln" style="stroke:var(--s{slot})"/>')
        for i, (px, py, v) in enumerate(pts):
            g.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" class="dot" style="fill:var(--s{slot})">'
                     f'<title>{esc(lab)}: {v:.2f}</title></circle>')
    g.append("</svg>")
    return "".join(g)


def hbar_chart(rows, title, w=420):
    """rows: list of (label, {A:v,B:v,C:v})"""
    bh, gap = 9, 2
    grp = 3 * bh + 2 * gap + 12
    pl, pr, pt = 110, 40, 8
    h = pt + grp * len(rows) + 10
    iw = w - pl - pr
    g = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{esc(title)}">']
    for t in (2, 4, 6, 8, 10):
        xx = pl + iw * t / 10
        g.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{pt}" y2="{h-10}" class="grid"/>')
    for i, (lab, vals) in enumerate(rows):
        y0 = pt + i * grp
        g.append(f'<text x="{pl-8}" y="{y0+bh*1.5+gap+4}" class="ax" text-anchor="end">{esc(lab)}</text>')
        for j, k in enumerate("ABC"):
            v = vals.get(k)
            if v is None:
                continue
            yy = y0 + j * (bh + gap)
            ww = max(iw * v / 10, 1)
            g.append(f'<rect x="{pl}" y="{yy}" width="{ww:.1f}" height="{bh}" rx="2" style="fill:var(--s{j+1})">'
                     f'<title>{esc(lab)} · {KRIT[k]}: {v:.2f}</title></rect>'
                     f'<text x="{pl+ww+4:.1f}" y="{yy+bh-1}" class="ax">{v:.1f}</text>')
    g.append("</svg>")
    return "".join(g)


def histogram(vals, slot, title, w=220, h=130):
    bins = [0] * 10
    for v in vals:
        bins[min(int(v) - 1, 9) if v >= 1 else 0] += 1
    pl, pb, pt = 8, 20, 10
    iw, ih = w - 2 * pl, h - pb - pt
    mx = max(bins + [1])
    bw = iw / 10
    g = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{esc(title)}">']
    g.append(f'<line x1="{pl}" x2="{w-pl}" y1="{pt+ih}" y2="{pt+ih}" class="grid"/>')
    for i, c in enumerate(bins):
        bh = ih * c / mx
        xx = pl + i * bw + 1
        if c:
            g.append(f'<rect x="{xx:.1f}" y="{pt+ih-bh:.1f}" width="{bw-2:.1f}" height="{bh:.1f}" rx="2" '
                     f'style="fill:var(--s{slot})"><title>{i+1}–{i+1}.9: {c}×</title></rect>'
                     f'<text x="{xx+bw/2-1:.1f}" y="{pt+ih-bh-3:.1f}" class="ax" text-anchor="middle">{c}</text>')
        g.append(f'<text x="{xx+bw/2-1:.1f}" y="{h-6}" class="ax" text-anchor="middle">{i+1}</text>')
    g.append("</svg>")
    return "".join(g)


def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def main():
    recs = load_records()
    fin = final_scores(recs)
    meta = {b["cislo"]: b for b in META["basne"]}

    # --- priemer po kolách pre každú dávku
    by_batch = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in recs:
        by_batch[r["davka"]][r["kolo"]][r["kritik"]].append(r["skore"])
    batch_charts = []
    for d in sorted(by_batch, key=lambda s: int(s) if s.isdigit() else 99):
        kola = sorted(by_batch[d])
        ser = [(KRIT[k], i + 1, [avg(by_batch[d][ko][k]) for ko in kola]) for i, k in enumerate("ABC")]
        lab = "Záverečná kontrola" if not d.isdigit() else f"Dávka {d}"
        batch_charts.append(f'<figure><figcaption>{lab}</figcaption>'
                            f'{line_chart(ser, lab, [f"kolo {k}" for k in kola])}</figure>')

    # --- distribúcia finálnych skóre
    hists = []
    for i, k in enumerate("ABC"):
        vals = [fin[n]["sc"][k] for n in fin if fin[n]["sc"][k] is not None]
        hists.append(f'<figure><figcaption>{KRIT[k]} (n={len(vals)})</figcaption>'
                     f'{histogram(vals, i+1, KRIT[k])}</figure>')

    # --- podľa formy a časti
    def grouped(keyf, labels):
        rows = []
        for key, lab in labels:
            ns = [n for n in fin if keyf(meta[n]) == key and fin[n]["sc"]["A"] is not None]
            if not ns:
                continue
            rows.append((f"{lab} ({len(ns)})", {k: avg([fin[n]["sc"][k] for n in ns]) for k in "ABC"}))
        return rows
    form_rows = grouped(lambda b: b["forma"], list(FORMY.items()))
    part_rows = grouped(lambda b: b["cast"], list(CASTI.items()))

    # --- mapa pestrosti
    cells = []
    for b in META["basne"]:
        n = b["cislo"]
        st = status(n, fin[n]["sc"])
        cells.append(f'<div class="cell st-{st.replace(" ", "-")}" style="--c:var(--s{FCOL[b["forma"]]})" '
                     f'title="{n}. {esc(b["nazov"])} · {FORMY[b["forma"]]} · metrum {b["metrum"]} · {st}">'
                     f'<span class="n">{n}</span><span class="f">{b["forma"]}</span>'
                     f'<span class="m">{b["metrum"]}</span></div>')
        if n in (20, 30):
            cells.append('<div class="sep"></div>')
    legend = "".join(f'<span class="lg"><i style="background:var(--s{FCOL[f]})"></i>{f} {l}</span>'
                     for f, l in FORMY.items())

    # --- prehľad 40
    overview = []
    for cast, lab in CASTI.items():
        rows = []
        for b in META["basne"]:
            if b["cast"] != cast:
                continue
            n = b["cislo"]
            sc = fin[n]["sc"]
            st = status(n, sc)
            def cellv(k):
                v = sc[k]
                if v is None:
                    return "<td>–</td>"
                cls = "ok" if v >= PRAH[k] else "bad"
                return f'<td class="{cls}">{v:.1f}</td>'
            rows.append(f'<tr><td>{n}</td><td>{esc(b["polozka"])}</td><td>{esc(b["nazov"])}</td>'
                        f'<td>{FORMY[b["forma"]]}</td><td>{b["metrum"]}</td>{cellv("A")}{cellv("B")}{cellv("C")}'
                        f'<td>{fin[n]["kola"]}</td><td><span class="badge b-{st.replace(" ", "-")}">{st}</span></td></tr>')
        overview.append(f'<h3>Časť {lab}</h3><div class="tw"><table><thead><tr><th>#</th><th>položka</th>'
                        f'<th>názov</th><th>forma</th><th>metrum</th><th>A</th><th>B</th><th>C</th><th>kôl</th>'
                        f'<th>stav</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    counts = defaultdict(int)
    for n in fin:
        counts[status(n, fin[n]["sc"])] += 1

    # --- detailná tabuľka
    det = []
    for r in sorted(recs, key=lambda r: (order_key(r), r["cislo"], r["kritik"])):
        b = meta[r["cislo"]]
        cls = "ok" if r["skore"] >= PRAH[r["kritik"]] else "bad"
        det.append(f'<tr><td>{esc(r["davka"])}</td><td>{r["kolo"]}</td><td>{b["cast"]}</td>'
                   f'<td>{r["cislo"]}. {esc(b["polozka"])}</td><td>{FORMY[b["forma"]]}</td>'
                   f'<td>{r["kritik"]}</td><td class="{cls}">{r["skore"]:.1f}</td>'
                   f'<td>{esc(r["funguje"])}</td><td>{esc(r["zmenit"])}</td></tr>')

    # --- odkazy na verzie
    links = []
    for f in sorted(glob.glob(os.path.join(ROOT, "davky", "davka_*.md")),
                    key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p)]):
        rel = os.path.relpath(f, ROOT)
        links.append(f'<a href="{rel}">{os.path.basename(f)}</a>')
    hlinks = []
    for f in sorted(glob.glob(os.path.join(ROOT, "hodnotenia", "*.md"))):
        rel = os.path.relpath(f, ROOT)
        hlinks.append(f'<a href="{rel}">{os.path.basename(f)}</a>')
    extra = [p for p in ("kniha.md", "kniha.html", "plan_knihy.md", "brief_kniha.md", "pravidla_z_pilotu.md",
                         "sumar_knihy.md", "ilustracie_brief.md") if os.path.exists(os.path.join(ROOT, p))]

    page = TEMPLATE.format(
        n_ok=counts["zamrazená"], n_wip=counts["v práci"], n_low=counts["pod prahom"],
        n_todo=counts["nenapísaná"], n_rec=len(recs),
        batch_charts="".join(batch_charts) or "<p class='muted'>Zatiaľ žiadne hodnotenia.</p>",
        hists="".join(hists),
        form_chart=hbar_chart(form_rows, "Priemer podľa formy") if form_rows else "",
        part_chart=hbar_chart(part_rows, "Priemer podľa časti") if part_rows else "",
        cells="".join(cells), legend=legend, overview="".join(overview), det="".join(det),
        links=" · ".join(links), hlinks=" · ".join(hlinks),
        extra=" · ".join(f'<a href="{p}">{p}</a>' for p in extra),
        klegend="".join(f'<span class="lg"><i style="background:var(--s{i+1})"></i>{KRIT[k]} (prah {PRAH[k]})</span>'
                        for i, k in enumerate("ABC")),
    )
    open(os.path.join(ROOT, "tracker_kniha.html"), "w", encoding="utf-8").write(page)
    print(f"tracker: {len(recs)} záznamov, zamrazené {counts['zamrazená']}, v práci {counts['v práci']}, "
          f"pod prahom {counts['pod prahom']}, nenapísané {counts['nenapísaná']}")


TEMPLATE = """<!doctype html>
<html lang="sk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tracker básničkovej knihy</title>
<style>
:root{{color-scheme:light;--bg:#fcfcfb;--card:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3df;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--s6:#008300;--s7:#6250d6;
--ok:#0f7a3a;--okbg:#e5f4ea;--bad:#a32b2b;--badbg:#fbe9e7;--wip:#8a5a00;--wipbg:#fdf2dc}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{color-scheme:dark;--bg:#1a1a19;--card:#232321;
--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3936;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;
--s6:#008300;--s7:#9085e9;--ok:#7fd49c;--okbg:#1f3a28;--bad:#f19b93;--badbg:#45231f;--wip:#f0c46a;--wipbg:#3d3018}}}}
:root[data-theme="dark"]{{color-scheme:dark;--bg:#1a1a19;--card:#232321;--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3936;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--ok:#7fd49c;
--okbg:#1f3a28;--bad:#f19b93;--badbg:#45231f;--wip:#f0c46a;--wipbg:#3d3018}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px 64px}}h1{{font-size:26px;margin:0 0 4px}}h2{{font-size:19px;margin:36px 0 12px}}
h3{{font-size:16px;margin:20px 0 8px}}.muted{{color:var(--ink2)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:18px 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}.kpi b{{font-size:26px;display:block}}
.grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}
figure{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px}}
figcaption{{font-size:13px;color:var(--ink2);margin-bottom:4px}}
.chart{{width:100%;height:auto;display:block}}.chart .grid{{stroke:var(--line);stroke-width:1}}
.chart .ax{{fill:var(--ink2);font-size:10px}}.chart .ln{{fill:none;stroke-width:2}}.chart .dot{{stroke:var(--card);stroke-width:2}}
.lg{{display:inline-flex;align-items:center;gap:6px;margin:0 14px 6px 0;font-size:13px;color:var(--ink2)}}
.lg i{{width:12px;height:12px;border-radius:3px;display:inline-block}}
.map{{display:flex;flex-wrap:wrap;gap:4px;align-items:stretch}}
.cell{{width:46px;height:58px;border-radius:6px;background:var(--c);color:#fff;display:flex;flex-direction:column;
align-items:center;justify-content:center;font-size:11px;line-height:1.2;position:relative}}
.cell .n{{font-weight:700;font-size:14px}}.cell.st-nenapísaná{{opacity:.35}}
.cell.st-zamrazená::after{{content:"✓";position:absolute;top:1px;right:4px;font-size:10px}}
.sep{{width:10px}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card)}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{color:var(--ink2);font-weight:600;position:sticky;top:0;background:var(--card)}}
td.ok{{color:var(--ok);font-weight:600}}td.bad{{color:var(--bad);font-weight:600}}
.badge{{padding:2px 8px;border-radius:999px;font-size:12px;white-space:nowrap}}
.b-zamrazená{{background:var(--okbg);color:var(--ok)}}.b-v-práci{{background:var(--wipbg);color:var(--wip)}}
.b-pod-prahom{{background:var(--badbg);color:var(--bad)}}.b-nenapísaná{{color:var(--ink2);border:1px solid var(--line)}}
.det{{max-height:640px;overflow:auto}}.det td:nth-child(8),.det td:nth-child(9){{min-width:240px}}
a{{color:var(--s1)}}.links a{{margin-right:4px}}
</style></head><body><main>
<h1>Tracker knihy „Ovocie a zelenina zo záhradky aj zo sveta“</h1>
<p class="muted">40 básničiek · 3 časti · prahy: A ≥ 7, B ≥ 7, C ≥ 8 · stránka sa generuje skriptom <code>nastroje/tracker.py</code> po každom kole.</p>
<div class="kpis"><div class="kpi"><b>{n_ok}</b>zamrazené</div><div class="kpi"><b>{n_wip}</b>v práci</div>
<div class="kpi"><b>{n_low}</b>pod prahom</div><div class="kpi"><b>{n_todo}</b>nenapísané</div><div class="kpi"><b>{n_rec}</b>hodnotení spolu</div></div>

<h2>Mapa pestrosti (poradie v knihe, farba = forma)</h2>
<div>{legend}</div><div class="map">{cells}</div>
<p class="muted">Písmeno dole = metrum (T trochej, D daktyl, J jamb). ✓ = zamrazená. Medzery oddeľujú časti I | II | III.</p>

<h2>Priemerné skóre po kolách</h2><div>{klegend}</div><div class="grid2">{batch_charts}</div>
<h2>Distribúcia finálnych skóre</h2><div class="grid2">{hists}</div>
<h2>Priemer podľa formy a podľa časti</h2><div>{klegend}</div>
<div class="grid2"><figure><figcaption>Podľa formy (počet básničiek)</figcaption>{form_chart}</figure>
<figure><figcaption>Podľa časti knihy</figcaption>{part_chart}</figure></div>

<h2>Prehľad 40 básničiek</h2>{overview}

<h2>Všetky hodnotenia</h2>
<div class="tw det"><table><thead><tr><th>dávka</th><th>kolo</th><th>časť</th><th>ovocie/zelenina</th><th>forma</th>
<th>kritik</th><th>skóre</th><th>čo funguje</th><th>čo zmeniť k 10/10</th></tr></thead><tbody>{det}</tbody></table></div>

<h2>Verzie a súbory</h2>
<p class="links"><b>Dávky:</b> {links}</p><p class="links"><b>Hodnotenia:</b> {hlinks}</p><p class="links"><b>Kniha:</b> {extra}</p>
</main></body></html>
"""

if __name__ == "__main__":
    main()
