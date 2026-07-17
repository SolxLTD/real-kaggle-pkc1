"""
card_data.py
------------
Loads card metadata from the competition-provided CSV schema:
Card ID, Card Name, Expansion, Collection No., Stage, Category,
Previous Stage, HP, Type, Weakness, Resistance, Retreat, Rule
(+ attack sub-fields, which are NOT part of the official schema shown
in the competition Data tab, but are required to actually simulate
battles. They're modeled here as an extension so the loader is a strict
superset of the real schema -- drop the real CSV in and only the
attack columns would need to be sourced separately, e.g. via card text
parsing or a supplementary lookup, once you have the real files.)
"""

import csv
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class Attack:
    name: str
    cost: str          # e.g. "FF" = 2 Fire energy, "C" = 1 colorless
    damage: int

    def cost_dict(self) -> Dict[str, int]:
        d: Dict[str, int] = {}
        for ch in self.cost:
            d[ch] = d.get(ch, 0) + 1
        return d

    def energy_count(self) -> int:
        return len(self.cost)


@dataclass
class Card:
    card_id: str
    name: str
    expansion: str
    collection_no: str
    stage: str            # Basic / Stage1 / Stage2 / Trainer / Energy
    category: str         # Pokemon / Trainer / Energy
    previous_stage: Optional[str]
    hp: Optional[int]
    ptype: Optional[str]
    weakness: Optional[str]
    resistance: Optional[str]
    retreat: Optional[int]
    rule_text: str
    attacks: List[Attack] = field(default_factory=list)

    @property
    def is_pokemon(self) -> bool:
        return self.category == "Pokemon"

    @property
    def is_basic(self) -> bool:
        return self.stage == "Basic"


def _get_row_value(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None:
            value = str(value).strip()
            if value:
                return value
    return ""


def _to_int(v: str) -> Optional[int]:
    value = (v or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _normalize_stage(value: str) -> str:
    stage = (value or "").strip()
    if not stage:
        return ""
    lowered = stage.lower()
    if "energy" in lowered:
        return "Energy"
    if "stage 2" in lowered or lowered.endswith("stage2"):
        return "Stage2"
    if "stage 1" in lowered or lowered.endswith("stage1"):
        return "Stage1"
    if "basic" in lowered:
        return "Basic"
    return stage


def _normalize_category(value: str, stage_value: str) -> str:
    raw_category = (value or "").strip()
    raw_stage = (stage_value or "").strip()
    category = raw_category.lower()
    stage = raw_stage.lower()

    if "energy" in stage:
        return "Energy"

    trainer_labels = {
        "trainer", "item", "supporter", "stadium", "tool", "pokemon tool",
        "pokémon tool", "ace spec", "ace spec", "resource", "supporter", "stadium",
    }
    if category in trainer_labels:
        return "Trainer"
    if any(token in stage for token in ("supporter", "stadium", "item", "tool", "ace spec", "resource")):
        return "Trainer"
    if "pokemon" in category or "pokemon" in stage:
        return "Pokemon"
    return "Pokemon"


def _normalize_pokemon_type(v: str) -> Optional[str]:
    value = (v or "").strip()
    if not value or value.lower() in {"n/a", "none", "nan"}:
        return None

    clean_value = value.replace("{", "").replace("}", "").replace(" ", "")
    mapping = {
        "r": "Fire",
        "w": "Water",
        "g": "Grass",
        "l": "Lightning",
        "p": "Psychic",
        "f": "Fighting",
        "m": "Metal",
        "d": "Darkness",
        "c": "Colorless",
        "y": "Fairy",
    }
    if clean_value.lower() in mapping:
        return mapping[clean_value.lower()]

    lower_value = clean_value.lower()
    if lower_value in {"fire", "water", "grass", "lightning", "psychic", "fighting", "metal", "darkness", "colorless", "fairy"}:
        return lower_value.capitalize()
    return value


def _normalize_attack_cost(value: str) -> str:
    raw_value = (value or "").strip()
    if not raw_value or raw_value.lower() in {"n/a", "none", "nan"}:
        return ""

    cleaned = raw_value.replace(" ", "")
    parts: List[str] = []
    i = 0
    while i < len(cleaned):
        char = cleaned[i]
        if char in {"●", "•"}:
            parts.append("C")
            i += 1
        elif char == "{":
            end = cleaned.find("}", i)
            if end != -1:
                token = cleaned[i + 1:end]
                if token.upper() in {"R", "W", "G", "L", "P", "F", "M", "D", "C", "Y"}:
                    parts.append(token.upper())
                else:
                    ptype = _normalize_pokemon_type(token)
                    if ptype == "Fire":
                        parts.append("R")
                    elif ptype == "Water":
                        parts.append("W")
                    elif ptype == "Grass":
                        parts.append("G")
                    elif ptype == "Lightning":
                        parts.append("L")
                    elif ptype == "Psychic":
                        parts.append("P")
                    elif ptype == "Fighting":
                        parts.append("F")
                    elif ptype == "Metal":
                        parts.append("M")
                    elif ptype == "Darkness":
                        parts.append("D")
                    elif ptype == "Colorless":
                        parts.append("C")
                    elif ptype == "Fairy":
                        parts.append("Y")
                i = end + 1
            else:
                i += 1
        elif char.upper() in {"R", "W", "G", "L", "P", "F", "M", "D", "C", "Y"}:
            parts.append(char.upper())
            i += 1
        else:
            i += 1
    return "".join(parts)


def load_cards(csv_path: str) -> Dict[str, Card]:
    cards: Dict[str, Card] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            card_id = _get_row_value(row, "Card ID").strip()
            if not card_id:
                continue

            card = cards.get(card_id)
            if card is None:
                stage_value = _get_row_value(row, "Stage", "Stage (Pokémon)/Type (Energy and Trainer)", "Stage (Pokémon)")
                category_value = _get_row_value(row, "Category")
                card = Card(
                    card_id=card_id,
                    name=_get_row_value(row, "Card Name").strip(),
                    expansion=_get_row_value(row, "Expansion").strip(),
                    collection_no=_get_row_value(row, "Collection No.").strip(),
                    stage=_normalize_stage(stage_value),
                    category=_normalize_category(category_value, stage_value),
                    previous_stage=_get_row_value(row, "Previous Stage", "Previous stage") or None,
                    hp=_to_int(_get_row_value(row, "HP")),
                    ptype=_normalize_pokemon_type(_get_row_value(row, "Type")),
                    weakness=_get_row_value(row, "Weakness") or None,
                    resistance=_get_row_value(row, "Resistance (Type)", "Resistance") or None,
                    retreat=_to_int(_get_row_value(row, "Retreat")),
                    rule_text=_get_row_value(row, "Rule").strip(),
                    attacks=[],
                )
                cards[card_id] = card

            attack_name = _get_row_value(row, "Attack1_Name", "Move Name", "Attack Name")
            if attack_name:
                attack_cost = _normalize_attack_cost(_get_row_value(row, "Attack1_Cost", "Cost"))
                attack_damage = _to_int(_get_row_value(row, "Attack1_Damage", "Damage")) or 0
                card.attacks.append(Attack(
                    name=attack_name,
                    cost=attack_cost,
                    damage=attack_damage,
                ))

            attack2_name = _get_row_value(row, "Attack2_Name")
            if attack2_name:
                attack2_cost = _normalize_attack_cost(_get_row_value(row, "Attack2_Cost"))
                attack2_damage = _to_int(_get_row_value(row, "Attack2_Damage")) or 0
                card.attacks.append(Attack(
                    name=attack2_name,
                    cost=attack2_cost,
                    damage=attack2_damage,
                ))
    return cards


if __name__ == "__main__":
    cards = load_cards("EN_Card_Data.csv")
    print(f"Loaded {len(cards)} cards")
    for c in list(cards.values())[:5]:
        print(c)
