"""Unit tests for the Olist Reviews MongoDB BSON transformer, validator, and batch flusher."""

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "ingestion"))

from mongodb_reviews_loader import (
    LoadStats,
    _flush_batch,
    build_review_document,
    redact_mongo_uri,
    run_load,
)


class FakeBulkWriteError(Exception):
    def __init__(self, details: dict) -> None:
        super().__init__("fake bulk write error")
        self.details = details


class FakeInsertOne:
    def __init__(self, document: dict) -> None:
        self.document = document


def _make_fake_pymongo_modules() -> dict[str, types.ModuleType]:
    pymongo_mod = types.ModuleType("pymongo")
    pymongo_mod.InsertOne = FakeInsertOne  # type: ignore[attr-defined]
    errors_mod = types.ModuleType("pymongo.errors")
    errors_mod.BulkWriteError = FakeBulkWriteError  # type: ignore[attr-defined]
    pymongo_mod.errors = errors_mod  # type: ignore[attr-defined]
    return {"pymongo": pymongo_mod, "pymongo.errors": errors_mod}


class FakeCollection:
    def __init__(self, bulk_exc: Exception | None = None, find_docs: list[dict] | None = None, find_exc: Exception | None = None) -> None:
        self.bulk_exc = bulk_exc
        self.find_docs = find_docs or []
        self.find_exc = find_exc

    def bulk_write(self, ops: list, ordered: bool = False) -> object:
        if self.bulk_exc is not None:
            raise self.bulk_exc
        return types.SimpleNamespace(inserted_count=len(ops))

    def find(self, query: dict, projection: dict) -> list[dict]:
        if self.find_exc is not None:
            raise self.find_exc
        wanted = set(query["_id"]["$in"])
        return [d for d in self.find_docs if d["_id"] in wanted]


class TestMongoDbReviewsLoader(unittest.TestCase):
    def setUp(self) -> None:
        self.base_row = {
            "review_id": "a" * 32,
            "order_id": "b" * 32,
            "review_score": "5",
            "review_comment_title": "",
            "review_comment_message": "Linha 1\nÓtimo produto!",
            "review_creation_date": "2018-01-18 00:00:00",
            "review_answer_timestamp": "2018-01-18 21:46:59",
        }
        self.now = datetime(2026, 11, 21, 2, 0, 0, tzinfo=timezone.utc)

    def _doc(self, suffix: str = "a", score: str = "5", run_id: str = "run-1") -> dict:
        row = dict(
            self.base_row,
            review_id=suffix * 32,
            order_id=("b" if suffix == "a" else suffix) * 32,
            review_score=score,
        )
        return build_review_document(
            row=row,
            row_number=1,
            source_file="olist_order_reviews_dataset.csv",
            source_sha256="0" * 64,
            run_id=run_id,
            ingested_at_utc=self.now,
        )

    def test_deterministic_id_null_title_and_utf8_multiline_preserved(self) -> None:
        doc = self._doc()
        self.assertEqual(doc["_id"], f"{'a' * 32}::{'b' * 32}")
        self.assertEqual(doc["review_score"], 5)
        self.assertIsNone(doc["comment"]["title"])
        self.assertEqual(doc["comment"]["message"], "Linha 1\nÓtimo produto!")
        self.assertEqual(doc["timestamps"]["review_creation_date_raw"], "2018-01-18 00:00:00")
        self.assertEqual(doc["timestamps"]["source_timezone_note"], "unspecified_naive_source_string")

    def test_invalid_score_rejected(self) -> None:
        bad = dict(self.base_row, review_score="6")
        with self.assertRaises(ValueError):
            build_review_document(bad, 2, "f.csv", "0" * 64, "run-1", self.now)

    def test_invalid_timestamp_rejected(self) -> None:
        bad = dict(self.base_row, review_answer_timestamp="not-a-timestamp")
        with self.assertRaises(ValueError):
            build_review_document(bad, 3, "f.csv", "0" * 64, "run-1", self.now)

    def test_redact_mongo_uri_masks_credentials(self) -> None:
        self.assertEqual(
            redact_mongo_uri("mongodb://admin:s3cr3t@localhost:27017/retail_reviews"),
            "mongodb://***:***@localhost:27017/retail_reviews",
        )
        self.assertEqual(
            redact_mongo_uri("mongodb://localhost:27017"),
            "mongodb://localhost:27017",
        )

    def test_duplicate_key_identical_stable_payload_is_matched(self) -> None:
        incoming = self._doc(run_id="run-new")
        existing = self._doc(run_id="run-old")
        existing["source_lineage"]["ingested_at_utc"] = datetime(2026, 11, 20, 0, 0, tzinfo=timezone.utc)
        col = FakeCollection(
            bulk_exc=FakeBulkWriteError({"nInserted": 0, "writeErrors": [{"index": 0, "code": 11000, "errmsg": "dup"}]}),
            find_docs=[existing],
        )
        stats = LoadStats()
        q = io.StringIO()
        with patch.dict(sys.modules, _make_fake_pymongo_modules()):
            _flush_batch(col, [incoming], stats, q)
        self.assertEqual(stats.matched, 1)
        self.assertEqual(stats.failed, 0)
        self.assertEqual(q.getvalue(), "")

    def test_duplicate_key_different_payload_is_failed_and_quarantined(self) -> None:
        incoming = self._doc(score="5")
        existing = self._doc(score="1")
        col = FakeCollection(
            bulk_exc=FakeBulkWriteError({"nInserted": 0, "writeErrors": [{"index": 0, "code": 11000, "errmsg": "dup"}]}),
            find_docs=[existing],
        )
        stats = LoadStats()
        q = io.StringIO()
        with patch.dict(sys.modules, _make_fake_pymongo_modules()):
            _flush_batch(col, [incoming], stats, q)
        self.assertEqual(stats.matched, 0)
        self.assertEqual(stats.failed, 1)
        rec = json.loads(q.getvalue().strip())
        self.assertEqual(rec["reason_code"], "DUPLICATE_KEY_CONTENT_MISMATCH")
        self.assertEqual(rec["_id"], incoming["_id"])

    def test_duplicate_key_when_existing_cannot_be_retrieved_is_failed(self) -> None:
        incoming = self._doc()
        # Case A: missing from find() result
        col_missing = FakeCollection(
            bulk_exc=FakeBulkWriteError({"nInserted": 0, "writeErrors": [{"index": 0, "code": 11000}]}),
            find_docs=[],
        )
        stats_a = LoadStats()
        q_a = io.StringIO()
        with patch.dict(sys.modules, _make_fake_pymongo_modules()):
            _flush_batch(col_missing, [incoming], stats_a, q_a)
        self.assertEqual(stats_a.matched, 0)
        self.assertEqual(stats_a.failed, 1)
        self.assertEqual(json.loads(q_a.getvalue().strip())["reason_code"], "DUPLICATE_KEY_EXISTING_NOT_FOUND")

        # Case B: find() raises read error
        col_err = FakeCollection(
            bulk_exc=FakeBulkWriteError({"nInserted": 0, "writeErrors": [{"index": 0, "code": 11000}]}),
            find_exc=RuntimeError("read timeout"),
        )
        stats_b = LoadStats()
        q_b = io.StringIO()
        with patch.dict(sys.modules, _make_fake_pymongo_modules()):
            _flush_batch(col_err, [incoming], stats_b, q_b)
        self.assertEqual(stats_b.matched, 0)
        self.assertEqual(stats_b.failed, 1)
        self.assertEqual(json.loads(q_b.getvalue().strip())["reason_code"], "DUPLICATE_KEY_VERIFICATION_ERROR")

    def test_partial_bulk_success_with_dup_write_error_and_write_concern_uncertain(self) -> None:
        d0 = self._doc("a")
        d1 = self._doc("c")
        d2 = self._doc("d")
        col = FakeCollection(
            bulk_exc=FakeBulkWriteError(
                {
                    "nInserted": 1,
                    "writeErrors": [
                        {"index": 1, "code": 11000, "errmsg": "dup"},
                        {"index": 2, "code": 121, "errmsg": "doc validation failed"},
                    ],
                    "writeConcernErrors": [{"code": 64, "errmsg": "waiting for replication timed out"}],
                }
            ),
            find_docs=[d1],
        )
        stats = LoadStats()
        q = io.StringIO()
        with patch.dict(sys.modules, _make_fake_pymongo_modules()):
            _flush_batch(col, [d0, d1, d2], stats, q)
        self.assertEqual(stats.inserted, 1)
        self.assertEqual(stats.matched, 1)
        self.assertEqual(stats.failed, 1)
        self.assertEqual(stats.write_concern_uncertain, 1)
        reasons = [json.loads(line)["reason_code"] for line in q.getvalue().strip().splitlines()]
        self.assertEqual(reasons, ["MONGO_WRITE_ERROR_121", "MONGO_WRITE_CONCERN_UNCERTAIN"])

    def test_logical_source_row_number_across_multiline_csv(self) -> None:
        csv_text = (
            "review_id,order_id,review_score,review_comment_title,review_comment_message,"
            "review_creation_date,review_answer_timestamp\n"
            f"{'1'*32},{'2'*32},5,,\"Line 1\nLine 2\nLine 3\",2018-01-01 00:00:00,2018-01-02 00:00:00\n"
            f"{'3'*32},{'4'*32},4,Bom,\"Single line\",2018-01-03 00:00:00,2018-01-04 00:00:00\n"
            f"bad_id,{'5'*32},3,,,2018-01-05 00:00:00,2018-01-06 00:00:00\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "reviews.csv"
            q_path = Path(tmp) / "quarantine.jsonl"
            csv_path.write_text(csv_text, encoding="utf-8")
            stats = run_load(
                csv_path=csv_path,
                mongo_uri=None,
                database_name="retail_reviews",
                collection_name="order_reviews",
                batch_size=10,
                quarantine_path=q_path,
                dry_run=True,
            )
            self.assertEqual(stats.total_read, 3)
            self.assertEqual(stats.valid_built, 2)
            self.assertEqual(stats.rejected, 1)
            q_rec = json.loads(q_path.read_text(encoding="utf-8").strip())
            # Logical CSV record 3 (despite 5 physical lines due to embedded newlines in record 1)
            self.assertEqual(q_rec["source_row_number"], 3)
            self.assertEqual(q_rec["reason_code"], "INVALID_REVIEW_ID")


if __name__ == "__main__":
    unittest.main()
