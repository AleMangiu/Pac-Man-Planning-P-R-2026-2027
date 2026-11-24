"""Evaluate policies on the probabilistic Pac-Man (rddl/domain.rddl) with pyRDDLGym.

  python3 tools/run_rddl.py [--episodes 30] [--problems p01 p02 p03 p04]

The environment dynamics are always those of the RDDL model, simulated by
pyRDDLGym. Policies compared:

  random        uniform choice among adjacent cells and waiting
  open-loop     the optimal/feasible plan of the classical (deterministic)
                model, executed blindly: shows what happens when the
                stochastic ghosts break the assumptions of classical planning
  greedy        reactive heuristic: shortest path to the nearest dot or pill
                that avoids the cells a living ghost can occupy at the next
                step (replans at every step)
  rollout       online Monte-Carlo planner that uses the RDDL model itself as
                a generative model: for every candidate action it simulates
                N futures with pyRDDLGym (greedy policy after the first step)
                and picks the action with the best average return
                (rollout algorithm / one-step policy improvement over greedy)

Writes results/rddl_episodes.csv and results/rddl_summary.csv.
"""
import argparse
import csv
import glob
import os
import random
import re
import sys
import time
from collections import deque

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from game import Game, cell_name  # noqa: E402
from maps import MAPS  # noqa: E402
from validate import parse_plan  # noqa: E402

import pyRDDLGym  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.environ.get("PACMAN_RESULTS", "results")   # run_all.py --quick uses results_quick
CELL = re.compile(r"c(\d+)_(\d+)")


class PacmanMDP:
    """Thin wrapper around a pyRDDLGym simulator with state save/restore."""

    def __init__(self, name, seed):
        self.name = name
        self.game = Game(MAPS[name], name)
        self.env = pyRDDLGym.make(os.path.join(ROOT, "rddl", "domain.rddl"),
                                  os.path.join(ROOT, "rddl", "instances", f"{name}.rddl"),
                                  vectorized=True)
        self.env.reset(seed=seed)
        self.sim = self.env.sampler
        self.model = self.env.model
        self.horizon = self.env.horizon
        self.cells = [tuple(map(int, CELL.fullmatch(c).groups()))
                      for c in self.model.type_to_objects["cell"]]
        self.state_keys = list(self.model.state_fluents)
        self._act_cache = {}

    # --- state handling ----------------------------------------------------
    def reset(self):
        self.sim.reset()

    def snapshot(self):
        return {k: np.copy(self.sim.subs[k]) for k in self.state_keys}

    def restore(self, snap):
        for k, v in snap.items():
            self.sim.subs[k] = np.copy(v)

    def decode(self):
        s = self.sim.subs
        pac = self.cells[int(np.argmax(s["pacman-at"]))]
        dots = {self.cells[i] for i in np.flatnonzero(s["dot"])}
        pills = {self.cells[i] for i in np.flatnonzero(s["pill"])}
        ghosts = []
        for k, cyc in enumerate(self.game.cycles):
            i = int(np.argmax(s["ghost-step"][k]))
            ghosts.append(dict(alive=bool(s["ghost-alive"][k]), cell=cyc[i],
                               nxt=cyc[(i + 1) % len(cyc)]))
        return dict(pac=pac, dots=dots, pills=pills, ghosts=ghosts,
                    power=int(s["power"]), caught=bool(s["caught"]))

    # --- dynamics ---------------------------------------------------------
    def step(self, target):
        """target: cell to move to, or None to wait."""
        key = target
        if key not in self._act_cache:
            acts = {} if target is None else {f"move___{cell_name(target)}": True}
            self._act_cache[key] = self.sim.prepare_actions_for_sim(acts)
        acts = {k: np.copy(v) for k, v in self._act_cache[key].items()}
        _, reward, _ = self.sim.step(acts)
        return float(reward)


# ------------------------------------------------------------------------- #
# policies
# ------------------------------------------------------------------------- #
def options(game, st):
    return [None] + list(game.adj[st["pac"]])


def random_policy(game, st, rng):
    return rng.choice(options(game, st))


def greedy_policy(game, st, rng, eps=0.0):
    """Shortest path to the nearest dot/pill. Only the first step must avoid the
    cells that a living ghost may occupy after this step (its cell and its next
    patrol cell); further steps ignore ghosts because the policy replans anyway."""
    if eps and rng.random() < eps:
        return rng.choice(options(game, st))
    pac = st["pac"]
    unsafe = set()
    if st["power"] <= 0:
        for g in st["ghosts"]:
            if g["alive"]:
                unsafe |= {g["cell"], g["nxt"]}
    targets = st["dots"] | st["pills"]
    best = None
    for first in game.adj[pac]:
        if first in unsafe:
            continue
        # BFS distance from `first` to the nearest target
        dist, q, d = {first: 0}, deque([first]), None
        while q:
            c = q.popleft()
            if c in targets:
                d = dist[c]
                break
            for n in game.adj[c]:
                if n not in dist:
                    dist[n] = dist[c] + 1
                    q.append(n)
        if d is not None and (best is None or d < best[0]):
            best = (d, first)
    if best:
        return best[1]
    if pac not in unsafe:
        return None
    safe = [n for n in game.adj[pac] if n not in unsafe]
    return rng.choice(safe) if safe else rng.choice(options(game, st))


class RolloutPolicy:
    def __init__(self, name, seed, n_rollouts, depth):
        self.planner = PacmanMDP(name, seed + 10_000)   # separate simulator for look-ahead
        self.n, self.depth = n_rollouts, depth
        self.rng = random.Random(seed)

    def __call__(self, game, st, rng, real):
        snap = real.snapshot()
        default = greedy_policy(game, st, rng)
        cands = [default] + [a for a in options(game, st) if a != default]
        best, best_val = None, -float("inf")
        for a in cands:
            total = 0.0
            for _ in range(self.n):
                self.planner.restore(snap)
                ret = self.planner.step(a)
                for _ in range(self.depth - 1):
                    s2 = self.planner.decode()
                    if s2["caught"] or not s2["dots"]:
                        break
                    ret += self.planner.step(greedy_policy(game, s2, self.rng, eps=0.1))
                total += ret
            val = total / self.n
            if val > best_val + 1e-9:
                best, best_val = a, val
        return best


def open_loop_plan(name):
    """Best classical plan found by the experiments (optimal if available)."""
    folder = os.path.join(ROOT, RESULTS, "plans", "classical")
    for pat in ("strips_a_lm_cut", "strips_a_hmax", "strips_a_blind", "strips_lama_first", "adl_lama_first"):
        f = os.path.join(folder, f"{name}_{pat}.plan")
        if os.path.exists(f):
            seq = []
            for toks in parse_plan(f):
                cs = [tuple(map(int, m.groups())) for m in (CELL.fullmatch(x) for x in toks[1:]) if m]
                seq.append(None if toks[0].startswith("wait") else cs[1])
            return seq, pat
    return None, None


# ------------------------------------------------------------------------- #
def run_episode(name, policy_name, seed, args):
    mdp = PacmanMDP(name, seed)
    game, rng = mdp.game, random.Random(seed)
    mdp.reset()
    plan = None
    if policy_name == "open-loop":
        plan, _ = open_loop_plan(name)
    roll = RolloutPolicy(name, seed, args.rollouts, args.depth) if policy_name == "rollout" else None
    total, steps, t_dec = 0.0, 0, 0.0
    start_dots = len(game.dots)
    for t in range(mdp.horizon):
        st = mdp.decode()
        if st["caught"] or not st["dots"]:
            break
        t0 = time.time()
        if policy_name == "random":
            a = random_policy(game, st, rng)
        elif policy_name == "greedy":
            a = greedy_policy(game, st, rng)
        elif policy_name == "open-loop":
            a = plan[t] if t < len(plan) else None
        else:
            a = roll(game, st, rng, mdp)
        t_dec += time.time() - t0
        total += mdp.step(a)
        steps += 1
    st = mdp.decode()
    return dict(problem=name, policy=policy_name, seed=seed, total_reward=round(total, 1),
                won=int(not st["dots"] and not st["caught"]), caught=int(st["caught"]),
                steps=steps, dots_eaten=start_dots - len(st["dots"]),
                ghosts_eaten=sum(not g["alive"] for g in st["ghosts"]),
                ms_per_decision=round(1000 * t_dec / max(steps, 1), 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=30)
    ap.add_argument("--problems", nargs="*", default=["p01", "p02", "p03", "p04", "p05"])
    ap.add_argument("--policies", nargs="*", default=["random", "open-loop", "greedy", "rollout"])
    ap.add_argument("--rollouts", type=int, default=8)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--rollout-episodes", type=int, default=None,
                    help="episodes for the (slow) rollout policy, default = --episodes")
    ap.add_argument("--append", action="store_true",
                    help="keep the results already in results/, replacing only the problem/policy pairs run now")
    a = ap.parse_args()
    rows = []
    old = os.path.join(ROOT, RESULTS, "rddl_episodes.csv")
    if a.append and os.path.exists(old):
        for r in csv.DictReader(open(old)):
            if not (r["problem"] in a.problems and r["policy"] in a.policies):
                for k in ("seed", "won", "caught", "steps", "dots_eaten", "ghosts_eaten"):
                    r[k] = int(r[k])
                for k in ("total_reward", "ms_per_decision"):
                    r[k] = float(r[k])
                rows.append(r)
    for name in a.problems:
        for pol in a.policies:
            n = a.rollout_episodes if (pol == "rollout" and a.rollout_episodes) else a.episodes
            if pol == "open-loop" and open_loop_plan(name)[0] is None:
                print(name, "open-loop: no classical plan available, skipped")
                continue
            for ep in range(n):
                rows.append(run_episode(name, pol, ep, a))
            sub = [r for r in rows if r["problem"] == name and r["policy"] == pol]
            print(f"{name} {pol:9} reward={np.mean([r['total_reward'] for r in sub]):8.1f} "
                  f"win={np.mean([r['won'] for r in sub]):.2f} caught={np.mean([r['caught'] for r in sub]):.2f} "
                  f"dots={np.mean([r['dots_eaten'] for r in sub]):5.1f} "
                  f"ms/dec={np.mean([r['ms_per_decision'] for r in sub]):.1f}", flush=True)
    os.makedirs(os.path.join(ROOT, RESULTS), exist_ok=True)
    with open(os.path.join(ROOT, RESULTS, "rddl_episodes.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = []
    all_policies = ["random", "open-loop", "greedy", "rollout"]
    for name in sorted({r["problem"] for r in rows}):
        for pol in [p for p in all_policies if any(r["policy"] == p for r in rows)]:
            sub = [r for r in rows if r["problem"] == name and r["policy"] == pol]
            if not sub:
                continue
            rew = [r["total_reward"] for r in sub]
            summary.append(dict(problem=name, policy=pol, episodes=len(sub),
                                mean_reward=round(float(np.mean(rew)), 1),
                                std_reward=round(float(np.std(rew)), 1),
                                win_rate=round(float(np.mean([r["won"] for r in sub])), 2),
                                caught_rate=round(float(np.mean([r["caught"] for r in sub])), 2),
                                mean_dots=round(float(np.mean([r["dots_eaten"] for r in sub])), 1),
                                mean_steps=round(float(np.mean([r["steps"] for r in sub])), 1),
                                ms_per_decision=round(float(np.mean([r["ms_per_decision"] for r in sub])), 1)))
    with open(os.path.join(ROOT, RESULTS, "rddl_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    print(f"written {RESULTS}/rddl_episodes.csv, {RESULTS}/rddl_summary.csv")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")
    main()
