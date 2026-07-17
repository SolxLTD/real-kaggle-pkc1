import unittest

from card_data import _to_int, _normalize_attack_cost, _normalize_pokemon_type, load_cards
from deck_builder import build_deck


class CardDataTests(unittest.TestCase):
    def test_to_int_returns_none_for_non_numeric_text(self) -> None:
        self.assertIsNone(_to_int("n/a"))

    def test_to_int_parses_numeric_text(self) -> None:
        self.assertEqual(_to_int("42"), 42)

    def test_normalize_pokemon_type_maps_energy_symbols(self) -> None:
        self.assertEqual(_normalize_pokemon_type("{R}"), "Fire")
        self.assertEqual(_normalize_pokemon_type("{W}"), "Water")

    def test_normalize_attack_cost_parses_energy_symbols(self) -> None:
        self.assertEqual(_normalize_attack_cost("{R}{R}●"), "RRC")
        self.assertEqual(_normalize_attack_cost("●●"), "CC")

    def test_build_deck_adds_energy_cards(self) -> None:
        cards = load_cards("EN_Card_Data.csv")
        decklist, _, _ = build_deck(cards, primary_type="Fire", secondary_type="Water")
        self.assertEqual(sum(decklist.values()), 60)
        self.assertTrue(any(cards[cid].category == "Energy" for cid in decklist))


if __name__ == "__main__":
    unittest.main()
