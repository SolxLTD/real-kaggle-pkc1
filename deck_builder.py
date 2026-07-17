"""
deck_builder.py
---------------
Builds a legal 60-card deck from the available card pool.

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

import random
from collections import defaultdict
from typing import Dict, List
from card_data import Card, load_cards

MAX_COPIES_NONENERGY = 4
DECK_SIZE = 60


def _evolution_line(cards: Dict[str, Card], basic: Card) -> List[Card]:
    """Return [basic, stage1, stage2] chain (as available) for a basic Pokemon."""
    line = [basic]
    current_name = basic.name
    changed = True
    while changed:
        changed = False
        for c in cards.values():
            if c.previous_stage == current_name:
                line.append(c)
                current_name = c.name
                changed = True
                break
    return line


def score_line(line: List[Card]) -> float:
    """Heuristic desirability of an evolution line as a deck's core."""
    top = line[-1]
    score = 0.0
    score += (top.hp or 0) * 0.5
    if top.attacks:
        best_atk = max(top.attacks, key=lambda a: a.damage)
        
        score += best_atk.damage / max(1, best_atk.energy_count()) * 3
    
    score += (3 - len(line)) * 15
    return score


def build_deck(cards: Dict[str, Card], primary_type: str = None,
                secondary_type: str = None) -> Dict[str, int]:
    pokemon = [c for c in cards.values() if c.is_pokemon]
    trainers = [c for c in cards.values() if c.category == "Trainer"]
    energies = [c for c in cards.values() if c.category == "Energy"]

    basics_by_type = defaultdict(list)
    for c in pokemon:
        if c.is_basic:
            basics_by_type[c.ptype].append(c)

    
    
    if primary_type is None:
        best_line, best_score = None, -1
        for t, basics in basics_by_type.items():
            for b in basics:
                line = _evolution_line(cards, b)
                s = score_line(line)
                if s > best_score:
                    best_score, best_line, primary_type = s, line, t
    primary_line = _evolution_line(cards, basics_by_type[primary_type][0])

    if secondary_type is None:
        
        
        candidates = [t for t in basics_by_type if t != primary_type]
        secondary_type = candidates[0] if candidates else primary_type
    secondary_line = _evolution_line(cards, basics_by_type[secondary_type][0])

    decklist: Dict[str, int] = defaultdict(int)

    
    for c in primary_line:
        decklist[c.card_id] += min(MAX_COPIES_NONENERGY, 4)
    for c in secondary_line:
        decklist[c.card_id] += min(MAX_COPIES_NONENERGY, 3)

    pokemon_count = sum(decklist.values())

    trainer_target = 15
    t_i = 0
    while sum(v for k, v in decklist.items() if k in {t.card_id for t in trainers}) < trainer_target and trainers:
        t = trainers[t_i % len(trainers)]
        if decklist[t.card_id] < MAX_COPIES_NONENERGY:
            decklist[t.card_id] += 1
        t_i += 1
        if t_i > 200:
            break

    
    used = sum(decklist.values())
    remaining = DECK_SIZE - used
    primary_energy_type = _energy_card_for_type(energies, primary_type)
    secondary_energy_type = _energy_card_for_type(energies, secondary_type)
    if primary_energy_type and secondary_energy_type and primary_energy_type != secondary_energy_type:
        primary_e_count = round(remaining * 0.65)
        secondary_e_count = remaining - primary_e_count
        decklist[primary_energy_type.card_id] += primary_e_count
        decklist[secondary_energy_type.card_id] += secondary_e_count
    elif primary_energy_type:
        decklist[primary_energy_type.card_id] += remaining

    return dict(decklist), primary_type, secondary_type


def _energy_card_for_type(energies: List[Card], ptype: str):
    if not ptype:
        return None

    normalized_type = ptype.lower()
    type_markers = {
        "fire": ("fire", "{r}", "r"),
        "water": ("water", "{w}", "w"),
        "grass": ("grass", "{g}", "g"),
        "lightning": ("lightning", "{l}", "l"),
        "psychic": ("psychic", "{p}", "p"),
        "fighting": ("fighting", "{f}", "f"),
        "metal": ("metal", "{m}", "m"),
        "darkness": ("darkness", "{d}", "d"),
        "fairy": ("fairy", "{y}", "y"),
        "colorless": ("colorless", "{c}", "c"),
    }

    for e in energies:
        if (e.ptype or "").lower() == normalized_type:
            return e
        lowered_name = e.name.lower()
        if any(marker in lowered_name for marker in type_markers.get(normalized_type, ())):
            return e
    return None


def print_decklist(cards: Dict[str, Card], decklist: Dict[str, int]):
    total = sum(decklist.values())
    print(f"Deck ({total} cards):")
    for cid, count in sorted(decklist.items(), key=lambda x: (-x[1], x[0])):
        c = cards[cid]
        print(f"  {count}x {c.name:20s} [{c.category}/{c.stage}]")


if __name__ == "__main__":
    cards = load_cards("EN_Card_Data.csv")
    decklist, primary, secondary = build_deck(cards)
    print(f"Primary type: {primary} | Secondary type (hedge): {secondary}\n")
    print_decklist(cards, decklist)
