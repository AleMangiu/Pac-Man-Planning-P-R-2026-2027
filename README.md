# Pac-Man Planning – Planning and Reasoning project (A.Y. 2026/27)

A simplified Pac-Man modelled as a planning problem in three forms:

| Part | Formalism | Tool | Folder |
|---|---|---|---|
| Main model | Classical PDDL, ADL + STRIPS compilation | Fast Downward | `classical/` |
| Variant 1 | Numeric PDDL 2.1 | ENHSP | `numeric/` |
| Variant 2 | RDDL (MDP with stochastic ghosts) | pyRDDLGym | `rddl/` |

All domain/problem files describe **the same game**: the maps live in
`tools/maps.py`, and `tools/gen.py` generates every PDDL and RDDL instance from them.
`tools/game.py` is the "ground truth" model of the game, and `tools/validate.py` uses
it to re-check every plan found by the planners, independently of the PDDL.

## Structure

```
classical/domain_adl.pddl        main domain (ADL)
classical/domain_strips.pddl     STRIPS compilation (generated)
classical/problems/{adl,strips}/p01..p05.pddl
numeric/domain.pddl              numeric variant
numeric/problems/p01..p05.pddl
rddl/domain.rddl                 probabilistic variant
rddl/instances/p01..p05.rddl
tools/maps.py                    the 5 maps (increasing difficulty)
tools/game.py                    game model (cells, patrols, threats)
tools/gen.py                     generator of all PDDL/RDDL files
tools/validate.py                independent plan validator
tools/run_classical.py           Fast Downward experiments -> results/classical.csv
tools/run_numeric.py             ENHSP experiments         -> results/numeric.csv
tools/run_rddl.py                RDDL policy evaluation    -> results/rddl_*.csv
results/                         CSV files and found plans
run_all.py                       regenerates everything and reruns the experiments
run_all.sh                       same, for bash users
```

Requirements: `python3`, `java`, `pip install -r requirements.txt`
(`up-fast-downward` and `up-enhsp` already ship the Fast Downward and ENHSP binaries).

## The domain

Pac-Man moves on a grid and must eat all the dots. Ghosts patrol fixed routes
(back and forth, or in a loop). A power pill lets Pac-Man eat the ghosts.

| Instance | Cells | Dots | Pills | Ghosts | Phases |
|---|---|---|---|---|---|
| p01 | 12 | 10 | 0 | 1 | 4 |
| p02 | 17 | 14 | 1 | 1 | 6 |
| p03 | 33 | 29 | 1 | 2 | 6 |
| p04 | 42 | 38 | 1 | 2 | 24 |
| p05 | 66 | 60 | 2 | 3 | 16 |

### Modelling choices (classical model)

* **Deterministic ghosts through phases.** In classical planning only the agent
  changes the state, so ghosts cannot "move on their own". Their position is a
  function of a **global cyclic phase** (objects `ph0..phN-1`, with N = lcm of the
  patrol lengths). Every Pac-Man action advances the phase by one.
* **Precomputed threats.** The static fact `(threat ?g ?from ?to ?p)` states that
  moving from `?from` to `?to` during phase `?p` makes Pac-Man collide with ghost
  `?g`: same cell at the end of the step, or a head-on swap of cells.
  This keeps the domain small and moves the trajectory computation into the generator.
* **Permanent power pill.** In the classical model `powered` stays true forever:
  a timer would require number objects such as `plus1` from the lectures. The real
  timer is introduced in the numeric variant.
* **ADL features used:** universal preconditions with `imply` (a live ghost on the
  trajectory is allowed only when powered), conditional effects (dot, pill),
  universal conditional effects (the ghosts met are eaten), negative universal goal
  `(forall (?c) (not (dot ?c)))`.

### From ADL to STRIPS (required by point 2.2)

Fast Downward compiles the quantified/negated constructs of the ADL domain into
**axioms** (26 in p01, 263 in p05). With this model **LM-cut cannot be used**:
Fast Downward answers *"This configuration does not support axioms!"*.
To compare A\* with LM-cut we wrote `domain_strips.pddl`, which compiles the ADL
away as seen in class:

* **conditional effects → one action per case**: `move-dot-*`, `move-pill-*`,
  `move-empty-*`;
* **forall over ghosts → one action per case**: no threat (static fact `free`),
  threatening ghost already dead (`dead`), ghost eaten (`powered`).
  This is correct because the generator checks that a single step is threatened by
  at most one ghost;
* **negative conditions → complementary positive predicates** (`no-dot`,
  `no-pill`, `dead`), as in the positive normal form construction; the goal lists
  `(no-dot c)` for every dot.

Result: we go from 2 action schemas to 12 (9 move + 3 wait). Ground operators grow
by about 1.4–1.8× (e.g. p04: 3120 → 5423), but the axioms disappear and LM-cut
becomes usable. Optimal plans have the same length in both encodings: this is a
check that the two encodings are equivalent.

## Results – classical model (Fast Downward, timeout 300 s)

Plan length (expanded nodes); "unsup." = unsupported configuration;
"t/o" = timeout.

| | p01 | p02 | p03 | p04 | p05 |
|---|---|---|---|---|---|
| ADL – A\* blind | 14 (432) | 17 (6 551) | 38 (8.1M) | 45 (6.1M) | t/o |
| ADL – A\* hmax | 14 (169) | 17 (920) | 38 (1.5M) | 45 (438k) | t/o |
| ADL – A\* LM-cut | unsup. | unsup. | unsup. | unsup. | unsup. |
| ADL – GBFS hFF | 31 (122) | 17 (55) | 45 (207) | 69 (3 274) | 205 (3 725) |
| ADL – LAMA-first | 18 (216) | 19 (40) | 67 (155) | 45 (98) | 83 (184) |
| STRIPS – A\* blind | 14 (435) | 17 (6 858) | 38 (8.5M) | 45 (6.2M) | t/o |
| STRIPS – A\* hmax | 14 (169) | 17 (920) | 38 (1.5M) | 45 (438k) | t/o |
| STRIPS – A\* LM-cut | 14 (92) | 17 (42) | 38 (13 027) | 45 (3 425) | t/o |
| STRIPS – GBFS hFF | 28 (116) | 17 (52) | 48 (283) | 81 (3 067) | 160 (7 499) |
| STRIPS – LAMA-first | 14 (22) | 18 (32) | 54 (192) | 47 (117) | 79 (181) |

What they show:

* **admissible and informed:** on p03 LM-cut expands ~650× fewer nodes than blind
  and ~115× fewer than hmax. All A\* configurations find the same optimal cost,
  as expected with admissible heuristics;
* **greedy/satisficing:** GBFS and LAMA answer in under a second even on p05,
  where every A\* times out, but with plans up to 2–3 times longer.
  They are suboptimal because they ignore g, as seen in class;
* **p05** (60 dots) is the threshold beyond which optimal planning does not scale:
  "eat all the dots" is a travelling-salesman-like problem.

All plans were validated with `tools/validate.py`.

## Variant 1 – Numeric planning (ENHSP)

Structural changes with respect to the classical model:

| Classical | Numeric | Why |
|---|---|---|
| permanent boolean `powered` | `(power)` timer: the pill sets it to `pill-duration` (8), every step decrements it | counting would require number objects (`plus1`) |
| touching a ghost is forbidden | `(lives)`: without power Pac-Man can pay a life (action `move-hit`) if at least one is left | resource / path trade-off |
| goal `forall (not (dot ?c))` | numeric goal `(<= (dots-left) 0)` | use of numeric conditions |
| cost = number of actions | `:metric minimize (+ (steps) (* 10 (hits)))` | non-uniform plan quality |

Design choice: being hit is a **separate action** (`move-hit`, `wait-hit`) rather
than a conditional effect. This way every action has a constant cost with respect
to the metric. With the conditional effect ENHSP charged the penalty to *every*
move (it estimated 132 instead of 22 on p01), unless the experimental `-sdac`
option is used.

Results (timeout 300 s, penalty K = 10), as steps, hits → metric:

| | p01 | p02 | p03 | p04 | p05 |
|---|---|---|---|---|---|
| GBFS hadd | 12 steps, 1 hit → 22 | 25, 2 → 45 | 38, 2 → 58 | 65, 2 → 85 | t/o |
| sat-hmrp | 12, 1 → 22 | 26, 2 → 46 | 76, 2 → 96 | 74, 2 → 94 | t/o |
| A\* blind | 14, 0 → 14 | 17, 0 → 17 | out of memory | out of memory | out of memory |
| A\* hrmax | 14, 0 → 14 | 17, 0 → 17 | t/o | 45, 0 → 45 | t/o |

Sensitivity study on the penalty (A\* hrmax, optimal): on p01 with K = 1 the
optimal plan **accepts a hit** (12 steps + 1 = 13 < 14), with K ≥ 3 it avoids it.
On p03 with K = 1 it accepts 2 hits and shortens the path from 38 to 33 steps
(metric 35); with K = 3 a plan with 1 hit (35 + 3 = 38) ties with the hit-free
plan. The numeric metric really changes the structure of the solution, which is
impossible in the classical model.

Observations:

* satisficing planners readily spend lives to shorten the path, because they
  mainly optimise the distance to the goal;
* optimal numeric planning scales worse than classical (p03 is not solved within
  300 s, and blind search runs out of memory). The state also contains `power` and
  `lives`, so the state space is larger, and an expansion in ENHSP is more expensive.

## Variant 2 – Probabilistic planning (RDDL, pyRDDLGym)

Structural changes:

* **stochastic ghosts:** at each step every ghost advances along its patrol with
  probability `P-ADVANCE` = 0.8, otherwise it stays still (an intermediate fluent
  `advance(?g)` = a single coin flip per ghost). Global phases disappear: every
  ghost has its own `ghost-step` pointer;
* **goal → reward:** +10 per dot, +50 per ghost eaten, +200 on victory, −1 per
  step, −500 if caught (absorbing state `caught`);
* **power** is an integer timer as in the numeric variant;
* **action:** `move(?c)` with `max-nondef-actions = 1`; no action means waiting.

We no longer produce a plan: we evaluate a **policy** on its mean reward (the
average total reward per episode; 30 episodes, 12 for rollout, which is slower;
only 6 rollout episodes on p05, where one decision costs ~2 s). On p05 the
open-loop baseline uses the LAMA-first plan, because no A\* finds an optimal plan
within the timeout. Policies compared (`tools/run_rddl.py`):

* **random:** random admissible action;
* **open-loop:** the optimal plan of the classical model, executed blindly;
* **greedy:** reactive, heads to the nearest dot while avoiding cells that a live
  ghost can occupy at the next step;
* **rollout:** Monte Carlo online planner that uses **the RDDL model itself**
  (pyRDDLGym simulator) as a generative model. For each action it simulates 6
  futures of 10 steps following the greedy policy and picks the action with the
  best average return (*rollout algorithm*, policy improvement over greedy).

| Instance | Policy | Mean reward | Wins | Caught | Dots eaten | ms/decision |
|---|---|---|---|---|---|---|
| p01 | random | -293.9 ± 242 | 0% | 63% | 4.9 | 0.0 |
| p01 | open-loop | -122.6 ± 382 | 47% | 53% | 5.9 | 0.0 |
| p01 | greedy | 42.7 ± 4 | 0% | 0% | 8.3 | 0.0 |
| p01 | rollout | 35.9 ± 172 | 17% | 8% | 8.2 | 98.1 |
| p02 | random | -171.6 ± 235 | 0% | 40% | 6.8 | 0.0 |
| p02 | open-loop | 373.0 ± 0 | 100% | 0% | 14.0 | 0.0 |
| p02 | greedy | 80.0 ± 0 | 0% | 0% | 13.0 | 0.0 |
| p02 | rollout | 363.2 ± 20 | 100% | 0% | 14.0 | 76.6 |
| p03 | random | -402.6 ± 142 | 0% | 90% | 9.5 | 0.0 |
| p03 | open-loop | -245.5 ± 6 | 0% | 100% | 23.5 | 0.0 |
| p03 | greedy | 233.3 ± 17 | 0% | 0% | 28.0 | 0.0 |
| p03 | rollout | 221.8 ± 172 | 17% | 8% | 26.7 | 218.1 |
| p04 | random | -250.7 ± 219 | 0% | 57% | 11.1 | 0.0 |
| p04 | open-loop | 2.2 ± 388 | 30% | 70% | 28.6 | 0.0 |
| p04 | greedy | 246.8 ± 59 | 3% | 0% | 34.0 | 0.0 |
| p04 | rollout | 251.2 ± 97 | 8% | 0% | 32.9 | 419.2 |
| p05 | random | -169.3 ± 224 | 0% | 43% | 17.3 | 0.0 |
| p05 | open-loop | -316.9 ± 20 | 0% | 100% | 20.6 | 0.0 |
| p05 | greedy | 434.0 ± 42 | 0% | 0% | 56.7 | 0.0 |
| p05 | rollout | 185.8 ± 361 | 0% | 33% | 45.7 | 1716.3 |

What they show:

* **the classical plan is not robust:** executed open-loop in a stochastic world
  it is often caught (p03: 100% of episodes), because a single ghost pausing for
  one step breaks the synchronisation it relied on. It only works when the route
  does not depend on ghost timing (p02: 100% wins);
* **greedy is safe but short-sighted:** never caught, but it almost never
  finishes. The last dots lie on the patrols and the rule "avoid the ghost's next
  step" blocks it;
* **rollout exploits the probabilistic model:** by simulating possible futures it
  finds the right moment to enter the ghosts' corridors and wins where greedy
  does not (p01: 17% vs 0%; p03: 17% vs 0%; p04: 8% vs 3%), at a cost of
  ~80–420 ms per decision. Its variance is high, though: with 12 episodes the
  win rates are noisy, and the price of entering the corridors is an occasional
  capture;
* **p05 shows the limit of rollout:** no policy finishes within 160 steps and
  rollout (6 futures of 10 steps) does worse than greedy. The simulation budget is
  too small for 66 cells and 3 ghosts, and a decision already costs ~2 s, because
  the simulator evaluates cell swaps over all cell × cell × step × step pairs.

## Edge cases and assumptions

* **At most one threatening ghost per step.** The STRIPS compilation creates one
  action per case (no threat / dead ghost / ghost eaten), so it is only valid if a
  single step is threatened by at most one ghost. `gen.py` checks this
  (`Game.check_single_threat`) for every map. With two ghosts on the same step one
  action per combination of ghost states would be needed.
* **Pill and ghost in the same step.** Power is checked on the value *before* the
  step, so the pill only takes effect from the next step. If Pac-Man is not
  powered and enters a cell with a pill while a ghost reaches it: in the classical
  model the move is forbidden, in the numeric one it costs a life (`move-hit`), in
  RDDL Pac-Man is caught. The rule is the same in all three models.

## Reproducing everything

Requirements: Python 3 and Java (for ENHSP). From the project folder:

```
pip install -r requirements.txt
python run_all.py --quick     # quick check on p01-p02, writes to results_quick/
python run_all.py             # all experiments (1-2 hours), writes to results/
```

The Fast Downward and ENHSP paths are found automatically from the pip packages;
they can be overridden with the environment variables `FAST_DOWNWARD` and
`ENHSP_JAR`. In VS Code the `.vscode/` folder already contains the launch
configurations (*Run and Debug* panel). `run_all.sh` remains for bash users.

The reported results were measured on a Mac with a 300 s timeout per
run: absolute times will change on other machines, the orders of magnitude will not.
Rollout results depend on random seeds and library versions, so its win rates can
vary between runs.
