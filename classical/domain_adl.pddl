;; Simplified Pac-Man - classical ADL formulation
;;
;; Pac-Man moves on a grid and must eat every dot. Ghosts patrol fixed routes:
;; their position is a deterministic function of a global, cyclic "phase"
;; (the phase advances by one at every Pac-Man step, so the problem stays
;; classical). The static predicate (threat ?g ?from ?to ?p) is precomputed
;; by the generator: moving from ?from to ?to while the phase goes from ?p to
;; its successor collides with ghost ?g (same cell afterwards, or head-on swap).
;; Eating a power pill makes Pac-Man powered (for the rest of the episode in
;; this formulation): a powered Pac-Man can walk into a ghost and eat it.
;;
;; ADL features used: negative and disjunctive (imply) preconditions,
;; universally quantified preconditions, universally quantified conditional
;; effects, universally quantified negative goal.

(define (domain pacman-adl)
  (:requirements :typing :adl)
  (:types cell ghost phase)

  (:predicates
    (at ?c - cell)                                  ; Pac-Man position
    (adj ?c1 ?c2 - cell)                            ; static: corridor between cells
    (dot ?c - cell)
    (pill ?c - cell)
    (powered)
    (alive ?g - ghost)
    (now ?p - phase)                                ; current phase of the ghost patrols
    (next ?p1 ?p2 - phase)                          ; static: cyclic successor of a phase
    (threat ?g - ghost ?from ?to - cell ?p - phase) ; static: collision with ghost ?g
  )

  (:action move
    :parameters (?from ?to - cell ?p ?q - phase)
    :precondition (and (at ?from) (adj ?from ?to) (now ?p) (next ?p ?q)
                       ;; a living ghost on the way is allowed only if Pac-Man is powered
                       (forall (?g - ghost)
                         (imply (and (alive ?g) (threat ?g ?from ?to ?p)) (powered))))
    :effect (and (not (at ?from)) (at ?to)
                 (not (now ?p)) (now ?q)
                 (when (dot ?to) (not (dot ?to)))
                 (when (pill ?to) (and (not (pill ?to)) (powered)))
                 ;; every living ghost met on the way is eaten
                 (forall (?g - ghost)
                   (when (and (alive ?g) (threat ?g ?from ?to ?p))
                         (not (alive ?g))))))

  (:action wait
    :parameters (?c - cell ?p ?q - phase)
    :precondition (and (at ?c) (now ?p) (next ?p ?q)
                       (forall (?g - ghost)
                         (imply (and (alive ?g) (threat ?g ?c ?c ?p)) (powered))))
    :effect (and (not (now ?p)) (now ?q)
                 (forall (?g - ghost)
                   (when (and (alive ?g) (threat ?g ?c ?c ?p))
                         (not (alive ?g))))))
)
