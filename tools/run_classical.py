"""Run Fast Downward on every classical problem with several heuristics.

  python3 tools/run_classical.py [--timeout 300] [--fd path/to/fast-downward.py]

Writes results/classical.csv and the plans in results/plans/classical/.
Every plan is checked with tools/validate.py.
"""
import argparse
import csv
import os
import re
import signal
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


DEFAULT_FD = os.environ.get("FAST_DOWNWARD") or _package_file(
    "up_fast_downward", "downward", "fast-downward.py")

# (label, encoding, Fast Downward arguments, optimal?)
CONFIGS = [
    ("A* blind",      "adl",    ["--search", "astar(blind())"], True),
    ("A* hmax",       "adl",    ["--search", "astar(hmax())"], True),
    ("GBFS hFF",      "adl",    ["--search", "eager_greedy([ff()])"], False),
    ("LAMA-first",    "adl",    ["--alias", "lama-first"], False),
    ("A* LM-cut",     "adl",    ["--search", "astar(lmcut())"], True),
    ("A* blind",      "strips", ["--search", "astar(blind())"], True),
    ("A* hmax",       "strips", ["--search", "astar(hmax())"], True),
    ("A* LM-cut",     "strips", ["--search", "astar(lmcut())"], True),
    ("GBFS hFF",      "strips", ["--search", "eager_greedy([ff()])"], False),
    ("LAMA-first",    "strips", ["--alias", "lama-first"], False),
]


def grab(pattern, text, cast=float, last=True):
    m = re.findall(pattern, text)
    return cast(m[-1] if last else m[0]) if m else ""


def run(fd, encoding, problem, args, timeout):
    domain = os.path.join(ROOT, "classical", f"domain_{encoding}.pddl")
    pfile = os.path.join(ROOT, "classical", "problems", encoding, f"{problem}.pddl")
    work = tempfile.mkdtemp(prefix="fd_")
    plan = os.path.join(work, "plan")
    cmd = [sys.executable, fd, "--plan-file", plan]
    # Fast Downward can set time/memory limits itself only on Linux; on macOS and
    # Windows asking for them makes it stop immediately, so there the timeout is
    # enforced here instead (killing the whole process group).
    use_fd_limits = sys.platform.startswith("linux") and not os.environ.get("PACMAN_NO_FD_LIMITS")
    if use_fd_limits:
        cmd += ["--overall-time-limit", f"{timeout}s", "--overall-memory-limit", "4G"]
    if args[0] == "--alias":
        cmd = cmd[:2] + args + cmd[2:]
        cmd += [domain, pfile]
    else:
        cmd += [domain, pfile] + args
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, start_new_session=(os.name != "nt"))
    killed = False
    try:
        out, _ = proc.communicate(timeout=None if use_fd_limits else timeout)
    except subprocess.TimeoutExpired:
        killed = True
        if os.name != "nt":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
        out, _ = proc.communicate()
    wall = time.time() - t0
    res = {
        "operators": grab(r"Translator operators: (\d+)", out, int),
        "axioms": grab(r"Translator axioms: (\d+)", out, int),
        "expanded": grab(r"Expanded (\d+) state", out, int),
        "generated": grab(r"Generated (\d+) state", out, int),
        "search_time": grab(r"Search time: ([\d.]+)s", out),
        "total_time": round(wall, 2),
    }
    if "does not support axioms" in out or "Tried to use unsupported feature" in out:
        res["status"] = "unsupported (axioms/cond. effects)"
    elif "Solution found" in out:
        res["status"] = "solved"
    elif killed or "Time limit" in out or "timeout" in out.lower():
        res["status"] = "timeout"
    elif "Memory limit" in out or "memory" in out.lower() and "exceeded" in out.lower():
        res["status"] = "out of memory"
    else:
        res["status"] = "failed"
        res["log_tail"] = "\n".join(out.strip().splitlines()[-8:])
    plans = [f for f in os.listdir(work) if f.startswith("plan")]
    res["plan_file"] = os.path.join(work, sorted(plans)[-1]) if plans else None
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--fd", default=DEFAULT_FD)
    ap.add_argument("--problems", nargs="*", default=list(MAPS))
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, RESULTS, "plans", "classical"), exist_ok=True)
    rows = []
    for prob in a.problems:
        for label, enc, args, opt in CONFIGS:
            r = run(a.fd, enc, prob, args, a.timeout)
            length, valid = "", ""
            if r["status"] == "solved" and r["plan_file"]:
                steps = parse_plan(r["plan_file"])
                ok, msg = validate("classical", prob, steps)
                length, valid = len(steps), ("yes" if ok else "NO: " + msg)
                slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
                dst = os.path.join(ROOT, RESULTS, "plans", "classical", f"{prob}_{enc}_{slug}.plan")
                with open(r["plan_file"]) as src, open(dst, "w") as d:
                    d.write(src.read())
            row = dict(problem=prob, encoding=enc, config=label, optimal_config=opt,
                       status=r["status"], plan_length=length, valid=valid,
                       expanded=r["expanded"], generated=r["generated"],
                       search_time_s=r["search_time"], total_time_s=r["total_time"],
                       operators=r["operators"], axioms=r["axioms"])
            rows.append(row)
            print(f"{prob} {enc:6} {label:11} {r['status']:12} len={length!s:4} "
                  f"exp={r['expanded']!s:9} t={r['total_time']}s valid={valid}", flush=True)
            if r.get("log_tail"):
                print("    Fast Downward output (last lines):\n    " + r["log_tail"].replace("\n", "\n    "), flush=True)
    out = os.path.join(ROOT, RESULTS, "classical.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("written", out)


if __name__ == "__main__":
    main()
