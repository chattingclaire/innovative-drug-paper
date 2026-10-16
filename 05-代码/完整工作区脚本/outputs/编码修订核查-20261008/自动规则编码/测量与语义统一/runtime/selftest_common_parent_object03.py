"""Six constructed source-relation checks; no dimension coding or real labels."""

import copy
import unittest
from unittest.mock import patch

import common_parent_object03 as module


def fixture(parent_text="药品管理协议的有关安排，具体包括以下几点：", current_text="一是按有关程序办理后续事项。"):
    parent = {"id": "parent", "text": parent_text, "pages": [1], "line_ids": ["1:1"]}
    current = {"id": "current", "text": current_text, "pages": [1], "line_ids": ["1:2"]}
    record = {
        "unit_id": "unit", "unit_text": current_text, "pages": [1],
        "source": "/constructed/source.pdf", "source_sha256": "source-hash",
        "candidate_file": "/constructed/candidate.json", "candidate_sha256": "candidate-hash",
        "paragraph_context": [{"paragraph_id": "current", "text": current_text, "pages": [1]}],
        "immediately_preceding_paragraph": {"text": parent_text, "pages": [1]},
    }
    doc = {"unit_candidates": [{"id": "unit", "paragraph_id": "current", "text": current_text, "pages": [1]}],
           "paragraphs": [parent, current]}
    return record, doc


def authenticated_context(context):
    result = copy.deepcopy(context)
    result["authentication_v34"] = {"method": "constructed_authentication_stub", "literal_reproduced_in_current_runtime": True}
    return result


class ParentObjectTests(unittest.TestCase):
    def resolve(self, record, doc, target_failure=None):
        with patch.object(module, "authenticate_target", side_effect=target_failure) as target_auth, \
             patch.object(module, "candidate", return_value=doc), \
             patch.object(module, "authenticate_context", side_effect=authenticated_context) as context_auth:
            result = module.resolve_enumerated_drug_object(record)
            return result, target_auth, context_auth

    def test_1_actual_first_item_retains_authentication_without_dimensions(self):
        record, doc = fixture()
        result, target_auth, context_auth = self.resolve(record, doc)
        self.assertIsNotNone(result)
        target_auth.assert_called_once_with(record)
        self.assertEqual(context_auth.call_count, 1)
        self.assertTrue(result["drug_scope"])
        self.assertFalse(result["dimension_assignment"])
        self.assertFalse(result["labels_may_be_copied"])
        self.assertEqual(result["parent_paragraph_id"], "parent")
        self.assertEqual(result["parent_text"], doc["paragraphs"][0]["text"])
        self.assertEqual(result["source_sha256"], "source-hash")
        self.assertIn("authentication_v34", result["parent_context"])
        self.assertTrue(result["current_paragraph_binding"]["authenticated"])
        self.assertFalse(result["current_paragraph_binding"]["independent_current_paragraph_literal_reproduction_performed"])
        relation = result["relation"]
        self.assertEqual(result["parent_text"][relation["drug_object_start"]:relation["drug_object_end"]], relation["drug_object_quote"])
        self.assertNotIn("Ec", result)
        self.assertNotIn("S", result)

    def test_2_neighbor_without_explicit_enumeration_is_rejected(self):
        record, doc = fixture(parent_text="药品管理协议的有关安排已经另行公布。")
        result, _, context_auth = self.resolve(record, doc)
        self.assertIsNone(result)
        context_auth.assert_not_called()

    def test_3_second_item_does_not_inherit_first_item_relation(self):
        record, doc = fixture(current_text="二是按有关程序办理后续事项。")
        result, target_auth, _ = self.resolve(record, doc)
        self.assertIsNone(result)
        target_auth.assert_not_called()

    def test_4_actual_intervening_paragraph_cannot_be_skipped(self):
        record, doc = fixture()
        doc["paragraphs"].insert(1, {"id": "intervening", "text": "这里另有一段说明。", "pages": [1]})
        result, _, context_auth = self.resolve(record, doc)
        self.assertIsNone(result)
        context_auth.assert_not_called()

    def test_5_drug_mentioned_only_in_title_is_rejected(self):
        record, doc = fixture(parent_text="《药品管理办法》的附件安排，具体包括以下几点：")
        result, _, context_auth = self.resolve(record, doc)
        self.assertIsNone(result)
        context_auth.assert_not_called()

    def test_6_failed_source_hash_authentication_remains_explicit(self):
        record, doc = fixture()
        with self.assertRaisesRegex(ValueError, "constructed source hash mismatch"):
            self.resolve(record, doc, ValueError("constructed source hash mismatch"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
