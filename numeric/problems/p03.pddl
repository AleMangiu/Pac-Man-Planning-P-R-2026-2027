;; p03: 2 ghosts patrolling the bottom corridors, 1 pill
;; {'cells': 33, 'dots': 29, 'pills': 1, 'ghosts': 2, 'phases': 6}
;;   ###########
;;   #P...#....#
;;   #.##.#.##.#
;;   #.........#
;;   #.##.#.##o#
;;   #G...#...G#
;;   ###########
(define (problem pacman-p03)
  (:domain pacman-numeric)
  (:objects
    c1_1 c2_1 c3_1 c4_1 c6_1 c7_1 c8_1 c9_1 c1_2 c4_2 c6_2 c9_2 c1_3 c2_3 c3_3 c4_3 c5_3 c6_3 c7_3 c8_3 c9_3 c1_4 c4_4 c6_4 c9_4 c1_5 c2_5 c3_5 c4_5 c6_5 c7_5 c8_5 c9_5 - cell
    ph0 ph1 ph2 ph3 ph4 ph5 - phase
    g1 g2 - ghost)
  (:init
    (at c1_1) (now ph0) (adj c1_1 c1_2) (adj c1_1 c2_1)
    (adj c2_1 c1_1) (adj c2_1 c3_1) (adj c3_1 c2_1) (adj c3_1 c4_1)
    (adj c4_1 c4_2) (adj c4_1 c3_1) (adj c6_1 c6_2) (adj c6_1 c7_1)
    (adj c7_1 c6_1) (adj c7_1 c8_1) (adj c8_1 c7_1) (adj c8_1 c9_1)
    (adj c9_1 c9_2) (adj c9_1 c8_1) (adj c1_2 c1_1) (adj c1_2 c1_3)
    (adj c4_2 c4_1) (adj c4_2 c4_3) (adj c6_2 c6_1) (adj c6_2 c6_3)
    (adj c9_2 c9_1) (adj c9_2 c9_3) (adj c1_3 c1_2) (adj c1_3 c1_4)
    (adj c1_3 c2_3) (adj c2_3 c1_3) (adj c2_3 c3_3) (adj c3_3 c2_3)
    (adj c3_3 c4_3) (adj c4_3 c4_2) (adj c4_3 c4_4) (adj c4_3 c3_3)
    (adj c4_3 c5_3) (adj c5_3 c4_3) (adj c5_3 c6_3) (adj c6_3 c6_2)
    (adj c6_3 c6_4) (adj c6_3 c5_3) (adj c6_3 c7_3) (adj c7_3 c6_3)
    (adj c7_3 c8_3) (adj c8_3 c7_3) (adj c8_3 c9_3) (adj c9_3 c9_2)
    (adj c9_3 c9_4) (adj c9_3 c8_3) (adj c1_4 c1_3) (adj c1_4 c1_5)
    (adj c4_4 c4_3) (adj c4_4 c4_5) (adj c6_4 c6_3) (adj c6_4 c6_5)
    (adj c9_4 c9_3) (adj c9_4 c9_5) (adj c1_5 c1_4) (adj c1_5 c2_5)
    (adj c2_5 c1_5) (adj c2_5 c3_5) (adj c3_5 c2_5) (adj c3_5 c4_5)
    (adj c4_5 c4_4) (adj c4_5 c3_5) (adj c6_5 c6_4) (adj c6_5 c7_5)
    (adj c7_5 c6_5) (adj c7_5 c8_5) (adj c8_5 c7_5) (adj c8_5 c9_5)
    (adj c9_5 c9_4) (adj c9_5 c8_5) (next ph0 ph1) (next ph1 ph2)
    (next ph2 ph3) (next ph3 ph4) (next ph4 ph5) (next ph5 ph0)
    (dot c1_2) (dot c1_3) (dot c1_4) (dot c2_1)
    (dot c2_3) (dot c2_5) (dot c3_1) (dot c3_3)
    (dot c3_5) (dot c4_1) (dot c4_2) (dot c4_3)
    (dot c4_4) (dot c4_5) (dot c5_3) (dot c6_1)
    (dot c6_2) (dot c6_3) (dot c6_4) (dot c6_5)
    (dot c7_1) (dot c7_3) (dot c7_5) (dot c8_1)
    (dot c8_3) (dot c8_5) (dot c9_1) (dot c9_2)
    (dot c9_3) (pill c9_4) (alive g1) (alive g2)
    (threat g1 c1_4 c1_5 ph5) (threat g1 c4_4 c4_5 ph2) (threat g2 c6_4 c6_5 ph2) (threat g2 c9_4 c9_5 ph5)
    (threat g1 c1_5 c1_5 ph5) (threat g1 c1_5 c2_5 ph0) (threat g1 c1_5 c2_5 ph4) (threat g1 c1_5 c2_5 ph5)
    (threat g1 c2_5 c2_5 ph0) (threat g1 c2_5 c2_5 ph4) (threat g1 c2_5 c1_5 ph0) (threat g1 c2_5 c1_5 ph5)
    (threat g1 c2_5 c3_5 ph1) (threat g1 c2_5 c3_5 ph3) (threat g1 c2_5 c3_5 ph4) (threat g1 c3_5 c3_5 ph1)
    (threat g1 c3_5 c3_5 ph3) (threat g1 c3_5 c2_5 ph0) (threat g1 c3_5 c2_5 ph1) (threat g1 c3_5 c2_5 ph4)
    (threat g1 c3_5 c4_5 ph2) (threat g1 c3_5 c4_5 ph3) (threat g1 c4_5 c4_5 ph2) (threat g1 c4_5 c3_5 ph1)
    (threat g1 c4_5 c3_5 ph2) (threat g1 c4_5 c3_5 ph3) (threat g2 c6_5 c6_5 ph2) (threat g2 c6_5 c7_5 ph1)
    (threat g2 c6_5 c7_5 ph2) (threat g2 c6_5 c7_5 ph3) (threat g2 c7_5 c7_5 ph1) (threat g2 c7_5 c7_5 ph3)
    (threat g2 c7_5 c6_5 ph2) (threat g2 c7_5 c6_5 ph3) (threat g2 c7_5 c8_5 ph0) (threat g2 c7_5 c8_5 ph1)
    (threat g2 c7_5 c8_5 ph4) (threat g2 c8_5 c8_5 ph0) (threat g2 c8_5 c8_5 ph4) (threat g2 c8_5 c7_5 ph1)
    (threat g2 c8_5 c7_5 ph3) (threat g2 c8_5 c7_5 ph4) (threat g2 c8_5 c9_5 ph0) (threat g2 c8_5 c9_5 ph5)
    (threat g2 c9_5 c9_5 ph5) (threat g2 c9_5 c8_5 ph0) (threat g2 c9_5 c8_5 ph4) (threat g2 c9_5 c8_5 ph5)
    (= (power) 0) (= (pill-duration) 8) (= (lives) 3) (= (dots-left) 29)
    (= (steps) 0) (= (hits) 0))
  (:goal (<= (dots-left) 0))
  (:metric minimize (+ (steps) (* 10 (hits)))))
