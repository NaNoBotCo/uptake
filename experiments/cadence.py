#!/usr/bin/env python3
"""cadence — the UPTAKE trial's push arms.

Two arms, identical cadence, one variable: whether the push carries real content.

  arm1_noop  a probe file's timestamp changes and nothing else
  arm2_real  a genuine content change, prepared beforehand and already staged
  holdout    never touched (guarded in push_walk.py and by a pre-push hook)

Cadence is what makes the arms comparable, so both fire on the same days or the
comparison is worthless. If arm2 has no real change staged for a repo on a push
day, that repo is SKIPPED and logged — a manufactured "real" change is a no-op
wearing a costume and would collapse the two arms into one.

Run: python3 cadence.py [--dry-run] [--arm arm1_noop]
"""
import json, subprocess, datetime, pathlib, sys, re

HERE = pathlib.Path(__file__).resolve().parent
ASSIGN = HERE / "cadence-ab-assignment.json"
LOG = HERE / "cadence.log"
CLONES = HERE / "localclones.json"

CASE_IDS = re.compile(
    r"2:26-cv-01775|26-cv-01775|25CV0545|FL1000577|Hulett|Peacock v\.? Peacock"
    r"|Sean Somers|peacocksettlement|Triple B", re.I)

PROBE = ".cadence-probe"
PROBE_TEXT = """UPTAKE cadence trial — probe file.

This file exists to change, and to change nothing else. It is one arm of a public
experiment testing whether a repository push draws machine readers when the push
carries no new content. The other arm ships real changes on the same schedule.

Window: 2026-09-19 .. 2026-10-03
Method and results: https://nanobotco.github.io/uptake/

Last touched: {stamp}
"""


def log(line):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"{stamp}  {line}"
    print(msg, flush=True)
    with open(LOG, "a") as fh:
        fh.write(msg + "\n")


def git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)


def push_one(repo_dir, name, dry):
    """Commit whatever is staged/changed in this repo and push it. Guarded."""
    st = git(repo_dir, "status", "--porcelain").stdout.strip()
    if not st:
        log(f"SKIP   {name}: nothing to commit")
        return False
    diff = git(repo_dir, "diff", "HEAD").stdout
    hits = sorted(set(m.group(0) for m in CASE_IDS.finditer(diff)))
    if hits:
        log(f"BLOCKED {name}: case identifiers in diff -> {hits}. NOT PUSHED.")
        return False
    if dry:
        log(f"DRY    {name}: would commit + push ({len(st.splitlines())} paths)")
        return False
    git(repo_dir, "add", "-A")
    today = datetime.date.today().isoformat()
    git(repo_dir, "commit", "-m", f"Cadence trial: scheduled push {today}")
    r = git(repo_dir, "push", "origin", "HEAD")
    if r.returncode == 0:
        log(f"PUSHED {name}")
        return True
    log(f"FAIL   {name}: {(r.stderr.strip().splitlines() or ['?'])[-1]}")
    return False


def main():
    dry = "--dry-run" in sys.argv
    only = None
    if "--arm" in sys.argv:
        only = sys.argv[sys.argv.index("--arm") + 1]

    a = json.loads(ASSIGN.read_text())
    today = datetime.date.today().isoformat()
    if today not in a["push_days"]:
        log(f"not a push day ({today}); next = "
            f"{[d for d in a['push_days'] if d >= today][:1] or ['none']}")
        return 0
    clones = json.loads(CLONES.read_text()) if CLONES.exists() else {}
    n = 0
    for arm in ("arm1_noop", "arm2_real"):
        if only and arm != only:
            continue
        for name in a["arms"][arm]:
            d = clones.get(name)
            if not d:
                log(f"SKIP   {name}: no local clone mapped")
                continue
            d = pathlib.Path(d)
            if arm == "arm1_noop":
                (d / PROBE).write_text(PROBE_TEXT.format(
                    stamp=datetime.datetime.now().isoformat(timespec="seconds")))
            n += push_one(d, f"[{arm}] {name}", dry)
    log(f"cadence done — {n} pushed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
