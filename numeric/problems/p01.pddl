;; p01: warm-up: 1 ghost, no pills
;; {'cells': 12, 'dots': 10, 'pills': 0, 'ghosts': 1, 'phases': 4}
;;   #######
;;   #P....#
;;   #.###.#
;;   #..G..#
;;   #######
(define (problem pacman-p01)
  (:domain pacman-numeric)
  (:objects
    c1_1 c2_1 c3_1 c4_1 c5_1 c1_2 c5_2 c1_3 c2_3 c3_3 c4_3 c5_3 - cell
    ph0 ph1 ph2 ph3 - phase
    g1 - ghost)
  (:init
    (at c1_1) (now ph0) (adj c1_1 c1_2) (adj c1_1 c2_1)
    (adj c2_1 c1_1) (adj c2_1 c3_1) (adj c3_1 c2_1) (adj c3_1 c4_1)
    (adj c4_1 c3_1) (adj c4_1 c5_1) (adj c5_1 c5_2) (adj c5_1 c4_1)
    (adj c1_2 c1_1) (adj c1_2 c1_3) (adj c5_2 c5_1) (adj c5_2 c5_3)
    (adj c1_3 c1_2) (adj c1_3 c2_3) (adj c2_3 c1_3) (adj c2_3 c3_3)
    (adj c3_3 c2_3) (adj c3_3 c4_3) (adj c4_3 c3_3) (adj c4_3 c5_3)
    (adj c5_3 c5_2) (adj c5_3 c4_3) (next ph0 ph1) (next ph1 ph2)
    (next ph2 ph3) (next ph3 ph0) (dot c1_2) (dot c1_3)
    (dot c2_1) (dot c2_3) (dot c3_1) (dot c4_1)
    (dot c4_3) (dot c5_1) (dot c5_2) (dot c5_3)
    (alive g1) (threat g1 c1_2 c1_3 ph1) (threat g1 c1_3 c1_3 ph1) (threat g1 c1_3 c2_3 ph0)
    (threat g1 c1_3 c2_3 ph1) (threat g1 c1_3 c2_3 ph2) (threat g1 c2_3 c2_3 ph0) (threat g1 c2_3 c2_3 ph2)
    (threat g1 c2_3 c1_3 ph1) (threat g1 c2_3 c1_3 ph2) (threat g1 c2_3 c3_3 ph0) (threat g1 c2_3 c3_3 ph3)
    (threat g1 c3_3 c3_3 ph3) (threat g1 c3_3 c2_3 ph0) (threat g1 c3_3 c2_3 ph2) (threat g1 c3_3 c2_3 ph3)
    (threat g1 c4_3 c3_3 ph3) (= (power) 0) (= (pill-duration) 8) (= (lives) 3)
    (= (dots-left) 10) (= (steps) 0) (= (hits) 0))
  (:goal (<= (dots-left) 0))
  (:metric minimize (+ (steps) (* 10 (hits)))))
