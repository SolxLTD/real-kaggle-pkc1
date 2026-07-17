# Real-kk-
Competition 


pokemon-tcg-ai-battle



1. Battle Engine
A deterministic, rule-complete Pokémon TCG battle simulator supporting all core mechanics: energy attachment, retreat, attacks, abilities, status effects, and prize card logic. Built for stability — every game state is hashable and reproducible.

2. Heuristic Agent
A fast, interpretable agent using handcrafted heuristics: board advantage scoring, energy efficiency, prize card pressure, and matchup-aware mulligan decisions. Designed for matchup generalization across deck archetypes.

3. Deck Builder
An evolutionary deck construction pipeline that optimizes for consistency (draw probability), coverage (type matchups), and synergy (card interactions). Uses Monte Carlo simulation to evaluate deck performance before a single real battle.

4. Self-Play Evaluation Harness
A round-robin tournament framework measuring exactly what the rubric scores: stability (variance across seeds) and matchup generalization (win rate spread across archetypes). Generates statistical reports with confidence intervals.

5. Data-Driven Insights
As a data analyst, I approach this as an experiment design problem. The harness produces structured datasets of every game: turn-by-turn state transitions, decision trees, and outcome distributions. This enables post-hoc analysis of why strategies succeed or fail — the core of the Strategy Category rubric.


1)files; Decker
"""
---------------
Builds a 60-card deck from the available card pool.

Design goals (these map directly onto the Strategy Category rubric:
"deck design concept" + "avoids over-reliance on specific matchups"):

1. Pick ONE primary type family (a fully evolved evolution line) as the
   deck's win condition, so the strategy narrative is coherent and
   explainable (rubric: "clearly articulated approach").
2. Include a secondary type as a matchup hedge, so the deck isn't
   auto-countered by a single Weakness type (rubric: "avoid
   over-reliance on ... matchups").
3. Keep an energy curve that favors early attackers (Basics that can
   attack turn 1-2) so the agent isn't starved for actions early
   (this is what "stability across repeated matches" partly depends on
   -- a deck that bricks on a bad draw creates high variance).
4. Respect real deck-building legality: exactly 60 cards, max 4 copies
   of any card (except basic Energy), full evolution lines only.
"""
-------------------------------------------------
"""
2)Engine.py
---------
A simplified, self-contained Pokemon TCG battle engine.

WHY THIS EXISTS: the real Kaggle simulator's observation/action API isn't
visible to us yet (it lives behind the Simulation Category's Code/Data
tabs, which need a logged-in Kaggle session to inspect). Rather than
wait, this engine implements the core official ruleset well enough to
(a) test deck-building decisions, (b) develop and benchmark a heuristic
policy, and (c) measure the exact things the rubric scores -- win-rate
stability and matchup generalization -- using self-play.

Once the real environment API is visible, only ONE seam needs to change:
`Agent.choose_action(observation)` -- everything else (deck logic,
heuristics, evaluation harness) ports over conceptually unchanged.

Simplifications vs. full official rules (documented, not hidden):
- No Special Conditions (poison/burn/etc.), Abilities, or item effects
  beyond the 5 sample Trainers implemented below.
- Damage: Weakness = +20 (matches current official rules, not old x2).
- One Prize taken per Knockout (no multi-prize Pokemon).
- Trainers other than the 5 modeled are ignored if drawn.
"""
"""
---------------

---------------------------------------------------
