import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_accepted_corpus import excerpt_text


class AcceptedExcerptTests(unittest.TestCase):
    def test_exact_values_and_omissions_are_preserved(self):
        original = "Inicio 0,5 l. Excluido. Advertencia: no abrir."
        text, spans = excerpt_text(
            original, ["Inicio 0,5 l.", "Advertencia: no abrir."]
        )
        self.assertEqual(text, "Inicio 0,5 l.\n\n[…]\n\nAdvertencia: no abrir.")
        self.assertEqual(
            [original[s["start"] : s["end"]] for s in spans],
            ["Inicio 0,5 l.", "Advertencia: no abrir."],
        )

    def test_changed_numbers_reordered_and_ambiguous_excerpts_are_rejected(self):
        for original, excerpts in [
            ("Valor 0,5 l", ["Valor 0.5 l"]),
            ("A luego B", ["B", "A"]),
            ("uno uno", ["uno"]),
            ("ABC", ["AB", "BC"]),
            ("ABC", []),
        ]:
            with self.assertRaises(ValueError):
                excerpt_text(original, excerpts)
