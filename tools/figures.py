#!/usr/bin/env python3
"""Draw the four figures, in the four formats the manual ships.

    python3 tools/figures.py

SVG is written by hand here so the text stays text — a machine reading the file
gets the labels and the numbers, not a picture of them. PNG and JPG come off the
same SVG through rsvg-convert, so the raster and the vector can never disagree.
The GIF is composed frame by frame in Pillow.
"""
from __future__ import annotations

import csv, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "docs" / "img"
DATA = ROOT / "data"

INK, PAPER = "#171310", "#faf6ef"
HONEY, COMB = "#c8891f", "#e8c16a"
SLATE, RULE, FAINT = "#7d878c", "#d8cfc0", "#b5a892"
MONO = "ui-monospace, SFMono-Regular, Menlo, monospace"
SANS = "Georgia, 'Iowan Old Style', serif"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, size=13, fill=INK, anchor="start", family=SANS, weight="normal", ls="0"):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{ls}">{esc(s)}</text>')


def frame(w, h, title, desc, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d">
<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>
<rect width="{w}" height="{h}" fill="{PAPER}"/>
{body}
</svg>
'''


# ---------------------------------------------------------------- figure 1
def fig_clones_vs_views(rows):
    rows = sorted(rows, key=lambda r: -r["unique_cloners"])[:16]
    w, h = 960, 700
    x0, top, rowh = 250, 118, 33
    scale = 620 / max(r["unique_cloners"] for r in rows)
    b = [txt(40, 48, "Who came for it", 27, INK, weight="bold"),
         txt(40, 74, "fourteen days, one GitHub account, fifty-two repositories", 14, SLATE),
         txt(40, 96, "distinct machines that copied the whole repository  ·  distinct browsers that opened its page",
             12, FAINT, family=MONO),
         f'<line x1="40" y1="106" x2="{w-40}" y2="106" stroke="{RULE}" stroke-width="1"/>']
    for i, r in enumerate(rows):
        y = top + i * rowh
        bw = max(2.5, r["unique_cloners"] * scale)
        vw = r["unique_viewers"] * scale
        b.append(txt(x0 - 12, y + 12, r["repo"], 13, INK, anchor="end", family=MONO))
        b.append(f'<rect x="{x0}" y="{y}" width="{bw:.1f}" height="16" fill="{HONEY}" rx="1.5"/>')
        if vw > 0:
            b.append(f'<rect x="{x0}" y="{y+18}" width="{max(2.5,vw):.1f}" height="5" fill="{SLATE}" rx="1"/>')
        b.append(txt(x0 + bw + 9, y + 13, r["unique_cloners"], 13, HONEY, family=MONO, weight="bold"))
        lbl = str(r["unique_viewers"]) if r["unique_viewers"] else "0"
        b.append(txt(x0 + max(bw, 20) + 42, y + 13, lbl, 11, SLATE if r["unique_viewers"] else FAINT, family=MONO))
    y = top + len(rows) * rowh + 16
    b += [f'<line x1="40" y1="{y}" x2="{w-40}" y2="{y}" stroke="{RULE}"/>',
          f'<rect x="{x0}" y="{y+16}" width="26" height="11" fill="{HONEY}" rx="1.5"/>',
          txt(x0 + 34, y + 26, "unique cloners", 12, INK),
          f'<rect x="{x0+160}" y="{y+20}" width="26" height="5" fill="{SLATE}" rx="1"/>',
          txt(x0 + 194, y + 26, "unique page viewers", 12, INK),
          txt(w - 40, y + 26, "GitHub traffic API · 4 – 18 Sept 2026", 11, FAINT, anchor="end", family=MONO)]
    return frame(w, h, "Unique cloners against unique page viewers, by repository",
                 "Sixteen repositories. The honey bars are distinct machines that cloned the "
                 "repository; the thin grey bars are distinct browsers that loaded its GitHub page. "
                 "Most repositories show double-digit cloners against zero viewers.", "\n".join(b))


# ---------------------------------------------------------------- figure 2
def fig_day_zero(days):
    w, h = 960, 540
    l, r_, top, bot = 70, 40, 150, 440
    mx = max(d["clones"] for d in days) or 1
    bw = (w - l - r_) / len(days)
    b = [txt(40, 48, "Day zero", 27, INK, weight="bold"),
         txt(40, 74, "clones a day across the account, and the evening seven directories went up", 14, SLATE),
         f'<line x1="40" y1="96" x2="{w-40}" y2="96" stroke="{RULE}"/>']
    for gy in (0, 0.25, 0.5, 0.75, 1.0):
        y = bot - gy * (bot - top)
        b.append(f'<line x1="{l}" y1="{y:.1f}" x2="{w-r_}" y2="{y:.1f}" stroke="{RULE}" stroke-width="0.7" stroke-dasharray="2 4"/>')
        b.append(txt(l - 10, y + 4, int(gy * mx), 11, FAINT, anchor="end", family=MONO))
    for i, d in enumerate(days):
        x = l + i * bw
        bh = (d["clones"] / mx) * (bot - top)
        peak = d["clones"] == mx
        b.append(f'<rect x="{x+bw*0.16:.1f}" y="{bot-bh:.1f}" width="{bw*0.68:.1f}" height="{bh:.1f}" '
                 f'fill="{HONEY if peak else COMB}" rx="1.5"/>')
        b.append(txt(x + bw / 2, bot + 18, d["date"][5:], 10, FAINT if not peak else INK,
                     anchor="middle", family=MONO))
        if d["clones"]:
            b.append(txt(x + bw / 2, bot - bh - 7, d["clones"], 11, INK if peak else SLATE,
                         anchor="middle", family=MONO, weight="bold" if peak else "normal"))
    b += [txt(l, top - 44, "617 clones from 267 distinct machines, in the twenty-four hours after publishing.",
              15, INK),
          txt(l, top - 24, "The twelve days before it come to 293 between them. Nothing linked to the new repositories.",
              13, SLATE),
          txt(l, bot + 56, "vertical axis: total clone operations · GitHub traffic API, UTC days",
              11, FAINT, family=MONO)]
    return frame(w, h, "Clones per day across the account over fourteen days",
                 "A daily bar chart. Days before 16 September range from zero to fifty-six clones. "
                 "16 September reaches 617 clones from 267 distinct machines, the day seven new "
                 "directories were published. 17 September falls back to 51.", "\n".join(b))


# ---------------------------------------------------------------- figure 3
def fig_hallway():
    w, h = 1000, 530
    b = [txt(44, 50, "The hallway", 27, INK, weight="bold"),
         txt(44, 76, "what an arriving agent can pick up, and what it costs you to leave out", 14, SLATE),
         f'<line x1="44" y1="98" x2="{w-44}" y2="98" stroke="{RULE}"/>']
    doors = [
        ("robots.txt", "named crawlers, allowed by name", "a crawler that guesses"),
        ("llms.txt", "every page, one line each", "a full crawl to find the map"),
        ("corpus.jsonl", "the corpus, already flat", "HTML parsed back into rows"),
        ("schema.json", "what the fields mean", "field names guessed from values"),
        ("sources.json", "where each fact came from", "a claim with no provenance"),
        ("CITATION.cff", "how to name you", "an uncredited paraphrase"),
        ("LICENSE", "what carrying it obliges", "silence, read as permission"),
    ]
    x, y0, cw, gap = 44, 130, 128, 8
    for i, (name, gives, costs) in enumerate(doors):
        cx = x + i * (cw + gap)
        b += [f'<rect x="{cx}" y="{y0}" width="{cw}" height="196" fill="none" stroke="{RULE}" stroke-width="1.4" rx="3"/>',
              f'<rect x="{cx}" y="{y0}" width="{cw}" height="30" fill="{HONEY}" rx="3"/>',
              f'<rect x="{cx}" y="{y0+24}" width="{cw}" height="6" fill="{HONEY}"/>',
              txt(cx + cw / 2, y0 + 20, name, 11.5, PAPER, anchor="middle", family=MONO, weight="bold")]
        for j, line in enumerate(_wrap(gives, 17)):
            b.append(txt(cx + 10, y0 + 54 + j * 15, line, 11.5, INK))
        b.append(f'<line x1="{cx+10}" y1="{y0+126}" x2="{cx+cw-10}" y2="{y0+126}" stroke="{RULE}" stroke-dasharray="2 3"/>')
        b.append(txt(cx + 10, y0 + 144, "without it:", 10, FAINT, family=MONO))
        for j, line in enumerate(_wrap(costs, 17)):
            b.append(txt(cx + 10, y0 + 160 + j * 14, line, 11, SLATE))
    ay = y0 + 232
    b += [f'<line x1="44" y1="{ay}" x2="{w-90}" y2="{ay}" stroke="{INK}" stroke-width="1.6"/>',
          f'<path d="M {w-90} {ay-7} L {w-62} {ay} L {w-90} {ay+7} Z" fill="{INK}"/>',
          txt(44, ay + 26, "an agent arrives", 12, INK, family=MONO),
          txt(w - 90, ay + 26, "and leaves carrying the whole thing", 12, INK, family=MONO, anchor="end"),
          txt(44, ay + 62, "Each door is a file at a guessable path. None of them needs an account, a key, a "
                           "rate limit or a render pass;", 13.5, INK),
          txt(44, ay + 82, "each one removes a guess the next reader would otherwise have to make. "
                           "The corridor is the product.", 13.5, INK),
          txt(44, ay + 108, "uptake · nanobotco.github.io/uptake", 11, FAINT, family=MONO)]
    return frame(w, h, "The seven files an arriving agent can pick up",
                 "Seven doors along a corridor: robots.txt, llms.txt, flat corpus files, a record "
                 "schema, a sources registry, a citation file and a licence. Each names what it "
                 "gives an agent and what its absence costs.", "\n".join(b))


def _wrap(s, n):
    out, line = [], ""
    for word in s.split():
        if len(line) + len(word) + 1 > n and line:
            out.append(line); line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


# ---------------------------------------------------------------- rasterise
def rasterise(svg_path, png_path=None, jpg_path=None, width=None):
    if png_path:
        cmd = ["rsvg-convert", "-f", "png", "-o", str(png_path)]
        if width:
            cmd += ["-w", str(width)]
        subprocess.run(cmd + [str(svg_path)], check=True)
    if jpg_path:
        tmp = svg_path.with_suffix(".tmp.png")
        cmd = ["rsvg-convert", "-f", "png", "-o", str(tmp)]
        if width:
            cmd += ["-w", str(width)]
        subprocess.run(cmd + [str(svg_path)], check=True)
        subprocess.run(["magick", str(tmp), "-background", PAPER, "-flatten",
                        "-strip", "-quality", "88", str(jpg_path)], check=True)
        tmp.unlink()


# ---------------------------------------------------------------- figure 4, animated
def fig_arrival_gif(days, out):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 720, 400
    l, r_, top, bot = 60, 30, 110, 320
    mx = max(d["clones"] for d in days) or 1
    bw = (W - l - r_) / len(days)

    def font(sz, bold=False):
        for p in ("/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold
                  else "/System/Library/Fonts/Supplemental/Georgia.ttf",
                  "/System/Library/Fonts/SFNSMono.ttf", "/Library/Fonts/Arial.ttf"):
            try:
                return ImageFont.truetype(p, sz)
            except OSError:
                continue
        return ImageFont.load_default()

    f_big, f_lab, f_num = font(20, True), font(10), font(11, True)
    frames = []
    for n in range(1, len(days) + 2):
        im = Image.new("RGB", (W, H), PAPER)
        d = ImageDraw.Draw(im)
        d.text((36, 30), "Fourteen days of arrivals", INK, font=f_big)
        d.line([(36, 62), (W - 36, 62)], RULE, 1)
        d.line([(l, bot), (W - r_, bot)], FAINT, 1)
        shown = days[:min(n, len(days))]
        for i, day in enumerate(shown):
            x = l + i * bw
            bh = (day["clones"] / mx) * (bot - top)
            peak = day["clones"] == mx
            d.rectangle([x + bw * .16, bot - bh, x + bw * .84, bot],
                        fill=HONEY if peak else COMB)
            d.text((x + bw * .5 - 11, bot + 6), day["date"][5:], FAINT, font=f_lab)
            if day["clones"]:
                lab = str(day["clones"])
                d.text((x + bw * .5 - 3 * len(lab), bot - bh - 15), lab,
                       INK if peak else SLATE, font=f_num)
        last = shown[-1]
        if last["clones"] == mx:
            d.text((l, top - 46), f"{last['date']}: seven directories published", INK, font=font(14, True))
            d.text((l, top - 26), f"{last['clones']} clones · {last['uniques']} distinct machines · 4 page views across the seven",
                   SLATE, font=font(12))
        else:
            d.text((l, top - 36), f"{last['date']} · {last['clones']} clones, {last['uniques']} distinct machines",
                   SLATE, font=font(12))
        d.text((36, H - 26), "uptake — GitHub traffic API, NaNoBotCo, 4–18 Sept 2026", FAINT, font=f_lab)
        frames.append(im)
    # Every frame redraws the whole panel, so each one is written whole and the
    # previous one is cleared first (disposal 2). Pillow's frame differencing would
    # leave the earlier caption showing through under the new one.
    seq = frames + [frames[-1]] * 6
    dur = [380] * len(frames) + [300] * 5 + [2600]
    seq[0].save(out, save_all=True, append_images=seq[1:], duration=dur,
                loop=0, optimize=False, disposal=2)


# ---------------------------------------------------------------- main
def main():
    IMG.mkdir(parents=True, exist_ok=True)
    rows = json.loads((DATA / "repo-traffic-2026-09-18.json").read_text())["repositories"]
    days = json.loads((DATA / "account-daily-2026-09-18.json").read_text())["days"]

    f1 = IMG / "figure-1-who-came-for-it.svg"
    f1.write_text(fig_clones_vs_views(rows))
    rasterise(f1, png_path=IMG / "figure-1-who-came-for-it.png", width=1440)

    f2 = IMG / "figure-2-day-zero.svg"
    f2.write_text(fig_day_zero(days))
    rasterise(f2, png_path=IMG / "figure-2-day-zero.png", width=1440)

    f3 = IMG / "figure-3-the-hallway.svg"
    f3.write_text(fig_hallway())
    rasterise(f3, jpg_path=IMG / "figure-3-the-hallway.jpg", width=1500)

    fig_arrival_gif(days, IMG / "figure-4-arrivals.gif")

    for p in sorted(IMG.glob("figure-*")):
        print(f"  {p.name:36} {p.stat().st_size:>9,} B")


if __name__ == "__main__":
    main()
