"""Generic image-attachment interface checks, never dimension expectations."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import source_packet


TEST_ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceImageInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="reader-interface-", dir=TEST_ROOT)
        self.root = Path(self.temp.name)
        (self.root / "source-pages").mkdir()
        self.image = self.root / "source-pages/source.jpg"
        self.image.write_bytes(b"\xff\xd8\xffsynthetic-asset-binding\xff\xd9")
        self.page = self.root / "source-pages/page.png"
        self.page.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic-page-binding")
        self.source_sha = "a" * 64
        self.row = {
            "id": "synthetic-source", "text": "来源原文。", "pages": [1],
            "contexts": [{
                "context_id": "CTX-synthetic", "kind": "paragraph",
                "source_document": "原始来源", "text": "原始上下文。",
                "structure": {"paragraph_id": "P1"},
                "source_ref": {"sha256": self.source_sha, "locator": {"paragraph_id": "P1"}},
            }],
            "source_page_attachments": [{
                "attachment_id": "source-page", "physical_page": 1,
                "relative_path": "source-pages/page.png", "sha256": digest(self.page),
                "source_pdf_sha256": self.source_sha,
            }],
            "source_image_attachments": [{
                "attachment_id": "source-image", "mime_type": "image/jpeg",
                "relative_path": "source-pages/source.jpg", "sha256": digest(self.image),
                "source_url": "https://example.invalid/original-source.jpg",
            }],
        }

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, row=None):
        row = self.row if row is None else row
        source = self.root / "source.jsonl"
        source.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        manual = self.root / "manual.md"
        manual.write_text("共有手册测试绑定。\n", encoding="utf-8")
        manifest = {
            "status": "sealed_development_fixture_not_formal_test_or_human_reference",
            "n": 1,
            "outputs": [{"path": str(p), "sha256": digest(p)} for p in [source, manual]],
            "source_pages": [{"path": str(p), "sha256": digest(p)} for p in [self.page, self.image]],
        }
        path = self.root / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return source, path

    def load(self, row=None):
        return source_packet.load_fixture(*self.fixture(row))

    def geometry_row(self):
        row = copy.deepcopy(self.row)
        context = row["contexts"][0]
        context["kind"] = "table_group_row"
        geometry = {
            "grid_row_index_convention": "0 denotes the header row",
            "physical_grid_row_index_zero_based": 1,
            "physical_merged_cells": [{
                "column_index": 0, "physical_grid_column_span": 2,
                "physical_grid_row_span": 1, "physical_grid_row_start_zero_based": 1,
                "text": "原始合并单元格。",
            }],
            "source_group_context_id": "CTX-synthetic",
            "table_text_context_ids": ["CTX-synthetic"],
            "source_image_sha256": digest(self.image),
        }
        context["structure"].update(copy.deepcopy(geometry))
        context["source_ref"]["locator"].update(copy.deepcopy(geometry))
        context["source_ref"]["locator"]["json_pointer"] = "/tables/0/rows/1"
        return row

    def test_preserves_full_original_attachment_fields(self):
        loaded = self.load()
        self.assertEqual(loaded, [self.row])
        unit = source_packet.semantic_unit(loaded[0])
        self.assertNotIn("id", unit)
        self.assertEqual(unit["attachments"], self.row["source_page_attachments"])
        self.assertEqual(unit["source_image_attachments"], self.row["source_image_attachments"])
        self.assertNotIn("physical_page", unit["source_image_attachments"][0])
        self.assertNotIn("source_pdf_sha256", unit["source_image_attachments"][0])
        unit["source_image_attachments"][0]["source_url"] = "changed copy"
        self.assertEqual(loaded[0]["source_image_attachments"][0]["source_url"],
                         self.row["source_image_attachments"][0]["source_url"])

    def test_non_image_mime_rejected(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["mime_type"] = "application/pdf"
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "image MIME"):
            self.load(row)

    def test_malformed_image_mime_rejected(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["mime_type"] = "image/jpeg; label=1"
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "image MIME"):
            self.load(row)

    def test_absolute_attachment_path_rejected(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["relative_path"] = str(self.image)
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "fixture-relative"):
            self.load(row)

    def test_escaped_attachment_path_rejected(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["relative_path"] = "../../outside.jpg"
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "inside the sealed fixture"):
            self.load(row)

    def test_attachment_sha_mismatch_rejected(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["sha256"] = "b" * 64
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "sealed asset SHA"):
            self.load(row)

    def test_asset_byte_sha_mismatch_rejected(self):
        paths = self.fixture()
        self.image.write_bytes(b"changed")
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "image SHA mismatch"):
            source_packet.load_fixture(*paths)

    def test_result_key_injection_rejected(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["labels"] = {"I": 1}
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "result or administrative"):
            self.load(row)

    def test_unknown_image_field_requires_review(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["physical_page"] = 1
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "unknown fields"):
            self.load(row)

    def test_shared_attachment_identity_rejected(self):
        row = copy.deepcopy(self.row)
        row["source_image_attachments"][0]["attachment_id"] = "source-page"
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "duplicate source attachment"):
            self.load(row)

    def test_original_geometry_and_context_kinds_preserved(self):
        for kind in ("table_group_row", "preceding_flattened_table_data_row"):
            with self.subTest(kind=kind):
                row = self.geometry_row()
                row["contexts"][0]["kind"] = kind
                loaded = self.load(row)
                self.assertEqual(loaded, [row])
                self.assertEqual(source_packet.semantic_unit(loaded[0])["contexts"], row["contexts"])

    def test_physical_grid_row_index_boolean_rejected(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["physical_grid_row_index_zero_based"] = True
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "expected an integer"):
            self.load(row)

    def test_merged_cell_zero_span_rejected(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["physical_merged_cells"][0]["physical_grid_row_span"] = 0
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "integer >= 1"):
            self.load(row)

    def test_geometry_sha_format_rejected(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["source_image_sha256"] = "wrong"
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "lowercase SHA256"):
            self.load(row)

    def test_geometry_sha_unbound_to_original_image_rejected(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["source_image_sha256"] = "c" * 64
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "absent from original image attachments"):
            self.load(row)

    def test_new_geometry_ctx_refs_require_closure(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["table_text_context_ids"] = ["CTX-missing"]
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "dangling CTX"):
            self.load(row)

    def test_result_in_merged_geometry_rejected(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["physical_merged_cells"][0]["labels"] = {"I": 1}
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "result or administrative"):
            self.load(row)

    def test_both_original_column_binding_shapes_preserved(self):
        for pair in (
            {"column_index": 0, "cell_index": 0, "header_index": 0},
            {"column_index": 0, "cell_index": 0,
             "header_context_id": "CTX-synthetic", "cell_context_id": "CTX-synthetic"},
        ):
            with self.subTest(pair=pair):
                row = self.geometry_row()
                row["contexts"][0]["structure"]["row_cell_column_pairs"] = [pair]
                loaded = self.load(row)
                self.assertEqual(loaded, [row])
                self.assertEqual(source_packet.semantic_unit(loaded[0])["contexts"], row["contexts"])

    def test_column_binding_shape_mixing_rejected(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["row_cell_column_pairs"] = [{
            "column_index": 0, "cell_index": 0, "header_index": 0,
            "header_context_id": "CTX-synthetic", "cell_context_id": "CTX-synthetic",
        }]
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "unknown fields"):
            self.load(row)

    def test_negative_header_index_rejected(self):
        row = self.geometry_row()
        row["contexts"][0]["structure"]["row_cell_column_pairs"] = [{
            "column_index": 0, "cell_index": 0, "header_index": -1,
        }]
        with self.assertRaisesRegex(source_packet.PacketInterfaceError, "integer >= 0"):
            self.load(row)


if __name__ == "__main__":
    unittest.main(verbosity=2)
