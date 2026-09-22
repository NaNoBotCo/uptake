#!/usr/bin/env python3
"""snapshot — capture every NaNoBotCo repo's traffic before GitHub drops it.

GitHub keeps 14 days of traffic and no more. The trial needs per-day resolution
over a 14-day window, so the window has to be captured while it exists: one row
per repo per day, appended to a ledger that outlives the API.

Idempotent by (repo, day): re-running on the same day overwrites that day's rows
rather than doubling them, because GitHub revises the current day's counts as it
goes and the last read of a day is the right one.

Run: python3 snapshot.py
"""
import json, subprocess, datetime, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = HERE / "traffic-ledger.jsonl"
COMMITS = HERE / "commit-ledger.jsonl"
POPULAR = HERE / "popular-ledger.jsonl"


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def repos():
    r = subprocess.run(
        ["gh", "repo", "list", "NaNoBotCo", "--limit", "200", "--json", "name",
         "--jq", ".[].name"], capture_output=True, text=True)
    return [x for x in r.stdout.split() if x]


def main():
    today = datetime.date.today().isoformat()
    rows, crows, prows = [], [], []
    names = repos()
    if not names:
        print("no repos returned — is gh authed?", file=sys.stderr)
        return 1
    for n in names:
        c = gh(f"repos/NaNoBotCo/{n}/traffic/clones")
        v = gh(f"repos/NaNoBotCo/{n}/traffic/views")
        if c is None:
            continue
        cv = {x["timestamp"][:10]: x for x in (v or {}).get("views", [])}
        for x in c.get("clones", []):
            d = x["timestamp"][:10]
            vv = cv.get(d, {})
            rows.append({"repo": n, "day": d, "clones": x["count"],
                         "cloners": x["uniques"], "views": vv.get("count", 0),
                         "viewers": vv.get("uniques", 0), "read_on": today})
        # referrers and fetched paths: a 14-day rolling window too, gone once dropped
        for kind in ("referrers", "paths"):
            for x in (gh(f"repos/NaNoBotCo/{n}/traffic/popular/{kind}") or []):
                prows.append({"repo": n, "kind": kind,
                              "what": x.get("referrer") or x.get("path"),
                              "count": x["count"], "uniques": x["uniques"],
                              "read_on": today})
        since = (datetime.date.today() - datetime.timedelta(days=15)).isoformat()
        cm = gh(f"repos/NaNoBotCo/{n}/commits?since={since}T00:00:00Z&per_page=100")
        for x in (cm or []):
            crows.append({"repo": n, "sha": x["sha"][:12],
                          "day": x["commit"]["committer"]["date"][:10],
                          "date": x["commit"]["committer"]["date"],
                          "msg": x["commit"]["message"].splitlines()[0][:120],
                          "read_on": today})

    # idempotent by (repo, day, read_on-day): drop any prior rows read today
    def rewrite(path, new, key):
        old = []
        if path.exists():
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                o = json.loads(line)
                if o.get("read_on") != today:
                    old.append(o)
        seen, out = set(), []
        for o in old + new:
            k = key(o)
            if k in seen:
                continue
            seen.add(k)
            out.append(o)
        path.write_text("".join(json.dumps(o, sort_keys=True) + "\n" for o in out))
        return len(out)

    n1 = rewrite(LEDGER, rows, lambda o: (o["repo"], o["day"], o["read_on"]))
    n2 = rewrite(COMMITS, crows, lambda o: (o["repo"], o["sha"]))
    n3 = rewrite(POPULAR, prows, lambda o: (o["repo"], o["kind"], o["what"], o["read_on"]))
    print(f"{today}: {len(names)} repos · traffic ledger {n1} rows · commit ledger {n2} rows · popular {n3} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
