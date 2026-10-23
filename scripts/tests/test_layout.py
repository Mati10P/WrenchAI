"""Guard against losing technical labels while separating illustration noise."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from segment_ocr_layout import (
    NARRATIVE,
    apply_region_overrides,
    choose_region,
    reading_order,
    text_for_words,
)


def region(identifier, kind, box):
    return dict(id=identifier, type=kind, bbox=box, confidence=0.95)


class LayoutTests(unittest.TestCase):
    def test_labels_inside_picture_do_not_leak_into_prose(self):
        regions = [
            region("figure", "picture", [20, 20, 80, 80]),
            region("text", "text", [0, 0, 100, 100]),
        ]
        self.assertEqual(choose_region([30, 30, 40, 40], regions), "figure")
        self.assertEqual(choose_region([0, 0, 10, 10], regions), "text")

    def test_short_units_and_labels_in_prose_are_preserved(self):
        words = [dict(text=t, line_id="one") for t in ["A", "N", "mm", "0,20"]]
        self.assertEqual(text_for_words(words, []), "A N mm 0,20")

    def test_visual_override_can_reunite_borderless_table_labels_and_values(self):
        spec = {
            "add_regions": [
                {
                    "id": "manual-table",
                    "type": "table",
                    "bbox_normalized": [0, 0, 1, 1],
                    "reason": "Test bounds",
                }
            ]
        }
        regions = apply_region_overrides(
            [region("text", "text", [0, 0, 30, 30])], spec, 100, 100
        )
        self.assertEqual(choose_region([5, 5, 15, 15], regions), "manual-table")
        self.assertEqual(choose_region([80, 5, 90, 15], regions), "manual-table")
        self.assertIsNone(regions[-1]["confidence"])

    def test_invalid_override_bounds_are_rejected(self):
        spec = {
            "add_regions": [
                {
                    "id": "bad",
                    "type": "text",
                    "bbox_normalized": [0, 0, 2, 1],
                    "reason": "Invalid",
                }
            ]
        }
        with self.assertRaises(ValueError):
            apply_region_overrides([], spec, 100, 100)

    def test_unmatched_words_remain_unassigned(self):
        self.assertIsNone(
            choose_region([80, 80, 90, 90], [region("text", "text", [0, 0, 30, 30])])
        )

    def test_table_values_stay_with_table(self):
        regions = [
            region("table", "table", [0, 0, 100, 100]),
            region("text", "text", [10, 10, 40, 40]),
        ]
        self.assertEqual(choose_region([15, 15, 25, 25], regions), "table")

    def test_column_order_does_not_interleave_rows(self):
        regions = [
            region("right1", "text", [60, 10, 90, 20]),
            region("left2", "text", [0, 30, 40, 40]),
            region("left1", "text", [0, 10, 40, 20]),
            region("right2", "text", [60, 30, 90, 40]),
        ]
        self.assertEqual(
            [r["id"] for r in reading_order(regions)],
            ["left1", "left2", "right1", "right2"],
        )

    def test_footnotes_remain_part_of_narrative_context(self):
        self.assertIn("footnote", NARRATIVE)

    def test_full_width_heading_precedes_separate_columns(self):
        regions = [
            region("heading", "title", [0, 0, 100, 10]),
            region("right", "text", [60, 30, 100, 80]),
            region("left", "text", [0, 30, 40, 80]),
        ]
        self.assertEqual(
            [r["id"] for r in reading_order(regions)], ["heading", "left", "right"]
        )

    def test_manual_correction_applies_only_to_exact_line(self):
        words = [
            dict(text="PL", line_id="one"),
            dict(text="PL", line_id="two"),
            dict(text="real", line_id="two"),
        ]
        self.assertEqual(
            text_for_words(words, [dict(before="\nPL\n", after="\n")]), "PL real"
        )


if __name__ == "__main__":
    unittest.main()
