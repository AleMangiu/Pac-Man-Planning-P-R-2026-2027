"""Pac-Man instances shared by every variant (classical, numeric, RDDL).

Legend
  #  wall          .  dot          o  power pill
  P  Pac-Man start G  ghost start  (space) empty corridor

Each ghost has a patrol given as a string of moves (U/D/L/R) from its start cell.
If the moves end where they started the patrol is a closed loop; otherwise the
ghost goes back and forth along the path (ping-pong).
Ghosts are listed in the order they appear in the map (row by row).
"""

MAPS = {
    "p01": {
        "grid": [
            "#######",
            "#P....#",
            "#.###.#",
            "#..G..#",
            "#######",
        ],
        "routes": ["LL"],
        "note": "warm-up: 1 ghost, no pills",
    },
    "p02": {
        "grid": [
            "#########",
            "#P......#",
            "#.##.##.#",
            "#o..G...#",
            "#########",
        ],
        "routes": ["RRR"],
        "note": "1 ghost, 1 power pill",
    },
    "p03": {
        "grid": [
            "###########",
            "#P...#....#",
            "#.##.#.##.#",
            "#.........#",
            "#.##.#.##o#",
            "#G...#...G#",
            "###########",
        ],
        "routes": ["RRR", "LLL"],
        "note": "2 ghosts patrolling the bottom corridors, 1 pill",
    },
    "p04": {
        "grid": [
            "###########",
            "#P........#",
            "#.###.###.#",
            "#.#G....#.#",
            "#.#.###.#.#",
            "#o#.....#.#",
            "#.###.###.#",
            "#........G#",
            "###########",
        ],
        "routes": ["RRRRDDLLLLUU", "LLLL"],
        "note": "2 ghosts: one loops around the central block, 1 pill",
    },
    "p05": {
        "grid": [
            "#############",
            "#P....#.....#",
            "#.###.#.###.#",
            "#o..........#",
            "#.###.#.###.#",
            "#.....#..G..#",
            "###.#####.###",
            "#G.........o#",
            "#.###.#.###.#",
            "#.....#....G#",
            "#############",
        ],
        "routes": ["LL", "RRRRRRRR", "LLLL"],
        "note": "3 ghosts, 2 pills, largest maze",
    },
}
