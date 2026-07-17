"""
simulate.py
-----------
Evaluation harness. Runs many games and reports the metrics that map
directly onto the Strategy Category "Model Score" rubric (70% weight):

  - "How consistently does the model perform under repeated matches
     and stable conditions?"          -> win-rate + variance across
                                          many seeded self-play games
  - "How well does the strategy avoid over-reliance on specific
     initial states, matchups, or situational advantages?"
                                       -> win-rate broken out by which
                                          deck went first, and heuristic
                                          agent vs. random-baseline agent
                                          (an ablation, not just a self-play
                                          number that could hide brittleness)

Run: python simulate.py
"""

import random
import statistics as stats
from card_data import load_cards
from deck_builder import build_deck
from engine import Battle
from agent import HeuristicAgent, RandomAgent

N_GAMES = 200


def run_batch(deck_a, deck_b, cards, agent_a_factory, agent_b_factory, n=N_GAMES, seed0=0):
    results = []
    for g in range(n):
        seed = seed0 + g
        rng = random.Random(seed)
        agent_a = agent_a_factory(rng)
        agent_b = agent_b_factory(rng)
        battle = Battle(deck_a, deck_b, cards, agent_a, agent_b, seed=seed)
        winner = battle.run()
        results.append(winner)  # 0 = A wins, 1 = B wins, -1 = draw/cap
    return results


def summarize(results, label_a="A", label_b="B"):
    n = len(results)
    a_wins = results.count(0)
    b_wins = results.count(1)
    draws = results.count(-1)
    win_rate_a = a_wins / n
    return {
        "n": n, "a_wins": a_wins, "b_wins": b_wins, "draws": draws,
        "win_rate_a": win_rate_a,
    }


def bootstrap_ci(results, n_boot=1000):
    """95% CI on A's win rate via bootstrap resampling -- a lightweight
    stand-in for the rubric's 'stability under repeated matches' check."""
    wins = [1 if r == 0 else 0 for r in results]
    n = len(wins)
    rng = random.Random(42)
    boot_means = []
    for _ in range(n_boot):
        sample = [wins[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    lo = boot_means[int(0.025 * n_boot)]
    hi = boot_means[int(0.975 * n_boot)]
    return lo, hi


if __name__ == "__main__":
    cards = load_cards("EN_Card_Data.csv")

    fire_deck, _, _ = build_deck(cards, primary_type="Fire", secondary_type="Water")
    water_deck, _, _ = build_deck(cards, primary_type="Water", secondary_type="Lightning")
    grass_deck, _, _ = build_deck(cards, primary_type="Grass", secondary_type="Fighting")

    print("=" * 60)
    print("EXPERIMENT 1: Heuristic Agent vs Random Agent (same deck)")
    print("Purpose: sanity-check the heuristic actually adds value,")
    print("         not just 'both sides equally bad'.")
    print("=" * 60)
    results = run_batch(
        fire_deck, fire_deck, cards,
        lambda rng: HeuristicAgent(),
        lambda rng: RandomAgent(rng),
        n=N_GAMES,
    )
    s = summarize(results)
    lo, hi = bootstrap_ci(results)
    print(f"Heuristic win rate vs Random: {s['win_rate_a']:.1%} "
          f"(95% CI [{lo:.1%}, {hi:.1%}]) over {s['n']} games. "
          f"Draws/cap-outs: {s['draws']}")

    print()
    print("=" * 60)
    print("EXPERIMENT 2: Matchup generalization")
    print("Purpose: does the Fire deck's win rate hold up across")
    print("         different opposing archetypes? (rubric: avoid")
    print("         over-reliance on specific matchups)")
    print("=" * 60)
    for opp_name, opp_deck in [("Water", water_deck), ("Grass", grass_deck)]:
        results = run_batch(
            fire_deck, opp_deck, cards,
            lambda rng: HeuristicAgent(),
            lambda rng: HeuristicAgent(),
            n=N_GAMES,
        )
        s = summarize(results)
        lo, hi = bootstrap_ci(results)
        print(f"Fire deck vs {opp_name} deck: {s['win_rate_a']:.1%} win rate "
              f"(95% CI [{lo:.1%}, {hi:.1%}]) over {s['n']} games. "
              f"Draws/cap-outs: {s['draws']}")

    print()
    print("=" * 60)
    print("EXPERIMENT 3: First-move advantage check")
    print("Purpose: quantify how much of the win rate is explained by")
    print("         going first vs. actual play quality (initial-state")
    print("         reliance check from the rubric).")
    print("=" * 60)
    results_ab = run_batch(fire_deck, water_deck, cards,
                            lambda rng: HeuristicAgent(), lambda rng: HeuristicAgent(), n=N_GAMES // 2)
    results_ba = run_batch(water_deck, fire_deck, cards,
                            lambda rng: HeuristicAgent(), lambda rng: HeuristicAgent(), n=N_GAMES // 2)
    fire_win_going_first = results_ab.count(0) / len(results_ab)
    fire_win_going_second = results_ba.count(1) / len(results_ba)
    print(f"Fire deck win rate when going FIRST:  {fire_win_going_first:.1%}")
    print(f"Fire deck win rate when going SECOND: {fire_win_going_second:.1%}")
    print(f"Delta (first-move advantage size): {abs(fire_win_going_first - fire_win_going_second):.1%}")
