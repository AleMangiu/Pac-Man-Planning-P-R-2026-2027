"""Rebuild all models and rerun the experiments (works on Windows, macOS and Linux).

  python run_all.py           full run (takes about 1-2 hours)
  python run_all.py --quick   quick check on p01-p02 (a couple of minutes), writes results_quick/
"""
import os
import subprocess
import sys

QUICK = "--quick" in sys.argv
if QUICK:   # never overwrite the full results used in the slides
    os.environ["PACMAN_RESULTS"] = "results_quick"
PY = sys.executable


def run(*args):
    print("\n>>>", " ".join(args), flush=True)
    subprocess.run([PY, *args], check=True)


run("tools/gen.py")
if QUICK:
    run("tools/run_classical.py", "--timeout", "30", "--problems", "p01", "p02")
    run("tools/run_numeric.py", "--timeout", "30", "--problems", "p01", "p02")
    run("tools/run_rddl.py", "--episodes", "5", "--rollout-episodes", "2", "--problems", "p01", "p02")
else:
    run("tools/run_classical.py", "--timeout", "300")
    run("tools/run_numeric.py", "--timeout", "300")
    run("tools/run_rddl.py", "--episodes", "30", "--rollout-episodes", "12",
        "--problems", "p01", "p02", "p03", "p04")
    run("tools/run_rddl.py", "--episodes", "30", "--rollout-episodes", "6",
        "--problems", "p05", "--append")
print("\nDone: results in the", "results_quick/" if QUICK else "results/", "folder.")
