"""Run ENHSP on the numeric problems with several configurations.

  python3 tools/run_numeric.py [--timeout 120] [--enhsp path/to/enhsp.jar]

Also runs a small sensitivity study on the hit penalty of the metric
(steps + K*hits, K in {1, 3, 10}) to show the trade-off between a shorter
path and lost lives. Writes results/numeric.csv and results/plans/numeric/.
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(__file__))
from maps import MAPS  # noqa: E402
from validate import parse_plan, validate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.environ.get("PACMAN_RESULTS", "results")   # run_all.py --quick uses results_quick
def _package_file(package, *parts):
    """Path of a file shipped inside an installed pip package (works on Windows, macOS, Linux)."""
    import importlib.util
    spec = importlib.util.find_spec(package)
    if spec is None or not spec.submodule_search_locations:
        return None
    return os.path.join(list(spec.submodule_search_locations)[0], *parts)


DEFAULT_ENHSP = os.environ.get("ENHSP_JAR") or _package_file("up_enhsp", "ENHSP", "enhsp.jar")

CONFIGS = [
    ("GBFS hadd",       ["-s", "gbfs", "-h", "hadd"], False),
    ("sat-hmrp",        ["-planner", "sat-hmrp"], False),
    ("A* blind",        ["-planner", "opt-blind"], True),
    ("A* hrmax",        ["-planner", "opt-hrmax"], True),
]


def grab(pattern, text, cast=float):
    m = re.findall(pattern, text)
    return cast(m[-1]) if m else ""


def run(jar, domain, problem, args, timeout):
    work = tempfile.mkdtemp(prefix="enhsp_")
    plan = os.path.join(work, "plan")
    cmd = ["java", "-Xmx4g", "-jar", jar, "-o", domain, "-f", problem, "-sp", plan] + args
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=timeout)
        out, status = p.stdout + p.stderr, None
    except subprocess.TimeoutExpired as e:
        out, status = (e.stdout or b"").decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout"
    wall = round(time.time() - t0, 2)
    if status is None:
        if "Problem Solved" in out and os.path.exists(plan):
            status = "solved"
        elif "OutOfMemory" in out:
            status = "out of memory"
        elif "Problem unsolvable" in out or "unsolvable" in out.lower():
            status = "unsolvable"
        else:
            status = "failed"
    return dict(status=status, expanded=grab(r"Expanded Nodes:(\d+)", out, int),
                metric=grab(r"Metric \(Search\):([\d.]+)", out), total_time=wall,
                plan=plan if status == "solved" else None)


def with_penalty(problem_file, k):
    text = open(problem_file).read()
    text = re.sub(r"\(\* \d+ \(hits\)\)", f"(* {k} (hits))", text)
    path = os.path.join(tempfile.mkdtemp(prefix="pen_"), os.path.basename(problem_file))
    open(path, "w").write(text)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--enhsp", default=DEFAULT_ENHSP)
    ap.add_argument("--problems", nargs="*", default=list(MAPS))
    a = ap.parse_args()
    domain = os.path.join(ROOT, "numeric", "domain.pddl")
    os.makedirs(os.path.join(ROOT, RESULTS, "plans", "numeric"), exist_ok=True)
    rows = []

    def record(prob, label, opt, penalty, r):
        length, hits, valid = "", "", ""
        if r["plan"]:
            steps = parse_plan(r["plan"])
            ok, msg = validate("numeric", prob, steps)
            length = len(steps)
            m = re.search(r"(\d+) hits", msg)
            hits = int(m.group(1)) if m else ""
            valid = "yes" if ok else "NO: " + msg
            slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
            dst = os.path.join(ROOT, RESULTS, "plans", "numeric", f"{prob}_k{penalty}_{slug}.plan")
            open(dst, "w").write(open(r["plan"]).read())
        rows.append(dict(problem=prob, config=label, optimal_config=opt, hit_penalty=penalty,
                         status=r["status"], plan_length=length, hits=hits,
                         metric=r["metric"], valid=valid, expanded=r["expanded"],
                         total_time_s=r["total_time"]))
        print(f"{prob} k={penalty:<2} {label:10} {r['status']:9} len={length!s:4} hits={hits!s:2} "
              f"metric={r['metric']!s:6} exp={r['expanded']!s:9} t={r['total_time']}s valid={valid}",
              flush=True)

    for prob in a.problems:
        pfile = os.path.join(ROOT, "numeric", "problems", f"{prob}.pddl")
        for label, args, opt in CONFIGS:
            record(prob, label, opt, 10, run(a.enhsp, domain, pfile, args, a.timeout))
    # sensitivity of the optimal plan to the hit penalty
    for prob in a.problems[:3]:
        for k in (1, 3):
            pfile = with_penalty(os.path.join(ROOT, "numeric", "problems", f"{prob}.pddl"), k)
            record(prob, "A* hrmax", True, k,
                   run(a.enhsp, domain, pfile, ["-planner", "opt-hrmax"], a.timeout))

    out = os.path.join(ROOT, RESULTS, "numeric.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("written", out)


if __name__ == "__main__":
    main()
