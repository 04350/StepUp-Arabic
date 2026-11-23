#!/usr/bin/env python3
"""Regression tests for exportable and safely applicable content-review JSON."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from content_review import apply_review_document, build_review_document, curriculum_match  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


html = (ROOT / "index.html").read_text(encoding="utf-8")
document = build_review_document(html)
records = document["records"]
require(document["format"] == "StepUp Arabic content review", "Review format is incorrect")
require(len([r for r in records if r["type"] == "lesson"]) == 57, "Expected review data for all 57 lessons")
require(len([r for r in records if r["type"] == "word"]) >= 404, "Expected all vocabulary entries")
require(len([r for r in records if r["type"] == "example"]) == 57, "Expected example records for all lessons")
require(all(r["review_status"] == "pending" for r in records), "New exports must default to pending")

approved = copy.deepcopy(document)
word = next(r for r in approved["records"] if r["type"] == "word")
old_note = word["fields"]["note"]
word["fields"]["note"] = old_note + " [הגהה אושרה]"
word["review_status"] = "approved"
word["reviewer"] = "test reviewer"
word["reviewed_at"] = "2026-11-24"
updated, changed = apply_review_document(html, approved)
require(changed == 1, "Exactly one approved field should be applied")
new_match = curriculum_match(updated)
curriculum = json.loads(new_match.group(1))
track = word["track"]
lesson = next(x for x in curriculum[track] if x["id"] == word["lesson_id"])
word_index = int(word["id"].rsplit(":", 1)[1]) - 1
require(lesson["words"][word_index][3] == old_note + " [הגהה אושרה]", "Approved correction was not applied")

pending_doc = copy.deepcopy(document)
pending = next(r for r in pending_doc["records"] if r["type"] == "word")
pending["fields"]["note"] = "שינוי שלא אושר"
updated_pending, pending_count = apply_review_document(html, pending_doc)
require(pending_count == 0 and updated_pending == html, "Pending corrections must never alter the app content")

bad_hash = copy.deepcopy(document)
bad_hash["source_curriculum_sha256"] = "0" * 64
try:
    apply_review_document(html, bad_hash)
except ValueError as error:
    require("תוכן ישן" in str(error), "Stale review package should have a clear error")
else:
    raise AssertionError("Stale review packages must be rejected")

duplicate = copy.deepcopy(document)
duplicate["records"].append(copy.deepcopy(duplicate["records"][0]))
try:
    apply_review_document(html, duplicate)
except ValueError as error:
    require("פעמיים" in str(error), "Duplicate IDs should have a clear error")
else:
    raise AssertionError("Duplicate review IDs must be rejected")

invalid = copy.deepcopy(document)
invalid_word = next(r for r in invalid["records"] if r["type"] == "word")
invalid_word["review_status"] = "approved"
invalid_word["fields"]["arabic"] = ""
try:
    apply_review_document(html, invalid)
except ValueError as error:
    require("ריק" in str(error), "Empty essential text should be rejected")
else:
    raise AssertionError("Approved empty Arabic text must be rejected")

print(json.dumps({
    "lessons": 57,
    "words": len([r for r in records if r["type"] == "word"]),
    "examples": len([r for r in records if r["type"] == "example"]),
    "approved_field_changes": changed,
    "pending_changes_ignored": True,
    "stale_package_rejected": True,
    "duplicate_ids_rejected": True,
}, ensure_ascii=False, indent=2))
