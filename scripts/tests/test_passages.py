import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_reviewed_passages import (
    assemble_segments,
    pixel_box,
    source_language,
    validate_passage,
)


class PassageTests(unittest.TestCase):
    def test_source_languages_are_distinct_and_unknown_manual_is_rejected(self):
        self.assertEqual(source_language("gol-owner-candidate"), "pt")
        self.assertEqual(source_language("gol-repair-candidate"), "es")
        with self.assertRaises(ValueError):
            source_language("unregistered-manual")

    def test_wrong_language_is_rejected_before_evidence_is_used(self):
        with self.assertRaisesRegex(ValueError, "language"):
            validate_passage(
                dict(rag_eligible=False, applicability_status="pending", language="pt"),
                Path("gol-repair-candidate"),
                Path("unused"),
            )

    def test_columns_and_pages_join_without_losing_warning(self):
        parts = [
            dict(text="Verifique se o ven-", join_next="split_word"),
            dict(text="tilador está funcionando.", join_next="sentence"),
            dict(text="Não coloque o motor em funcionamento."),
        ]
        self.assertEqual(
            assemble_segments(parts),
            "Verifique se o ventilador está funcionando. Não coloque o motor em funcionamento.",
        )

    def test_literal_numbers_and_paragraphs_are_preserved(self):
        self.assertEqual(
            assemble_segments([dict(text="30 a 40 segundos"), dict(text="pág. 6-06")]),
            "30 a 40 segundos\n\npág. 6-06",
        )

    def test_invalid_continuations_do_not_guess_missing_text(self):
        for parts in (
            [dict(text="aviso", join_next="split_word"), dict(text="final")],
            [dict(text="aviso", join_next="sentence")],
        ):
            with self.assertRaises(ValueError):
                assemble_segments(parts)

    def test_bounds_must_stay_on_page_and_have_pixels(self):
        for bounds in ([0, 0, 1.1, 1], [0, 0, 0, 1], [0, 0, 0.001, 0.001]):
            with self.assertRaises(ValueError):
                pixel_box(bounds, 100, 100)

    def test_transcription_cannot_enable_rag(self):
        with self.assertRaises(ValueError):
            validate_passage(
                dict(rag_eligible=True, applicability_status="pending"),
                Path("unused"),
                Path("unused"),
            )
