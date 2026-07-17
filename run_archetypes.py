from collections import Counter
import random
from card_data import load_cards
from deck_builder import build_deck
from engine import Battle
from agent import HeuristicAgent, AggressiveAgent, DefensiveAgent, EnergyFloodAgent, DrawComboAgent, SwitchTempoAgent

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
        results.append(winner)
    return results


def summarize(results):
    n = len(results)
    a_wins = results.count(0)
    b_wins = results.count(1)
    draws = results.count(-1)
    return {"n": n, "a_wins": a_wins, "b_wins": b_wins, "draws": draws, "win_rate_a": a_wins / n}


if __name__ == "__main__":
    cards = load_cards("EN_Card_Data.csv")
    fire_deck, _, _ = build_deck(cards, primary_type="Fire", secondary_type="Water")

    archetypes = [
        ("Aggressive", lambda rng: AggressiveAgent(rng)),
        ("Defensive", lambda rng: DefensiveAgent(rng)),
        ("EnergyFlood", lambda rng: EnergyFloodAgent(rng)),
        ("DrawCombo", lambda rng: DrawComboAgent(rng)),
        ("SwitchTempo", lambda rng: SwitchTempoAgent(rng)),
    ]

    results = {}
    for name, factory in archetypes:
        print(f"Running Heuristic vs {name} ({N_GAMES} games)")
        res = run_batch(fire_deck, fire_deck, cards, lambda rng: HeuristicAgent(), factory, n=N_GAMES)
        s = summarize(res)
        results[name] = s
        lo = 0.0
        hi = 0.0
        print(f"Heuristic win rate vs {name}: {s['win_rate_a']:.1%} over {s['n']} games (A wins {s['a_wins']}, B wins {s['b_wins']}, draws {s['draws']})")

    # quick local summary
    print('\nSummary:')
    for name, s in results.items():
        print(f"- vs {name}: {s['win_rate_a']:.1%} (A wins {s['a_wins']}, B wins {s['b_wins']}, draws {s['draws']})")
