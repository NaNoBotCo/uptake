#!/usr/bin/env python3
"""Build the site from manual/uptake.md, data/*.json and docs/img/*.

    python3 tools/build.py

One source of prose, four renderings: an HTML page for people, a plain-text file for
anyone reading without a browser, the Markdown itself, and a flattened corpus for a
retrieval pipeline. The citation numbers in the text are resolved against
data/sources.json at build time, so a reference with no entry fails the build instead
of shipping as a dead superscript.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import shutil
import textwrap
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"
SITE = "https://nanobotco.github.io/uptake"
BUILT = datetime.now(timezone.utc).strftime("%Y-%m-%d")
PUBLISHED = "2026-09-18"

SOURCES = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text())["sources"]}
TRAFFIC = json.loads((DATA / "repo-traffic-2026-09-18.json").read_text())
DAILY = json.loads((DATA / "account-daily-2026-09-18.json").read_text())
T = TRAFFIC["totals"]

TITLE = "Uptake"
TAGLINE = "Publishing for machines that copy"
BLURB = ("A field manual for the web after search. Fifty-two repositories over fourteen days: "
         f"{T['clones']} clones from {T['unique_cloners']} distinct machines, against {T['views']} page "
         f"views from {T['unique_viewers']} distinct browsers. The unit of arrival is the copy, not the click.")

# ------------------------------------------------------------------ markdown
CITE = re.compile(r"\[S(\d+)\]")
FIG = re.compile(r"^!\[([^|\]]*)\|([^|\]]*)\|(.*)\]\((\S+)\)\s*$")


def inline(s, links=True):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    if links:
        s = CITE.sub(lambda m: f'<a class="cite" href="#s{m.group(1)}" title="'
                               f'{html.escape(SOURCES[int(m.group(1))]["title"])}">{m.group(1)}</a>', s)
    else:
        s = CITE.sub(lambda m: f"[{m.group(1)}]", s)
    return s


def render(md):
    """Markdown -> (html blocks, plain-text blocks, figure list)."""
    out, plain, figs = [], [], []
    lines = md.split("\n")
    i, sect = 0, 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("# "):
            out.append(f"<h1>{inline(ln[2:])}</h1>")
            i += 1                                   # the text file's own header carries the title
        elif ln.startswith("## "):
            head = ln[3:]
            m = re.match(r"^(\d+)\.\s+(.*)$", head)
            if m:
                sect = int(m.group(1))
                slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
                out.append(f'<h2 id="{slug}"><span class="num">{sect}</span>{inline(m.group(2))}</h2>')
                plain.append(f"\n\n{sect}. {m.group(2).upper()}\n" + "-" * 74)
            else:
                slug = re.sub(r"[^a-z0-9]+", "-", head.lower()).strip("-")
                standfirst = bool(out) and out[-1].startswith("<h1")
                cls = " class=\"standfirst\"" if standfirst else ""
                out.append(f'<h2 id="{slug}"{cls}>{inline(head)}</h2>')
                if not standfirst:
                    plain.append(f"\n\n{head.upper()}\n" + "-" * 74)
            i += 1
        elif ln.strip() == "---":
            out.append('<hr>')
            plain.append("\n" + "·" * 74)
            i += 1
        elif ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            plain.append(textwrap.fill("    " + CITE.sub(r"[\1]", " ".join(buf)), 78,
                                       initial_indent="    ", subsequent_indent="    "))
        elif FIG.match(ln):
            name, alt, cap = FIG.match(ln).group(1, 2, 3)
            src = FIG.match(ln).group(4).replace("docs/", "")
            figs.append({"file": src, "alt": alt, "caption": CITE.sub(r"[\1]", cap)})
            sizes = alt_srcs(src)
            out.append(
                f'<figure><img src="{src}" alt="{html.escape(alt)}" loading="lazy" decoding="async">'
                f'<figcaption>{inline(cap)}{sizes}</figcaption></figure>')
            flat = CITE.sub(r"[\1]", cap)
            plain.append(textwrap.fill("[FIGURE: " + alt + "] " + flat, 78,
                                       initial_indent="  ", subsequent_indent="  "))
            i += 1
        elif ln.startswith("| "):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            body = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
            head, body = (body[0], body[1:]) if any(body[0]) and len(body) > 1 else (None, body)
            h = ["<div class=\"scroll\"><table>"]
            if head and any(head):
                h.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
            h.append("<tbody>")
            for r in body:
                h.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            h.append("</tbody></table></div>")
            out.append("".join(h))
            plain.append(plain_table(head if head and any(head) else None, body))
        elif ln.startswith("*") and ln.rstrip().endswith("*") and len(ln.strip()) > 2 and not ln.startswith("**"):
            out.append(f"<p class=\"aside\">{inline(ln.strip().strip('*'))}</p>")
            plain.append(textwrap.fill(ln.strip().strip("*"), 78))
            i += 1
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", ">", "|", "!", "---")):
                buf.append(lines[i].strip())
                i += 1
            if not buf:                       # a line no branch claimed; never stall on it
                i += 1
                continue
            para = " ".join(buf)
            out.append(f"<p>{inline(para)}</p>")
            plain.append(textwrap.fill(CITE.sub(r"[\1]", para), 78))
    return out, plain, figs


def plain_table(head, body, width=74):
    """Lay a table out in fixed columns, wrapped, for the plain-text file."""
    clean = lambda c: CITE.sub(r"[\1]", c).replace("`", "").replace("**", "")
    rows = ([head] if head else []) + body
    cols = max(len(r) for r in rows)
    rows = [r + [""] * (cols - len(r)) for r in rows]
    rows = [[clean(c) for c in r] for r in rows]
    want = [max(len(c) for c in col) for col in zip(*rows)]
    gap = 2
    room = width - 2 - gap * (cols - 1)
    while sum(want) > room:                       # shave the widest column until it fits
        want[want.index(max(want))] -= 1
    out = []
    for n, r in enumerate(rows):
        cells = [textwrap.wrap(c, w) or [""] for c, w in zip(r, want)]
        for line in range(max(len(c) for c in cells)):
            out.append("  " + (" " * gap).join(
                (c[line] if line < len(c) else "").ljust(w) for c, w in zip(cells, want)).rstrip())
        if head and n == 0:
            out.append("  " + (" " * gap).join("-" * w for w in want))
    return "\n".join(out)


def alt_srcs(src):
    stem = pathlib.Path(src).stem
    others = sorted(p.name for p in (DOCS / "img").glob(stem + ".*")
                    if p.name != pathlib.Path(src).name and not p.name.endswith(".json"))
    if not others:
        return ""
    links = " · ".join(f'<a href="img/{o}">{o.rsplit(".", 1)[1]}</a>' for o in others)
    return f' <span class="alt">also as {links}</span>'


# ------------------------------------------------------------------ sources
def sources_html():
    rows = []
    for i in sorted(SOURCES):
        s = SOURCES[i]
        rows.append(
            f'<li id="s{i}"><span class="sn">{i}</span>'
            f'<a href="{html.escape(s["url"])}">{html.escape(s["title"])}</a>'
            f'<span class="pub">{html.escape(s["publisher"])} · {html.escape(s["kind"])}</span>'
            f'<span class="why">{inline(s["used_for"], links=False)}</span></li>')
    return '<ol class="sources">' + "".join(rows) + "</ol>"


def sources_text():
    out = []
    for i in sorted(SOURCES):
        s = SOURCES[i]
        out.append(f"[{i}] {s['title']}")
        out.append(f"     {s['publisher']} — {s['kind']}")
        out.append(f"     {s['url']}")
        out.append(textwrap.fill(s["used_for"], 74, initial_indent="     ", subsequent_indent="     "))
        out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------ structured data
def jsonld():
    dist = [
        ("repo-traffic-2026-09-18.json", "application/json"),
        ("repo-traffic-2026-09-18.csv", "text/csv"),
        ("account-daily-2026-09-18.json", "application/json"),
        ("account-daily-2026-09-18.csv", "text/csv"),
        ("sources.json", "application/json"),
        ("corpus.jsonl", "application/x-ndjson"),
    ]
    dataset = {
        "@type": "Dataset",
        "@id": f"{SITE}/#dataset",
        "name": "Repository clone and view traffic, NaNoBotCo, 4–18 September 2026",
        "description": TRAFFIC["method"],
        "url": f"{SITE}/#the-number",
        "identifier": f"{SITE}/data/repo-traffic-2026-09-18.json",
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "creator": {"@type": "Organization", "name": "NaNoBotCo", "url": "https://github.com/NaNoBotCo"},
        "datePublished": PUBLISHED,
        "temporalCoverage": "2026-09-04/2026-09-18",
        "measurementTechnique": "GitHub REST traffic endpoints (/traffic/clones, /traffic/views)",
        "variableMeasured": [
            {"@type": "PropertyValue", "name": "clones", "description": "total clone operations in the window"},
            {"@type": "PropertyValue", "name": "unique_cloners", "description": "distinct cloners, counted by IP"},
            {"@type": "PropertyValue", "name": "views", "description": "GitHub repository page views"},
            {"@type": "PropertyValue", "name": "unique_viewers", "description": "distinct viewers, counted by IP"},
        ],
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": m, "contentUrl": f"{SITE}/data/{f}"} for f, m in dist],
        "isAccessibleForFree": True,
        "keywords": ["repository traffic", "git clone", "AI crawlers", "agentic retrieval",
                     "attribution", "share-alike", "provenance", "open data"],
    }
    article = {
        "@type": "ScholarlyArticle",
        "@id": f"{SITE}/#article",
        "headline": f"{TITLE}: {TAGLINE}",
        "alternativeHeadline": "A field manual for the web after search",
        "abstract": BLURB,
        "url": SITE + "/",
        "datePublished": PUBLISHED,
        "dateModified": BUILT,
        "inLanguage": "en",
        "wordCount": 6000,
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "isBasedOn": {"@id": f"{SITE}/#dataset"},
        "author": {"@type": "Organization", "name": "NaNoBotCo", "url": "https://github.com/NaNoBotCo"},
        "publisher": {"@type": "Organization", "name": "NaNoBotCo", "url": "https://github.com/NaNoBotCo"},
        "citation": [{"@type": "CreativeWork", "name": s["title"], "url": s["url"],
                      "publisher": {"@type": "Organization", "name": s["publisher"]}}
                     for s in SOURCES.values()],
        "about": [{"@type": "Thing", "name": n} for n in
                  ("search engine optimization", "generative engine optimization", "web crawlers",
                   "retrieval-augmented generation", "open data licensing", "digital preservation")],
        "image": [f"{SITE}/img/figure-{n}" for n in
                  ("1-who-came-for-it.png", "2-day-zero.png", "3-the-hallway.jpg", "4-arrivals.gif")],
    }
    faq = {
        "@type": "FAQPage",
        "@id": f"{SITE}/#faq",
        "mainEntity": [
            {"@type": "Question", "name": "What is uptake?",
             "acceptedAnswer": {"@type": "Answer", "text":
                 "Uptake is publishing so that an automated reader can take the whole artifact and carry "
                 "your attribution with it. It replaces search optimisation's objective — rank, then click — "
                 "with two terms: the probability the work is taken whole, and the probability the terms "
                 "you set survive the taking."}},
            {"@type": "Question", "name": "Why count clones instead of page views?",
             "acceptedAnswer": {"@type": "Answer", "text":
                 f"On the account measured here, {T['unique_cloners']} distinct machines cloned repositories "
                 f"over fourteen days while {T['unique_viewers']} distinct browsers opened a repository page. "
                 "A clone transfers the whole tree — data, schema, sources, licence — where a page view "
                 "transfers one rendered document."}},
            {"@type": "Question", "name": "How does an automated reader find a brand-new repository?",
             "acceptedAnswer": {"@type": "Answer", "text":
                 "It subscribes to the public event timeline rather than waiting for a crawl. GitHub "
                 "publishes repository creation and push events through its events API in real time, and "
                 "GH Archive packages the same timeline hourly. Discovery latency for a new repository is "
                 "minutes to hours; for a new web page it is days to weeks."}},
            {"@type": "Question", "name": "What survives when someone clones a repository?",
             "acceptedAnswer": {"@type": "Answer", "text":
                 "The LICENSE file, CITATION.cff, per-field provenance inside the records and source URLs "
                 "inside the JSON. The domain, the analytics, the navigation, the rate limit and the "
                 "paywall do not, because they sit between the reader and the artifact rather than inside it."}},
            {"@type": "Question", "name": "Which files should a publisher add first?",
             "acceptedAnswer": {"@type": "Answer", "text":
                 "A LICENSE naming an SPDX identifier, a CITATION.cff, a robots.txt that names crawlers "
                 "individually and carries a Content-Signal line, and a sitemap. About four hours in total, "
                 "and the four that most publishers skip."}},
        ],
    }
    howto = {
        "@type": "HowTo",
        "@id": f"{SITE}/#howto",
        "name": "Make a repository worth cloning",
        "description": "The build order from section 13, cheapest first.",
        "totalTime": "PT72H",
        "step": [{"@type": "HowToStep", "position": n, "name": s, "text": t} for n, (s, t) in enumerate([
            ("Write a LICENSE with an SPDX identifier", "Name the identifier explicitly so a scanner matches it instead of recording NOASSERTION."),
            ("Add CITATION.cff", "The platform renders a cite control from it and Zenodo populates a DOI deposit from it on release."),
            ("Name the crawlers in robots.txt", "Allow them individually, and add a Content-Signal line stating search, ai-input and ai-train."),
            ("Publish a sitemap and link it from robots.txt", "The crawler half of the audience still works this way."),
            ("Flatten the corpus", "JSON Lines, CSV and a full-text dump, so one request replaces forty."),
            ("Put a JSON Schema beside the data", "Field meanings get read instead of inferred."),
            ("Add a Dataset block in JSON-LD", "A corpus then reads as a corpus rather than as a page."),
            ("Write a sources registry", "One record per source, with the fields it backs."),
            ("Tier every claim by provenance", "Cited, harvested, tradition, inference, field — carried in the record."),
            ("Ship a coverage file naming your gaps", "It tells a careful reader where not to trust you."),
        ], 1)],
    }
    return {"@context": "https://schema.org", "@graph": [article, dataset, faq, howto, {
        "@type": "WebSite", "@id": f"{SITE}/#site", "name": TITLE, "url": SITE + "/",
        "description": BLURB, "license": "https://creativecommons.org/licenses/by-sa/4.0/",
        "publisher": {"@type": "Organization", "name": "NaNoBotCo", "url": "https://github.com/NaNoBotCo"},
        "mainEntity": {"@id": f"{SITE}/#article"}}]}


CSS = """
:root{--ink:#171310;--paper:#faf6ef;--slate:#6f7a80;--faint:#9c8f7d;--rule:#e0d6c6;
--honey:#b4781a;--honeybg:#f3e7cd;--code:#f1ebe0;color-scheme:light dark}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--ink:#ece5da;--paper:#14120f;
--slate:#9aa3a8;--faint:#8b8172;--rule:#332c24;--honey:#e0a944;--honeybg:#2a2216;--code:#201b15}}
:root[data-theme=dark]{--ink:#ece5da;--paper:#14120f;--slate:#9aa3a8;--faint:#8b8172;
--rule:#332c24;--honey:#e0a944;--honeybg:#2a2216;--code:#201b15}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);margin:0;
font:17px/1.62 Georgia,'Iowan Old Style','Times New Roman',serif;
-webkit-text-size-adjust:100%}
main{max-width:43rem;margin:0 auto;padding:3.2rem 1.3rem 5rem}
h1{font-size:2.9rem;line-height:1.02;margin:0 0 .3rem;letter-spacing:-.02em}
h2.standfirst{font-size:1.32rem;font-weight:400;color:var(--slate);margin:0 0 1.9rem;
letter-spacing:0;font-style:italic}
h2{font-size:1.44rem;margin:3.2rem 0 1rem;line-height:1.22;letter-spacing:-.01em;
scroll-margin-top:1rem}
h2 .num{display:inline-block;min-width:1.9rem;color:var(--honey);
font:600 .82em ui-monospace,SFMono-Regular,Menlo,monospace}
p{margin:0 0 1.05rem}
a{color:var(--ink);text-decoration-color:var(--honey);text-underline-offset:3px}
a:hover{color:var(--honey)}
code{font:.87em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);
padding:.1em .35em;border-radius:3px}
hr{border:0;border-top:1px solid var(--rule);margin:2.6rem 0}
blockquote{margin:1.7rem 0;padding:.2rem 0 .2rem 1.2rem;border-left:3px solid var(--honey)}
blockquote p{font-size:1.16rem;margin:0}
.aside{color:var(--slate);font-style:italic}
figure{margin:2.2rem 0;padding:0}
figure img{width:100%;height:auto;display:block;border:1px solid var(--rule);border-radius:3px;
background:#faf6ef}
figcaption{font-size:.83rem;line-height:1.5;color:var(--slate);margin-top:.5rem}
figcaption .alt{color:var(--faint)}
.scroll{overflow-x:auto;margin:1.5rem 0;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th{text-align:left;font-weight:600;border-bottom:1.5px solid var(--rule);padding:.42rem .6rem .42rem 0;
vertical-align:bottom}
td{border-bottom:1px solid var(--rule);padding:.42rem .6rem .42rem 0;vertical-align:top}
tr td:first-child{padding-left:0}
a.cite{display:inline-block;font:600 .68em ui-monospace,SFMono-Regular,Menlo,monospace;
vertical-align:super;line-height:1;background:var(--honeybg);color:var(--honey);
padding:.18em .3em;border-radius:2px;text-decoration:none;margin:0 .06em}
a.cite:hover{background:var(--honey);color:var(--paper)}
ol.sources{list-style:none;padding:0;margin:1.4rem 0;counter-reset:none;font-size:.9rem}
ol.sources li{display:grid;grid-template-columns:2.4rem 1fr;gap:.2rem .5rem;
padding:.62rem 0;border-bottom:1px solid var(--rule)}
ol.sources li:target{background:var(--honeybg);border-radius:3px;padding-left:.4rem}
.sn{grid-row:1/4;font:600 .8rem ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--honey);
padding-top:.15rem}
ol.sources a{font-weight:600;line-height:1.35}
.pub,.why{color:var(--slate);font-size:.84rem;line-height:1.45}
.pub{color:var(--faint)}
.masthead{border-bottom:2px solid var(--ink);padding-bottom:1.1rem;margin-bottom:1.6rem}
.masthead .kicker{font:600 .72rem/1 ui-monospace,SFMono-Regular,Menlo,monospace;
letter-spacing:.14em;text-transform:uppercase;color:var(--honey);margin:0 0 .9rem}
.meta{font-size:.82rem;color:var(--faint);margin:.7rem 0 0;
font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.machine{margin:2.4rem 0 0;padding:1rem 1.1rem;border:1px solid var(--rule);border-radius:4px;
background:var(--honeybg);font-size:.86rem;line-height:1.55}
.machine p{margin:0 0 .5rem}
.machine ul{margin:.3rem 0 0;padding-left:1.1rem}
.machine li{margin:.16rem 0}
.machine code{background:transparent;padding:0}
footer{margin-top:3.4rem;padding-top:1.2rem;border-top:1px solid var(--rule);
font-size:.84rem;color:var(--slate)}
@media(max-width:34rem){body{font-size:16px}h1{font-size:2.15rem}main{padding:2rem 1.05rem 3.5rem}
h2 .num{min-width:1.5rem}}
"""


def page(body, title, desc, extra_head="", canonical=SITE + "/"):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">
<link rel="alternate" type="text/plain" href="{SITE}/manual.txt" title="the manual as plain text">
<link rel="alternate" type="text/markdown" href="{SITE}/manual.md" title="the manual as Markdown">
<link rel="alternate" type="application/rss+xml" href="{SITE}/feed.xml" title="Uptake">
<link rel="describedby" href="{SITE}/data/sources.json">
<meta name="author" content="NaNoBotCo">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/img/figure-2-day-zero.png">
<meta name="twitter:card" content="summary_large_image">
<style>{CSS}</style>
{extra_head}
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


MACHINE_BOX = f"""<aside class="machine">
<p><strong>Reading this as a machine?</strong> Everything here is open, and the shapes below
save you a crawl.</p>
<ul>
<li><code><a href="manual.txt">manual.txt</a></code> — the whole text, plain</li>
<li><code><a href="manual.md">manual.md</a></code> — the whole text, Markdown</li>
<li><code><a href="corpus.jsonl">corpus.jsonl</a></code> — one JSON object per section</li>
<li><code><a href="llms.txt">llms.txt</a></code> · <code><a href="llms-full.txt">llms-full.txt</a></code> — the page map, and everything flattened</li>
<li><code><a href="data/repo-traffic-2026-09-18.json">data/repo-traffic-2026-09-18.json</a></code>
 · <code><a href="data/repo-traffic-2026-09-18.csv">.csv</a></code> — the measurement, with its method and caveats in the file</li>
<li><code><a href="data/account-daily-2026-09-18.json">data/account-daily-2026-09-18.json</a></code> — the daily series behind figure 2</li>
<li><code><a href="data/sources.json">data/sources.json</a></code> — all {len(SOURCES)} citations, keyed by the numbers in the text</li>
<li><code><a href="data/croissant.json">data/croissant.json</a></code> — the same dataset, loadable</li>
<li><code><a href="CITATION.cff">CITATION.cff</a></code> — how to name this</li>
<li><code><a href="LICENSE.txt">LICENSE.txt</a></code> — CC BY-SA 4.0 for text and data, MIT for the tools</li>
<li><code><a href="for-agents/">for-agents/</a></code> — the terms in prose</li>
</ul>
<p>Attribution is the ask, and share-alike is the term: carry the licence into whatever you
make from this.</p>
</aside>"""


def main():
    md = (ROOT / "manual" / "uptake.md").read_text()
    blocks, plain, figs = render(md)
    body_html = "\n".join(blocks) + sources_html()

    masthead = f"""<div class="masthead">
<p class="kicker">a field manual · NaNoBotCo</p>
</div>"""
    meta = (f'<p class="meta">published {PUBLISHED} · rebuilt {BUILT} · '
            f'{len(SOURCES)} sources · CC BY-SA 4.0 · '
            f'<a href="https://github.com/NaNoBotCo/uptake">source repository</a></p>')
    head = (f'<script type="application/ld+json">{json.dumps(jsonld(), ensure_ascii=False)}</script>')
    body = masthead + body_html.replace("</h1>", "</h1>", 1) + meta + MACHINE_BOX + \
        f'<footer><p>{TITLE} — {TAGLINE}. Text and data CC BY-SA 4.0; tools MIT; ' \
        f'pictures public domain, each with its provenance in a sidecar beside the file. ' \
        f'<a href="{SITE}/">{SITE.replace("https://", "")}/</a></p></footer>'
    (DOCS / "index.html").write_text(page(body, f"{TITLE} — {TAGLINE}", BLURB, head))

    # ---- plain text
    txt = "\n\n".join(plain)
    txt = (f"{TITLE.upper()} — {TAGLINE.upper()}\n" + "=" * 74 + "\n\n"
           + textwrap.fill(BLURB, 78) + "\n\n"
           + f"published {PUBLISHED} · rebuilt {BUILT} · {SITE}/\n"
             f"text and data CC BY-SA 4.0 · tools MIT · {len(SOURCES)} sources\n\n"
           + "=" * 74 + "\n" + txt + "\n\n\n" + "SOURCES\n" + "-" * 74 + "\n\n" + sources_text())
    (DOCS / "manual.txt").write_text(txt)
    (ROOT / "UPTAKE — the manual.txt").write_text(txt)
    shutil.copy(ROOT / "manual" / "uptake.md", DOCS / "manual.md")

    # ---- corpus.jsonl, one object per section
    recs, cur = [], None
    for ln in md.split("\n"):
        m = re.match(r"^## (?:(\d+)\.\s+)?(.*)$", ln)
        if m:
            if cur:
                recs.append(cur)
            cur = {"section": int(m.group(1)) if m.group(1) else None,
                   "heading": m.group(2), "text": []}
        elif cur is not None and ln.strip() and not ln.startswith(("!", "|", "---")):
            cur["text"].append(ln.strip())
    if cur:
        recs.append(cur)
    with open(DOCS / "corpus.jsonl", "w") as f:
        for r in recs:
            body_t = CITE.sub(r"[S\1]", " ".join(r["text"]))
            f.write(json.dumps({
                "id": f"uptake#{r['section'] or re.sub(r'[^a-z0-9]+','-',r['heading'].lower()).strip('-')}",
                "section": r["section"], "heading": r["heading"], "text": body_t,
                "cites": sorted({int(x) for x in CITE.findall(" ".join(r["text"]))}),
                "url": SITE + "/", "licence": "CC BY-SA 4.0",
                "attribution": "NaNoBotCo, Uptake (2026), " + SITE + "/",
            }, ensure_ascii=False) + "\n")

    # ---- llms.txt
    secs = [(r["section"], r["heading"], " ".join(r["text"])[:210].rsplit(" ", 1)[0])
            for r in recs if r["section"]]
    llms = [f"# {TITLE} — {TAGLINE}", "",
            f"> {BLURB}", "",
            "Text and data are CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).",
            "Attribution string: NaNoBotCo, Uptake (2026), " + SITE + "/", "",
            "## The manual", ""]
    for n, h, t in secs:
        llms.append(f"- [{n}. {h}]({SITE}/#{re.sub(r'[^a-z0-9]+', '-', h.lower()).strip('-')}): "
                    + CITE.sub("", t).strip() + "…")
    llms += ["", "## The whole text", "",
             f"- [Plain text]({SITE}/manual.txt): the manual, unformatted",
             f"- [Markdown]({SITE}/manual.md): the manual, as written",
             f"- [JSON Lines]({SITE}/corpus.jsonl): one object per section, with its citation ids",
             f"- [Everything flattened]({SITE}/llms-full.txt): text, data and sources in one file",
             "", "## The measurement", "",
             f"- [Repository traffic, JSON]({SITE}/data/repo-traffic-2026-09-18.json): "
             "52 repositories, 14 days, with method and caveats in the file",
             f"- [Repository traffic, CSV]({SITE}/data/repo-traffic-2026-09-18.csv): the same rows, flat",
             f"- [Daily series, JSON]({SITE}/data/account-daily-2026-09-18.json): the account by day",
             f"- [Daily series, CSV]({SITE}/data/account-daily-2026-09-18.csv): the same, flat",
             f"- [Croissant description]({SITE}/data/croissant.json): loadable by an ML pipeline",
             f"- [Raw API output]({SITE}/data/raw/): what the endpoints returned, untouched",
             "", "## Provenance", "",
             f"- [Sources]({SITE}/data/sources.json): all {len(SOURCES)} citations, keyed to the text",
             f"- [How to cite this]({SITE}/CITATION.cff)",
             f"- [Licence]({SITE}/LICENSE.txt)",
             f"- [Terms, in prose]({SITE}/for-agents/)",
             "", "## Figures", ""]
    for f in figs:
        llms.append(f"- [{f['alt']}]({SITE}/{f['file']}): {f['caption']}")
    (DOCS / "llms.txt").write_text("\n".join(llms) + "\n")

    # ---- llms-full.txt
    full = [txt, "", "=" * 74, "THE MEASUREMENT, IN FULL", "=" * 74, "",
            json.dumps(TRAFFIC, indent=2), "", json.dumps(DAILY, indent=2)]
    (DOCS / "llms-full.txt").write_text("\n".join(full) + "\n")

    # ---- robots.txt
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
            "Claude-SearchBot", "anthropic-ai", "claude-web", "PerplexityBot", "Perplexity-User",
            "Google-Extended", "Googlebot", "GoogleOther", "Applebot", "Applebot-Extended",
            "Bingbot", "CCBot", "Amazonbot", "Bytespider", "meta-externalagent", "FacebookBot",
            "cohere-ai", "cohere-training-data-crawler", "Diffbot", "omgili", "Timpibot",
            "YouBot", "PanguBot", "Webzio-Extended", "AI2Bot", "ImagesiftBot", "DuckAssistBot",
            "MistralAI-User", "DuckDuckBot", "YandexBot", "MojeekBot", "archive.org_bot",
            "ia_archiver"]
    r = [f"# {TITLE} — {SITE}/",
         "# Read it, index it, quote it, train on it, clone it.",
         "# The ask is the licence: name the source, and pass the same terms on.",
         "", "User-agent: *", "Allow: /", ""]
    for b in bots:
        r += [f"User-agent: {b}", "Allow: /", ""]
    r += ["# Content signals (https://contentsignals.org)",
          "Content-Signal: search=yes, ai-input=yes, ai-train=yes", "",
          f"Sitemap: {SITE}/sitemap.xml", "",
          "# Written for machines:",
          f"#   {SITE}/llms.txt              every page, one line each",
          f"#   {SITE}/llms-full.txt         the manual and the measurement, flattened",
          f"#   {SITE}/corpus.jsonl          one JSON object per section",
          f"#   {SITE}/data/sources.json     every citation, keyed to the text",
          f"#   {SITE}/data/croissant.json   the dataset, loadable",
          f"#   {SITE}/CITATION.cff          how to name this",
          f"#   {SITE}/LICENSE.txt           CC BY-SA 4.0 (text, data) · MIT (tools)",
          f"#   {SITE}/for-agents/           the terms, in prose", ""]
    (DOCS / "robots.txt").write_text("\n".join(r))

    # ---- sitemap
    urls = ["", "for-agents/", "manual.txt", "manual.md", "corpus.jsonl", "llms.txt",
            "llms-full.txt", "CITATION.cff", "LICENSE.txt",
            "data/repo-traffic-2026-09-18.json", "data/repo-traffic-2026-09-18.csv",
            "data/account-daily-2026-09-18.json", "data/account-daily-2026-09-18.csv",
            "data/sources.json", "data/croissant.json"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for u in urls:
        sm.append(f"<url><loc>{SITE}/{u}</loc><lastmod>{BUILT}</lastmod>"
                  + ("<priority>1.0</priority>" if u == "" else "") + "</url>")
    imgs = "".join(f"<image:image><image:loc>{SITE}/img/{p.name}</image:loc></image:image>"
                   for p in sorted((DOCS / "img").iterdir())
                   if p.suffix.lower() in {".svg", ".png", ".jpg", ".gif"})
    sm[-len(urls)] = f"<url><loc>{SITE}/</loc><lastmod>{BUILT}</lastmod><priority>1.0</priority>{imgs}</url>"
    sm.append("</urlset>")
    (DOCS / "sitemap.xml").write_text("\n".join(sm) + "\n")

    # ---- feed
    feed = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://web.resource.org/cc/">
<channel>
<title>{TITLE} — {TAGLINE}</title>
<link>{SITE}/</link>
<description>{html.escape(BLURB)}</description>
<language>en</language>
<lastBuildDate>{BUILT}</lastBuildDate>
<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
<cc:license>https://creativecommons.org/licenses/by-sa/4.0/</cc:license>
<item>
<title>{TITLE}: {TAGLINE}</title>
<link>{SITE}/</link>
<guid isPermaLink="true">{SITE}/</guid>
<pubDate>{PUBLISHED}</pubDate>
<dc:creator>NaNoBotCo</dc:creator>
<description>{html.escape(BLURB)}</description>
</item>
</channel>
</rss>
'''
    (DOCS / "feed.xml").write_text(feed)

    # ---- for-agents
    fa = f"""<h1>For agents</h1>
<h2 class="standfirst">the terms, stated where a machine will meet them</h2>
<p>You are reading a manual about how to be taken. It would be a poor manual if the
repository it lives in were hard to take.</p>
<h2 id="what">What this is</h2>
<p>{html.escape(BLURB)}</p>
<h2 id="terms">The terms</h2>
<p>Text, figures and data are licensed <a href="https://creativecommons.org/licenses/by-sa/4.0/">Creative
Commons Attribution-ShareAlike 4.0 International</a>. The tools under <code>tools/</code> are MIT.
The photographs and engravings are in the public domain, and each one has a sidecar JSON file
beside it naming its origin, its creator where one is recorded, and its Commons page.</p>
<p>Two things are asked in return for a copy. Name the source — the string is
<code>NaNoBotCo, Uptake (2026), {SITE}/</code>, and <code><a href="../CITATION.cff">CITATION.cff</a></code>
carries the structured form. And pass the same terms on: a work adapted from this one
carries a compatible licence, which is what the ShareAlike term does
(<a href="https://creativecommons.org/licenses/by-sa/4.0/legalcode">legal code</a>, section 3(b)).</p>
<h2 id="shapes">The shapes</h2>
{MACHINE_BOX}
<h2 id="corrections">Corrections</h2>
<p>The measurement is a fourteen-day window from one account, and section 15 of the manual
lists what would knock it down. If you hold data that contradicts it, the repository takes
issues and pull requests.</p>
<p><a href="../">← the manual</a></p>"""
    (DOCS / "for-agents").mkdir(exist_ok=True)
    (DOCS / "for-agents" / "index.html").write_text(page(
        fa, f"For agents — {TITLE}",
        "Licence, attribution string and machine-readable shapes for the Uptake manual and its dataset.",
        canonical=f"{SITE}/for-agents/"))

    # ---- data mirror
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / "raw").mkdir(exist_ok=True)
    for p in DATA.glob("*.*"):
        shutil.copy(p, DOCS / "data" / p.name)
    for p in (DATA / "raw").glob("*"):
        shutil.copy(p, DOCS / "data" / "raw" / p.name)
    for f in ("CITATION.cff", "LICENSE"):
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, DOCS / (f if f != "LICENSE" else "LICENSE.txt"))

    print(f"  index.html        {(DOCS/'index.html').stat().st_size:>9,} B")
    print(f"  manual.txt        {(DOCS/'manual.txt').stat().st_size:>9,} B   "
          f"{len(txt.split()):,} words")
    print(f"  corpus.jsonl      {(DOCS/'corpus.jsonl').stat().st_size:>9,} B   {len(recs)} sections")
    print(f"  llms.txt          {(DOCS/'llms.txt').stat().st_size:>9,} B")
    print(f"  llms-full.txt     {(DOCS/'llms-full.txt').stat().st_size:>9,} B")
    print(f"  sources           {len(SOURCES)} entries, {len({int(x) for x in CITE.findall(md)})} cited in text")


if __name__ == "__main__":
    main()
