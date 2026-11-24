"""Safe, idempotent CSV-to-MongoDB BSON loader for Olist order reviews.

Reads `olist_order_reviews_dataset.csv` with UTF-8/RFC-4180 multiline support,
validates every row, quarantines rejected rows to JSONL, and inserts nested
BSON documents into `retail_reviews.order_reviews` using deterministic `_id`
(`{review_id}::{order_id}`) and `InsertOne(..., ordered=False)` so reruns
never duplicate or overwrite existing documents.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlsplit, urlunsplit
import uuid

DEFAULT_CSV_PATH = Path("datasets/Olist-Store/olist_order_reviews_dataset.csv")
DEFAULT_DATABASE = "retail_reviews"
DEFAULT_COLLECTION = "order_reviews"
DEFAULT_BATCH_SIZE = 1000
SCHEMA_VERSION = "1.0.0"

EXPECTED_COLUMNS = [
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp",
]

TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
HEX32_RE = re.compile(r"^[0-9a-fA-F]{32}$")


@dataclass
class LoadStats:
    """Counters for auditable ingestion reporting."""

    total_read: int = 0
    valid_built: int = 0
    inserted: int = 0
    matched: int = 0
    rejected: int = 0
    failed: int = 0
    write_concern_uncertain: int = 0


STABLE_COMPARE_FIELDS = (
    "review_id",
    "order_id",
    "review_score",
    "comment",
    "timestamps",
)


def redact_mongo_uri(uri: str) -> str:
    """Mask userinfo credentials in a MongoDB connection URI for safe logging."""
    try:
        parts = urlsplit(uri)
        if "@" in parts.netloc:
            _, host = parts.netloc.rsplit("@", 1)
            return urlunsplit((parts.scheme, f"***:***@{host}", parts.path, parts.query, parts.fragment))
        return uri
    except ValueError:
        return "<unparseable-uri-redacted>"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest of a file using streaming reads."""
    digest = hashlib.sha256()
    with file_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_timestamp(value: str, field_name: str) -> str:
    if not value or not TIMESTAMP_RE.match(value):
        raise ValueError(f"INVALID_TIMESTAMP:{field_name}")
    datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value


def build_review_document(
    row: dict[str, str],
    row_number: int,
    source_file: str,
    source_sha256: str,
    run_id: str,
    ingested_at_utc: datetime,
) -> dict[str, Any]:
    """Validate one CSV row and transform it into the target nested BSON document."""
    review_id = (row.get("review_id") or "").strip()
    order_id = (row.get("order_id") or "").strip()
    if not review_id or not HEX32_RE.match(review_id):
        raise ValueError("INVALID_REVIEW_ID")
    if not order_id or not HEX32_RE.match(order_id):
        raise ValueError("INVALID_ORDER_ID")

    score_raw = (row.get("review_score") or "").strip()
    try:
        review_score = int(score_raw)
    except ValueError as exc:
        raise ValueError("INVALID_REVIEW_SCORE_TYPE") from exc
    if review_score < 1 or review_score > 5:
        raise ValueError("INVALID_REVIEW_SCORE_RANGE")

    creation_raw = _validate_timestamp(
        (row.get("review_creation_date") or "").strip(), "review_creation_date"
    )
    answer_raw = _validate_timestamp(
        (row.get("review_answer_timestamp") or "").strip(), "review_answer_timestamp"
    )

    # Preserve valid comment text verbatim (including UTF-8 and line breaks);
    # map empty strings to BSON null.
    raw_title = row.get("review_comment_title")
    raw_message = row.get("review_comment_message")
    comment_title = None if raw_title is None or raw_title == "" else raw_title
    comment_message = None if raw_message is None or raw_message == "" else raw_message

    return {
        "_id": f"{review_id}::{order_id}",
        "review_id": review_id,
        "order_id": order_id,
        "review_score": review_score,
        "comment": {
            "title": comment_title,
            "message": comment_message,
        },
        "timestamps": {
            "review_creation_date_raw": creation_raw,
            "review_answer_timestamp_raw": answer_raw,
            "source_timezone_note": "unspecified_naive_source_string",
        },
        "source_lineage": {
            "source_system": "olist_csv",
            "source_file": source_file,
            "source_file_sha256": source_sha256,
            "source_row_number": row_number,
            "ingestion_run_id": run_id,
            "ingested_at_utc": ingested_at_utc,
            "schema_version": SCHEMA_VERSION,
        },
    }


def _stable_payload(doc: dict[str, Any]) -> dict[str, Any]:
    """Extract only stable source fields for duplicate-key content comparison."""
    return {field: doc.get(field) for field in STABLE_COMPARE_FIELDS}


def _flush_batch(
    collection: Any,
    batch: list[dict[str, Any]],
    stats: LoadStats,
    quarantine_fh: Any,
) -> None:
    """Insert a batch without overwriting existing docs; verify duplicates against stable fields."""
    if not batch:
        return
    from pymongo import InsertOne
    from pymongo.errors import BulkWriteError

    ops = [InsertOne(doc) for doc in batch]
    try:
        result = collection.bulk_write(ops, ordered=False)
        stats.inserted += int(result.inserted_count)
    except BulkWriteError as bwe:
        details = bwe.details or {}
        stats.inserted += int(details.get("nInserted", 0))
        dup_candidates: list[dict[str, Any]] = []

        for err in details.get("writeErrors", []):
            code = err.get("code")
            idx = err.get("index")
            incoming = batch[idx] if isinstance(idx, int) and 0 <= idx < len(batch) else None
            doc_id = incoming["_id"] if incoming is not None else None
            if code == 11000:
                if incoming is None:
                    stats.failed += 1
                    quarantine_fh.write(
                        json.dumps(
                            {
                                "reason_code": "DUPLICATE_KEY_MISSING_BATCH_INDEX",
                                "error_message": err.get("errmsg"),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                else:
                    dup_candidates.append(incoming)
            else:
                stats.failed += 1
                quarantine_fh.write(
                    json.dumps(
                        {
                            "reason_code": f"MONGO_WRITE_ERROR_{code}",
                            "error_message": err.get("errmsg"),
                            "_id": doc_id,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        if dup_candidates:
            dup_ids = [doc["_id"] for doc in dup_candidates]
            projection = {"_id": 1, **{field: 1 for field in STABLE_COMPARE_FIELDS}}
            try:
                existing_by_id = {
                    doc["_id"]: doc
                    for doc in collection.find({"_id": {"$in": dup_ids}}, projection)
                }
            except Exception as exc:
                for incoming in dup_candidates:
                    stats.failed += 1
                    quarantine_fh.write(
                        json.dumps(
                            {
                                "reason_code": "DUPLICATE_KEY_VERIFICATION_ERROR",
                                "_id": incoming["_id"],
                                "error_message": str(exc),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            else:
                for incoming in dup_candidates:
                    doc_id = incoming["_id"]
                    existing = existing_by_id.get(doc_id)
                    if existing is None:
                        stats.failed += 1
                        quarantine_fh.write(
                            json.dumps(
                                {
                                    "reason_code": "DUPLICATE_KEY_EXISTING_NOT_FOUND",
                                    "_id": doc_id,
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )
                    elif _stable_payload(existing) == _stable_payload(incoming):
                        stats.matched += 1
                    else:
                        stats.failed += 1
                        quarantine_fh.write(
                            json.dumps(
                                {
                                    "reason_code": "DUPLICATE_KEY_CONTENT_MISMATCH",
                                    "_id": doc_id,
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )

        for wc_err in details.get("writeConcernErrors", []):
            # Write-concern errors do not identify which batch documents failed;
            # record the uncertain batch outcome separately without per-record guessing.
            stats.write_concern_uncertain += 1
            quarantine_fh.write(
                json.dumps(
                    {
                        "reason_code": "MONGO_WRITE_CONCERN_UNCERTAIN",
                        "batch_size": len(batch),
                        "error_detail": wc_err,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def run_load(
    csv_path: Path,
    mongo_uri: str | None,
    database_name: str,
    collection_name: str,
    batch_size: int,
    quarantine_path: Path,
    dry_run: bool,
) -> LoadStats:
    """Stream CSV, validate records, and execute safe batched MongoDB inserts."""
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Source CSV not found: {csv_path}")
    if not dry_run and not mongo_uri:
        raise RuntimeError(
            "MONGODB_URI environment variable is required when not running with --dry-run."
        )

    run_id = str(uuid.uuid4())
    ingested_at_utc = datetime.now(timezone.utc)
    source_sha256 = compute_sha256(csv_path)
    stats = LoadStats()
    seen_ids_in_run: set[str] = set()

    quarantine_path.parent.mkdir(parents=True, exist_ok=True)

    client: Any = None
    collection: Any = None
    if not dry_run:
        from pymongo import MongoClient

        assert mongo_uri is not None
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        collection = client[database_name][collection_name]

    try:
        with (
            csv_path.open("r", encoding="utf-8-sig", newline="") as csv_fh,
            quarantine_path.open("w", encoding="utf-8") as q_fh,
        ):
            reader = csv.DictReader(csv_fh)
            if reader.fieldnames != EXPECTED_COLUMNS:
                raise ValueError(
                    f"Unexpected CSV header {reader.fieldnames}; expected {EXPECTED_COLUMNS}"
                )

            batch: list[dict[str, Any]] = []
            for row_num, row in enumerate(reader, start=1):
                stats.total_read += 1
                if None in row:
                    stats.rejected += 1
                    q_fh.write(
                        json.dumps(
                            {
                                "source_row_number": row_num,
                                "reason_code": "EXTRA_CSV_COLUMNS",
                                "raw_record": row,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    continue

                try:
                    doc = build_review_document(
                        row=row,
                        row_number=row_num,
                        source_file=csv_path.name,
                        source_sha256=source_sha256,
                        run_id=run_id,
                        ingested_at_utc=ingested_at_utc,
                    )
                except ValueError as exc:
                    stats.rejected += 1
                    q_fh.write(
                        json.dumps(
                            {
                                "source_row_number": row_num,
                                "reason_code": str(exc),
                                "review_id": row.get("review_id"),
                                "order_id": row.get("order_id"),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    continue

                if doc["_id"] in seen_ids_in_run:
                    stats.rejected += 1
                    q_fh.write(
                        json.dumps(
                            {
                                "source_row_number": row_num,
                                "reason_code": "DUPLICATE_COMPOSITE_KEY_IN_CSV",
                                "_id": doc["_id"],
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    continue

                seen_ids_in_run.add(doc["_id"])
                stats.valid_built += 1

                if not dry_run:
                    batch.append(doc)
                    if len(batch) >= batch_size:
                        _flush_batch(collection, batch, stats, q_fh)
                        batch.clear()

            if not dry_run and batch:
                _flush_batch(collection, batch, stats, q_fh)
                batch.clear()
    finally:
        if client is not None:
            client.close()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "mode": "dry_run" if dry_run else "live_insert",
                "csv_path": str(csv_path),
                "source_sha256": source_sha256,
                "target": None if dry_run else f"{database_name}.{collection_name}",
                "mongo_uri": None if dry_run or not mongo_uri else redact_mongo_uri(mongo_uri),
                "total_read": stats.total_read,
                "valid_built": stats.valid_built,
                "inserted": stats.inserted,
                "matched": stats.matched,
                "rejected": stats.rejected,
                "failed": stats.failed,
                "write_concern_uncertain": stats.write_concern_uncertain,
                "quarantine_file": str(quarantine_path),
            },
            indent=2,
        )
    )
    return stats


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Idempotent Olist Reviews CSV -> MongoDB BSON loader."
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path(os.environ.get("REVIEWS_CSV_PATH", str(DEFAULT_CSV_PATH))),
        help="Path to olist_order_reviews_dataset.csv",
    )
    parser.add_argument(
        "--database",
        default=os.environ.get("MONGODB_DATABASE", DEFAULT_DATABASE),
        help="Target MongoDB database name",
    )
    parser.add_argument(
        "--collection",
        default=os.environ.get("MONGODB_COLLECTION", DEFAULT_COLLECTION),
        help="Target MongoDB collection name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("MONGODB_BATCH_SIZE", str(DEFAULT_BATCH_SIZE))),
        help="Bulk insert batch size",
    )
    parser.add_argument(
        "--quarantine-path",
        type=Path,
        default=Path("logs/reviews_quarantine.jsonl"),
        help="Path to write rejected/failed record metadata",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate CSV and build BSON documents without connecting to MongoDB",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mongo_uri = os.environ.get("MONGODB_URI")
    try:
        stats = run_load(
            csv_path=args.csv_path,
            mongo_uri=mongo_uri,
            database_name=args.database,
            collection_name=args.collection,
            batch_size=args.batch_size,
            quarantine_path=args.quarantine_path,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if stats.rejected > 0 or stats.failed > 0 or stats.write_concern_uncertain > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
