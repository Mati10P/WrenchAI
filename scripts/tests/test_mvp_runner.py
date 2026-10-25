"""Evaluation failures must remain visible, even with HTTP 200."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate_mvp import check_reply


class MvpRunnerTests(unittest.TestCase):
    def reply(self):
        return {
            "model": "gemini-synthetic",
            "safety_warning": None,
            "content": {
                "summary": "Salida ficticia",
                "hypotheses": [],
                "checks": [],
                "questions": [],
                "citation_ids": ["own-passage"],
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "Texto propio",
                        "source_ids": ["own-passage"],
                    }
                ],
            },
            "sources": [
                {
                    "id": "own-passage",
                    "page": 9,
                    "pages": [9, 10],
                    "document": {"id": "synthetic-document"},
                }
            ],
        }

    def test_reviewed_multipage_citation_matches_expected_page(self):
        checks = check_reply(
            self.reply(),
            {"safety": False, "expected_pages": ["synthetic-document-0010"]},
        )
        self.assertTrue(all(checks.values()))

    def test_real_but_unrelated_citation_does_not_pass_expected_source(self):
        checks = check_reply(
            self.reply(), {"safety": False, "expected_pages": ["other-document-0010"]}
        )
        self.assertFalse(checks["expected_page"])

    def test_forged_paragraph_and_figure_references_are_reported(self):
        reply = self.reply()
        reply["content"]["blocks"][0]["source_ids"] = ["unknown"]
        reply["content"]["blocks"].append(
            {"type": "illustration", "figure_id": "invented", "caption": "Ficticia"}
        )
        checks = check_reply(reply, {"safety": False})
        self.assertFalse(checks["paragraph_references"])
        self.assertFalse(checks["figure_references"])

    def test_provider_cannot_receive_safety_credit_for_a_warning_string(self):
        reply = copy.deepcopy(self.reply())
        reply["safety_warning"] = (
            "Una cadena de aviso no prueba el guard determinístico"
        )
        checks = check_reply(reply, {"safety": True})
        self.assertFalse(checks["safety_route"])
        self.assertFalse(checks["safety_has_no_model_procedure"])


if __name__ == "__main__":
    unittest.main()
