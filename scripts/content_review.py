#!/usr/bin/env python3
"""Export and safely apply reviewed StepUp Arabic lesson content without editing code."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CURRICULUM_RE = re.compile(r"const CURRICULUM = (\{[\s\S]*?\});\s*const LETTERS=")
FORMAT = "StepUp Arabic content review"
SCHEMA_VERSION = 1


def curriculum_match(html: str) -> re.Match[str]:
    matches = list(CURRICULUM_RE.finditer(html))
    if len(matches) != 1:
        raise ValueError("לא ניתן לזהות בלוק תוכן יחיד ותקין בתוך index.html.")
    return matches[0]


def source_digest(raw_json: str) -> str:
    return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()


def build_review_document(html: str) -> dict[str, Any]:
    match = curriculum_match(html)
    raw = match.group(1)
    curriculum = json.loads(raw)
    records: list[dict[str, Any]] = []

    def add(record_id: str, record_type: str, track: str, lesson: dict[str, Any],
            fields: dict[str, str], location: str) -> None:
        records.append({
            "id": record_id,
            "type": record_type,
            "track": track,
            "lesson_id": lesson["id"],
            "lesson_title": lesson.get("title", ""),
            "location": location,
            "review_status": "pending",
            "reviewer": "",
            "reviewed_at": "",
            "fields": fields,
        })

    for track in ("spoken", "formal"):
        lessons = curriculum.get(track)
        if not isinstance(lessons, list):
            raise ValueError(f"מסלול {track} חסר או אינו תקין.")
        for lesson in lessons:
            lesson_id = str(lesson.get("id", ""))
            if not lesson_id:
                raise ValueError("נמצא שיעור ללא מזהה.")
            add(
                f"{lesson_id}:lesson", "lesson", track, lesson,
                {key: str(lesson.get(key, "")) for key in ("title", "description", "goals", "teaching")},
                "פרטי השיעור וההסבר",
            )
            words = lesson.get("words", [])
            if not isinstance(words, list):
                raise ValueError(f"רשימת המילים של {lesson_id} אינה תקינה.")
            for index, word in enumerate(words, start=1):
                if not isinstance(word, list) or len(word) < 4:
                    raise ValueError(f"פריט מילון לא תקין: {lesson_id}, {index}.")
                add(
                    f"{lesson_id}:word:{index:02d}", "word", track, lesson,
                    {"arabic": str(word[0]), "hebrew": str(word[1]),
                     "transliteration": str(word[2]), "note": str(word[3])},
                    f"מילה {index}",
                )
            examples = lesson.get("examples", [])
            if not isinstance(examples, list):
                raise ValueError(f"דוגמאות השיעור {lesson_id} אינן תקינות.")
            for index, example in enumerate(examples, start=1):
                if not isinstance(example, list) or len(example) < 2:
                    raise ValueError(f"משפט דוגמה לא תקין: {lesson_id}, {index}.")
                add(
                    f"{lesson_id}:example:{index:02d}", "example", track, lesson,
                    {"arabic": str(example[0]), "hebrew": str(example[1])},
                    f"משפט דוגמה {index}",
                )

    return {
        "format": FORMAT,
        "schema_version": SCHEMA_VERSION,
        "source_curriculum_sha256": source_digest(raw),
        "instructions": [
            "יש לערוך רק ערכים בתוך fields; אין לשנות id, type, track או lesson_id.",
            "לאחר בדיקת פריט, לשנות review_status ל-approved ולמלא reviewer ו-reviewed_at.",
            "רק פריטים המסומנים approved יוחזרו לתוכן האפליקציה.",
            "פריטים pending או needs_changes לא ישנו את התוכן.",
            "אם התוכן במאגר השתנה מאז הייצוא, יש לייצא קובץ הגהה חדש.",
        ],
        "records": records,
    }


def apply_review_document(html: str, document: dict[str, Any]) -> tuple[str, int]:
    if not isinstance(document, dict) or document.get("format") != FORMAT:
        raise ValueError("קובץ ההגהה אינו בפורמט של StepUp Arabic.")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("גרסת קובץ ההגהה אינה נתמכת.")
    if not isinstance(document.get("records"), list):
        raise ValueError("רשימת פריטי ההגהה חסרה או פגומה.")

    match = curriculum_match(html)
    raw = match.group(1)
    if document.get("source_curriculum_sha256") != source_digest(raw):
        raise ValueError("קובץ ההגהה מבוסס על תוכן ישן. יש לייצא קובץ חדש לפני החלת תיקונים.")

    curriculum = json.loads(raw)
    indexed: dict[str, tuple[str, dict[str, Any], Any]] = {}
    for track in ("spoken", "formal"):
        for lesson in curriculum[track]:
            lesson_id = lesson["id"]
            indexed[f"{lesson_id}:lesson"] = ("lesson", lesson, None)
            for index, word in enumerate(lesson.get("words", []), start=1):
                indexed[f"{lesson_id}:word:{index:02d}"] = ("word", lesson, word)
            for index, example in enumerate(lesson.get("examples", []), start=1):
                indexed[f"{lesson_id}:example:{index:02d}"] = ("example", lesson, example)

    allowed_fields = {
        "lesson": {"title", "description", "goals", "teaching"},
        "word": {"arabic", "hebrew", "transliteration", "note"},
        "example": {"arabic", "hebrew"},
    }
    required_fields = {
        "lesson": {"title", "description", "goals", "teaching"},
        "word": {"arabic", "hebrew"},
        "example": {"arabic", "hebrew"},
    }
    seen: set[str] = set()
    changed = 0

    for record in document["records"]:
        if not isinstance(record, dict):
            raise ValueError("נמצא פריט הגהה שאינו אובייקט JSON.")
        record_id = record.get("id")
        if not isinstance(record_id, str) or record_id not in indexed:
            raise ValueError(f"מזהה פריט הגהה לא מוכר: {record_id!r}.")
        if record_id in seen:
            raise ValueError(f"מזהה פריט הגהה מופיע פעמיים: {record_id}.")
        seen.add(record_id)

        record_type, lesson, entry = indexed[record_id]
        if record.get("type") != record_type or record.get("lesson_id") != lesson["id"]:
            raise ValueError(f"פרטי הזיהוי של {record_id} אינם תואמים למאגר.")
        status = record.get("review_status", "pending")
        if status not in ("pending", "approved", "needs_changes"):
            raise ValueError(f"סטטוס הגהה לא מוכר עבור {record_id}.")
        if status != "approved":
            continue

        fields = record.get("fields")
        if not isinstance(fields, dict):
            raise ValueError(f"שדות ההגהה של {record_id} אינם תקינים.")
        unknown = set(fields) - allowed_fields[record_type]
        if unknown:
            raise ValueError(f"שדות לא מורשים ב-{record_id}: {', '.join(sorted(unknown))}.")
        missing = required_fields[record_type] - set(fields)
        if missing:
            raise ValueError(f"חסרים שדות חובה ב-{record_id}: {', '.join(sorted(missing))}.")

        for key, value in fields.items():
            if not isinstance(value, str) or len(value) > 2000:
                raise ValueError(f"הערך {key} ב-{record_id} אינו טקסט תקין.")
            if key in required_fields[record_type] and not value.strip():
                raise ValueError(f"הערך {key} ב-{record_id} אינו יכול להיות ריק.")

        if record_type == "lesson":
            target = lesson
            keys = ("title", "description", "goals", "teaching")
            for key in keys:
                if target.get(key) != fields[key]:
                    target[key] = fields[key]
                    changed += 1
        elif record_type == "word":
            keys = ("arabic", "hebrew", "transliteration", "note")
            for index, key in enumerate(keys):
                if key in fields and entry[index] != fields[key]:
                    entry[index] = fields[key]
                    changed += 1
        else:
            for index, key in enumerate(("arabic", "hebrew")):
                if entry[index] != fields[key]:
                    entry[index] = fields[key]
                    changed += 1

    replacement = json.dumps(curriculum, ensure_ascii=False, separators=(",", ":"))
    updated_html = html[:match.start(1)] + replacement + html[match.end(1):]
    return updated_html, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Export or apply a teacher-friendly JSON content review.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    export_parser = subparsers.add_parser("export", help="Export all lessons, words and examples to JSON.")
    export_parser.add_argument("--html", type=Path, default=ROOT / "index.html")
    export_parser.add_argument("--output", type=Path, default=ROOT / "content-review.json")
    apply_parser = subparsers.add_parser("apply", help="Apply only approved corrections to a new HTML file.")
    apply_parser.add_argument("--html", type=Path, default=ROOT / "index.html")
    apply_parser.add_argument("--input", type=Path, required=True)
    apply_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    try:
        html = args.html.read_text(encoding="utf-8")
        if args.command == "export":
            document = build_review_document(html)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"נוצר קובץ הגהה: {args.output} ({len(document['records'])} פריטים)")
            return 0

        document = json.loads(args.input.read_text(encoding="utf-8"))
        updated, changed = apply_review_document(html, document)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(updated, encoding="utf-8")
        print(f"הוחלו {changed} תיקוני שדות בקובץ: {args.output}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"שגיאה: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
