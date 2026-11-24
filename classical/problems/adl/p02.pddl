;; p02: 1 ghost, 1 power pill
;; {'cells': 17, 'dots': 14, 'pills': 1, 'ghosts': 1, 'phases': 6}
;;   #########
;;   #P......#
;;   #.##.##.#
;;   #o..G...#
;;   #########
(define (problem pacman-p02)
  (:domain pacman-adl)
  (:objects
    c1_1 c2_1 c3_1 c4_1 c5_1 c6_1 c7_1 c1_2 c4_2 c7_2 c1_3 c2_3 c3_3 c4_3 c5_3 c6_3 c7_3 - cell
    ph0 ph1 ph2 ph3 ph4 ph5 - phase
    g1 - ghost)
  (:init
    (at c1_1) (now ph0) (adj c1_1 c1_2) (adj c1_1 c2_1)
    (adj c2_1 c1_1) (adj c2_1 c3_1) (adj c3_1 c2_1) (adj c3_1 c4_1)
    (adj c4_1 c4_2) (adj c4_1 c3_1) (adj c4_1 c5_1) (adj c5_1 c4_1)
    (adj c5_1 c6_1) (adj c6_1 c5_1) (adj c6_1 c7_1) (adj c7_1 c7_2)
    (adj c7_1 c6_1) (adj c1_2 c1_1) (adj c1_2 c1_3) (adj c4_2 c4_1)
    (adj c4_2 c4_3) (adj c7_2 c7_1) (adj c7_2 c7_3) (adj c1_3 c1_2)
    (adj c1_3 c2_3) (adj c2_3 c1_3) (adj c2_3 c3_3) (adj c3_3 c2_3)
    (adj c3_3 c4_3) (adj c4_3 c4_2) (adj c4_3 c3_3) (adj c4_3 c5_3)
    (adj c5_3 c4_3) (adj c5_3 c6_3) (adj c6_3 c5_3) (adj c6_3 c7_3)
    (adj c7_3 c7_2) (adj c7_3 c6_3) (next ph0 ph1) (next ph1 ph2)
    (next ph2 ph3) (next ph3 ph4) (next ph4 ph5) (next ph5 ph0)
    (dot c1_2) (dot c2_1) (dot c2_3) (dot c3_1)
    (dot c3_3) (dot c4_1) (dot c4_2) (dot c5_1)
    (dot c5_3) (dot c6_1) (dot c6_3) (dot c7_1)
    (dot c7_2) (dot c7_3) (pill c1_3) (alive g1)
    (threat g1 c4_2 c4_3 ph5) (threat g1 c7_2 c7_3 ph2) (threat g1 c3_3 c4_3 ph5) (threat g1 c4_3 c4_3 ph5)
    (threat g1 c4_3 c5_3 ph0) (threat g1 c4_3 c5_3 ph4) (threat g1 c4_3 c5_3 ph5) (threat g1 c5_3 c5_3 ph0)
    (threat g1 c5_3 c5_3 ph4) (threat g1 c5_3 c4_3 ph0) (threat g1 c5_3 c4_3 ph5) (threat g1 c5_3 c6_3 ph1)
    (threat g1 c5_3 c6_3 ph3) (threat g1 c5_3 c6_3 ph4) (threat g1 c6_3 c6_3 ph1) (threat g1 c6_3 c6_3 ph3)
    (threat g1 c6_3 c5_3 ph0) (threat g1 c6_3 c5_3 ph1) (threat g1 c6_3 c5_3 ph4) (threat g1 c6_3 c7_3 ph2)
    (threat g1 c6_3 c7_3 ph3) (threat g1 c7_3 c7_3 ph2) (threat g1 c7_3 c6_3 ph1) (threat g1 c7_3 c6_3 ph2)
    (threat g1 c7_3 c6_3 ph3))
  (:goal (forall (?c - cell) (not (dot ?c)))))
