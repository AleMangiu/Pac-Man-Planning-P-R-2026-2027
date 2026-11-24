;; Simplified Pac-Man - numeric formulation (PDDL 2.1, solved with ENHSP)
;;
;; Differences w.r.t. the classical ADL model:
;;  * the power pill is a TIMER: eating it sets (power) to (pill-duration);
;;    every step decreases it; Pac-Man can eat ghosts only while (power) > 0
;;    (in the classical model "powered" lasted forever, because counting
;;    steps there needs one object per value, as with plus1 in the lectures);
;;  * Pac-Man has (lives): touching a living ghost while not powered costs one
;;    life instead of being forbidden, as long as at least one life remains;
;;  * the number of remaining dots is a numeric fluent and the goal is a
;;    numeric condition;
;;  * plan quality is a metric that trades path length against lost lives.
;;
;; Being hit is a separate action (move-hit / wait-hit) instead of a
;; conditional effect: this keeps every action at a constant cost w.r.t. the
;; metric (steps + 10*hits). With the hit as a conditional effect ENHSP
;; charges the penalty to every move (it assumes the effect may always fire)
;; unless the experimental -sdac option is used.

(define (domain pacman-numeric)
  (:requirements :typing :adl :numeric-fluents)
  (:types cell ghost phase)

  (:predicates
    (at ?c - cell)
    (adj ?c1 ?c2 - cell)
    (dot ?c - cell)
    (pill ?c - cell)
    (alive ?g - ghost)
    (now ?p - phase)
    (next ?p1 ?p2 - phase)
    (threat ?g - ghost ?from ?to - cell ?p - phase)
  )

  (:functions
    (power)            ; remaining powered steps (0 = not powered)
    (pill-duration)    ; static: steps of power given by a pill
    (lives)            ; remaining lives
    (dots-left)        ; dots still to eat
    (steps)            ; plan length (metric only)
    (hits)             ; lives lost (metric only)
  )

  ;; normal step: allowed if no living ghost is met, or if Pac-Man is powered
  ;; (in which case the ghost is eaten)
  (:action move
    :parameters (?from ?to - cell ?p ?q - phase)
    :precondition (and (at ?from) (adj ?from ?to) (now ?p) (next ?p ?q)
                       (forall (?g - ghost)
                         (imply (and (alive ?g) (threat ?g ?from ?to ?p)) (> (power) 0))))
    :effect (and (not (at ?from)) (at ?to)
                 (not (now ?p)) (now ?q)
                 (increase (steps) 1)
                 (when (dot ?to) (and (not (dot ?to)) (decrease (dots-left) 1)))
                 (when (pill ?to) (and (not (pill ?to)) (assign (power) (pill-duration))))
                 (when (and (> (power) 0) (not (pill ?to))) (decrease (power) 1))
                 (forall (?g - ghost)
                   (when (and (alive ?g) (threat ?g ?from ?to ?p)) (not (alive ?g))))))

  ;; step that runs into a living ghost while not powered: costs one life
  (:action move-hit
    :parameters (?from ?to - cell ?p ?q - phase ?g - ghost)
    :precondition (and (at ?from) (adj ?from ?to) (now ?p) (next ?p ?q)
                       (alive ?g) (threat ?g ?from ?to ?p)
                       (<= (power) 0) (> (lives) 1))
    :effect (and (not (at ?from)) (at ?to)
                 (not (now ?p)) (now ?q)
                 (increase (steps) 1)
                 (decrease (lives) 1) (increase (hits) 1)
                 (when (dot ?to) (and (not (dot ?to)) (decrease (dots-left) 1)))
                 (when (pill ?to) (and (not (pill ?to)) (assign (power) (pill-duration))))))

  (:action wait
    :parameters (?c - cell ?p ?q - phase)
    :precondition (and (at ?c) (now ?p) (next ?p ?q)
                       (forall (?g - ghost)
                         (imply (and (alive ?g) (threat ?g ?c ?c ?p)) (> (power) 0))))
    :effect (and (not (now ?p)) (now ?q)
                 (increase (steps) 1)
                 (when (> (power) 0) (decrease (power) 1))
                 (forall (?g - ghost)
                   (when (and (alive ?g) (threat ?g ?c ?c ?p)) (not (alive ?g))))))

  (:action wait-hit
    :parameters (?c - cell ?p ?q - phase ?g - ghost)
    :precondition (and (at ?c) (now ?p) (next ?p ?q)
                       (alive ?g) (threat ?g ?c ?c ?p)
                       (<= (power) 0) (> (lives) 1))
    :effect (and (not (now ?p)) (now ?q)
                 (increase (steps) 1)
                 (decrease (lives) 1) (increase (hits) 1)))
)
