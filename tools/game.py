"""Ground-truth model of the simplified Pac-Man game.

Everything that the PDDL/RDDL encodings need (cells, adjacency, ghost positions
per phase, threats) is computed here once, so all variants describe exactly the
same game. The same code is used by the plan validator.
"""
from math import lcm

MOVES = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}


def cell_name(c):
    return f"c{c[0]}_{c[1]}"


class Game:
    def __init__(self, spec, name="p"):
        self.name = name
        grid = spec["grid"]
        self.grid = grid
        self.walls, self.cells = set(), []
        self.dots, self.pills, ghost_starts = set(), set(), []
        self.start = None
        for y, row in enumerate(grid):
            for x, ch in enumerate(row):
                if ch == "#":
                    self.walls.add((x, y))
                    continue
                self.cells.append((x, y))
                if ch == ".":
                    self.dots.add((x, y))
                elif ch == "o":
                    self.pills.add((x, y))
                elif ch == "P":
                    self.start = (x, y)
                elif ch == "G":
                    ghost_starts.append((x, y))
        cs = set(self.cells)
        self.adj = {c: [] for c in self.cells}
        for (x, y) in self.cells:
            for dx, dy in MOVES.values():
                n = (x + dx, y + dy)
                if n in cs:
                    self.adj[(x, y)].append(n)

        # ghost trajectories: list of positions, one per step of the cycle
        assert len(ghost_starts) == len(spec["routes"]), "one route per ghost"
        self.cycles = []
        for start, route in zip(ghost_starts, spec["routes"]):
            path = [start]
            for m in route:
                dx, dy = MOVES[m]
                nxt = (path[-1][0] + dx, path[-1][1] + dy)
                assert nxt in cs, f"{name}: ghost route enters wall at {nxt}"
                path.append(nxt)
            if path[-1] == path[0]:          # closed loop
                cycle = path[:-1]
            else:                            # ping-pong
                cycle = path + path[-2:0:-1]
            self.cycles.append(cycle)
        self.ghosts = [f"g{i+1}" for i in range(len(self.cycles))]
        self.nphases = lcm(*[len(c) for c in self.cycles]) if self.cycles else 1

        # pos[g][p] = cell of ghost g at phase p
        self.pos = {g: [cyc[p % len(cyc)] for p in range(self.nphases)]
                    for g, cyc in zip(self.ghosts, self.cycles)}
        assert self.start not in [self.pos[g][0] for g in self.ghosts], "ghost on start"

    def nxt(self, p):
        return (p + 1) % self.nphases

    def threats(self, frm, to, p):
        """Ghosts that collide with Pac-Man moving frm->to while the phase goes p->p+1
        (frm == to means waiting). Collision = same cell after the step, or head-on swap."""
        q = self.nxt(p)
        out = []
        for g in self.ghosts:
            gp, gq = self.pos[g][p], self.pos[g][q]
            if gq == to or (gp == to and gq == frm):
                out.append(g)
        return out

    def transitions(self):
        """All (frm, to) pairs Pac-Man can attempt: moves to adjacent cells and waiting."""
        for c in self.cells:
            yield c, c
            for n in self.adj[c]:
                yield c, n

    def check_single_threat(self):
        for frm, to in self.transitions():
            for p in range(self.nphases):
                assert len(self.threats(frm, to, p)) <= 1, \
                    f"{self.name}: two ghosts threaten {frm}->{to} at phase {p}"

    def stats(self):
        return dict(cells=len(self.cells), dots=len(self.dots), pills=len(self.pills),
                    ghosts=len(self.ghosts), phases=self.nphases)
