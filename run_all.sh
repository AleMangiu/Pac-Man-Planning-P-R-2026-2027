#!/usr/bin/env bash
# Rebuild every model and rerun all the experiments.
# Requirements: python3, java (for ENHSP), and
#   pip install up-fast-downward up-enhsp pyRDDLGym
# Paths can be overridden with FAST_DOWNWARD=/path/fast-downward.py and ENHSP_JAR=/path/enhsp.jar
set -e
cd "$(dirname "$0")"
python3 tools/gen.py                                   # PDDL/RDDL files from tools/maps.py
python3 tools/run_classical.py --timeout 300           # Fast Downward, 5 problems x 10 configs
python3 tools/run_numeric.py   --timeout 300           # ENHSP, 5 problems x 4 configs + penalty study
python3 tools/run_rddl.py --episodes 30 --rollout-episodes 12 --problems p01 p02 p03 p04   # pyRDDLGym policies
python3 tools/run_rddl.py --episodes 30 --rollout-episodes 6 --problems p05 --append   # slow: ~2 s per rollout decision
