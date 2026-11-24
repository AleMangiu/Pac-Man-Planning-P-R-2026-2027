"""Independent plan validator: replays a plan on the ground-truth game model
(tools/game.py), without using any PDDL code.

  python3 tools/validate.py classical p03 plans/p03.plan
  python3 tools/validate.py numeric   p03 plans/p03.plan

Accepts the action names of all encodings: move / wait (ADL, numeric) and
move-<content>-<ghost> / wait-<ghost> (STRIPS). Only cells and phases are
taken from the plan; every rule is re-checked here.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from game import Game, cell_name  # noqa: E402
from maps import MAPS  # noqa: E402
from gen import LIVES, PILL_DURATION  # noqa: E402

CELL = re.compile(r"c(\d+)_(\d+)")


def parse_plan(path):
    acts = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        line = re.sub(r"^\s*[\d.]+\s*:\s*", "", line)      # ENHSP "0.0: (move ...)"
        line = re.sub(r"\s*\[[\d.]+\]\s*$", "", line)
        toks = line.strip("()").split()
        acts.append(toks)
    return acts


def validate(mode, name, plan):
    g = Game(MAPS[name], name)
    pos, phase = g.start, 0
    dots, pills = set(g.dots), set(g.pills)
    alive = set(g.ghosts)
    powered, power, lives, hits = False, 0, LIVES, 0
    for i, toks in enumerate(plan):
        act, args = toks[0].lower(), toks[1:]
        cells = [(int(a), int(b)) for a, b in (CELL.fullmatch(x).groups() for x in args if CELL.fullmatch(x))]
        phases = [int(x[2:]) for x in args if re.fullmatch(r"ph\d+", x)]
        if act.startswith("wait"):
            frm = to = cells[0]
        else:
            frm, to = cells[0], cells[1]
        err = lambda m: (False, f"step {i+1} {' '.join(toks)}: {m}")  # noqa: E731
        if frm != pos:
            return err(f"Pac-Man is in {cell_name(pos)}")
        if to != frm and to not in g.adj[frm]:
            return err("cells not adjacent")
        if phases and phases[0] != phase:
            return err(f"current phase is ph{phase}")
        for x in g.threats(frm, to, phase):
            if x not in alive:
                continue
            if mode == "classical":
                if not powered:
                    return err(f"collision with {x} while not powered")
                alive.discard(x)
            else:
                if power > 0:
                    alive.discard(x)
                elif lives > 1:
                    lives -= 1
                    hits += 1
                else:
                    return err(f"collision with {x} with no spare life")
        ate_pill = to in pills
        dots.discard(to)
        if mode == "numeric" and power > 0 and not ate_pill:
            power -= 1
        if ate_pill:
            pills.discard(to)
            powered, power = True, PILL_DURATION
        pos, phase = to, g.nxt(phase)
    if dots:
        return False, f"{len(dots)} dots left"
    info = f"valid: {len(plan)} steps"
    if mode == "numeric":
        info += f", {hits} hits, metric={len(plan) + 10 * hits}"
    info += f", ghosts eaten={len(g.ghosts) - len(alive)}"
    return True, info


if __name__ == "__main__":
    mode, name, path = sys.argv[1:4]
    ok, msg = validate(mode, name, parse_plan(path))
    print(("OK  " if ok else "FAIL ") + msg)
    sys.exit(0 if ok else 1)
