import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from structure_ocr_tables import draft_cells, literal_candidates, spatial_text


class TableTests(unittest.TestCase):
    def test_decimal_commas_signs_and_ratios_remain_literal(self):
        result = literal_candidates("-2,0 mm; 3,45:1; 0,03 +/- 0,01 mm")
        self.assertIn("-2,0", result["numeric_literals"])
        self.assertIn("3,45:1", result["numeric_literals"])
        self.assertIn("0,03", result["numeric_literals"])

    def test_symbol_units_attached_to_numbers_are_detected(self):
        result = literal_candidates("2% 30°")
        self.assertEqual(result["unit_literals"], ["%", "°"])

    def test_unprinted_units_are_not_inferred(self):
        self.assertEqual(literal_candidates("900 +/- 50")["unit_literals"], [])
        self.assertEqual(literal_candidates("9 +/- 0,5")["unit_literals"], [])

    def test_no_data_abbreviation_is_preserved(self):
        self.assertEqual(
            literal_candidates("S.D."), dict(numeric_literals=[], unit_literals=[])
        )

    def test_spatial_candidates_preserve_every_word_once(self):
        words = [
            dict(id="a", text="A", bbox=[0, 0, 10, 10]),
            dict(id="b", text="0,20", bbox=[100, 0, 125, 10]),
            dict(id="c", text="mm", bbox=[130, 0, 145, 10]),
            dict(id="d", text="N", bbox=[0, 30, 10, 40]),
        ]
        cells = draft_cells(words)
        self.assertEqual(
            sorted(w for c in cells for w in c["word_ids"]), ["a", "b", "c", "d"]
        )
        self.assertTrue(all(c["review_status"] == "pending" for c in cells))

    def test_minor_baseline_variation_does_not_reorder_values(self):
        words = [
            dict(id="a", text="0,40", bbox=[0, 2, 30, 12]),
            dict(id="b", text="a", bbox=[35, 4, 40, 10]),
            dict(id="c", text="0.50", bbox=[45, 1, 75, 13]),
            dict(id="d", text="mm", bbox=[80, 3, 95, 12]),
        ]
        self.assertEqual(spatial_text(words), "0,40 a 0.50 mm")

    def test_empty_table_has_no_invented_cells(self):
        self.assertEqual(draft_cells([]), [])


if __name__ == "__main__":
    unittest.main()
