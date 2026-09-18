==============================================================================
UPTAKE
==============================================================================


PUBLISHING FOR MACHINES THAT COPY. A field manual for the web after search,
built on a measurement rather than a theory.

READ IT: https://nanobotco.github.io/uptake/ · plain text
(https://nanobotco.github.io/uptake/manual.txt) · Markdown
(https://nanobotco.github.io/uptake/manual.md) · JSON Lines
(https://nanobotco.github.io/uptake/corpus.jsonl)

------------------------------------------------------------------------------


THE FINDING
------------------------------------------------------------------------------


Fourteen days, fifty-two repositories on one GitHub account, no promotion of
any kind:

      CLONE OPERATIONS
          961

      DISTINCT MACHINES THAT CLONED
          501

      GITHUB PAGE VIEWS
          36

      DISTINCT BROWSERS THAT VIEWED
          20

      CLONERS PER VIEWER
          25.1

      REPOSITORIES WITH FIVE OR MORE CLONERS AND ZERO VIEWERS
          23 OF 52


On 16 September 2026 seven directories went public in one evening. That day
drew 617 CLONE OPERATIONS FROM 267 DISTINCT MACHINES — the twelve days before
it total 293 between them. The largest of the seven was created at 04:54 UTC
and cloned 130 times by 69 machines before the day was out, with one referrer
and four human page views. Nothing linked to it. It was hours old.

A new repository is not a document somebody has to find. It is a row in a
public event stream that anyone can subscribe to, and the subscribers arrive
within the hour.

the fourteen-day clone series

WHAT THE MANUAL COVERS
------------------------------------------------------------------------------


  1.  The number
  2.  What a clone is, and what a click was
  3.  The measurement, and what it cannot say
  4.  Day zero
  5.  Three bots wearing one coat
  6.  The objective function moved
  7.  The artifact, not the page
  8.  The hallway
  9.  Provenance is the product
  10.  The licence is the only thing that travels
  11.  What to count now
  12.  What does not work
  13.  The tactics, in order of cost
  14.  Posterity
  15.  What would falsify this

Plus a colophon on why the thing is shaped this way, and 54 sources.

THE MEASUREMENT
------------------------------------------------------------------------------


Everything the manual cites is in data/, with the collection method and the
caveats written into the files rather than into a caption.

      data/repo-traffic-2026-09-18.json (data/repo-traffic-2026-09-18.json)
          what it is: one record per repository, with totals and caveats

      data/repo-traffic-2026-09-18.csv (data/repo-traffic-2026-09-18.csv)
          what it is: the same rows, flat

      data/account-daily-2026-09-18.json (data/account-daily-2026-09-18.json)
          what it is: the daily series behind the chart

      data/account-daily-2026-09-18.csv (data/account-daily-2026-09-18.csv)
          what it is: the same, flat

      DATA/SOURCES.JSON (DATA/SOURCES.JSON)
          what it is: all 54 citations, keyed to the numbers in the text

      DATA/CROISSANT.JSON (DATA/CROISSANT.JSON)
          what it is: the dataset as MLCommons Croissant, loadable by a
              pipeline

      DATA/RAW/ (DATA/RAW/)
          what it is: what the GitHub endpoints returned, untouched


The window is a rolling fourteen days because that is all GitHub retains.
Uniques are counted by IP. The endpoints carry no user agent. Section 3 of the
manual states what those limits rule out, and section 15 lists the control
experiment that has not been run.

WRITTEN FOR MACHINES
------------------------------------------------------------------------------


      LLMS.TXT (DOCS/LLMS.TXT)
          every page and file, one line each

      LLMS-FULL.TXT (DOCS/LLMS-FULL.TXT)
          the manual and the measurement, flattened

      CORPUS.JSONL (DOCS/CORPUS.JSONL)
          one JSON object per section, with its citation ids and attribution
              string

      ROBOTS.TXT (DOCS/ROBOTS.TXT)
          38 crawlers allowed by name, with a Content-Signal line

      SITEMAP.XML (DOCS/SITEMAP.XML)
          pages and images

      CITATION.CFF (CITATION.CFF)
          how to name this

      FOR-AGENTS/ (HTTPS://NANOBOTCO.GITHUB.IO/UPTAKE/FOR-AGENTS/)
          the terms, in prose


The published page carries JSON-LD for ScholarlyArticle, Dataset, FAQPage,
HowTo and WebSite, with all 54 citations in the article's citation array.

FIGURES
------------------------------------------------------------------------------


Four, drawn by tools/figures.py from the data in data/, in four formats. The
SVG keeps its labels as text, so a machine reading the file gets 617 clones
from 267 distinct machines as a string rather than as pixels; the PNG and JPG
are rendered from that same SVG by the build, so raster and vector cannot
drift apart.

      FIGURE 1 (DOCS/IMG/FIGURE-1-WHO-CAME-FOR-IT.SVG)
          unique cloners against unique page viewers — SVG, PNG

      FIGURE 2 (DOCS/IMG/FIGURE-2-DAY-ZERO.SVG)
          clones per day, and the spike — SVG, PNG

      FIGURE 3 (DOCS/IMG/FIGURE-3-THE-HALLWAY.SVG)
          the seven files an arriving agent can pick up — SVG, JPG

      FIGURE 4 (DOCS/IMG/FIGURE-4-ARRIVALS.GIF)
          the same fourteen days, revealed one at a time — GIF


Five public-domain pictures sit alongside them, each with a sidecar JSON file
naming its Commons page, its creator where one is recorded, and its licence
statement.

LICENCE
------------------------------------------------------------------------------


Text, figures and data: CC BY-SA 4.0 — attribution and share-alike. Tools:
MIT. Pictures: public domain, not relicensed here. Full terms in LICENSE
(LICENSE).

Cite it as:

      NaNoBotCo, Uptake: publishing for machines that copy (2026),
      https://nanobotco.github.io/uptake/


Two asks for a copy: name the source, and pass the same terms on. Share-alike
binds the visible reuse — the fork, the republished dataset, the derivative
directory. Whether it reaches a model's weights is unsettled law, and the
manual says so rather than pretending otherwise.

BUILD IT
------------------------------------------------------------------------------


      python3 tools/fetch_images.py    # public-domain pictures, with their sidecars
      python3 tools/figures.py         # four figures, four formats, from data/
      python3 tools/build.py           # docs/ — page, plain text, corpus, llms.txt, robots, sitemap, feed


Standard library only, except Pillow for the animated frames and rsvg-convert
for the raster passes.

CORRECTIONS
------------------------------------------------------------------------------


The finding is one account over one fortnight. Contradicting data is worth
more here than agreement — issues and pull requests are open.


---

Contact: Nan · nan@motdang.net · Sponsor: ko-fi.com/defiantchiangmai · patreon.com/nanobotco
