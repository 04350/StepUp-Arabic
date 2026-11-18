#!/usr/bin/env python3
"""Fetch only two neutral, short MSA clips from the CC BY 4.0 Nahw corpus."""
from __future__ import annotations
import json
from pathlib import Path
import sys

SOURCE = "https://huggingface.co/datasets/NahwAI/arabic-tashkeel-speech"
LICENSE = "CC BY 4.0"
TARGETS = {
    "في الصباح": "msa-in-morning.wav",
    "في مدينة صغيرة": "msa-city-small.wav",
    "في ذات يوم": "msa-one-day.wav",
    "على كوكب بعيد": "msa-on-distant-planet.wav",
    "طعامهم واحد": "msa-their-food-is-the-same.wav",
}

def main() -> int:
    try:
        from datasets import Audio, load_dataset
    except ImportError:
        print("Missing dependency: install requirements-audio.txt", file=sys.stderr)
        return 2

    out = Path("audio")
    out.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("NahwAI/arabic-tashkeel-speech", split="train")
    ds = ds.cast_column("audio", Audio(decode=False))

    saved: dict[str, dict[str, str]] = {}
    for row in ds:
        sentence = " ".join(str(row.get("sentence", "")).split()).strip()
        filename = TARGETS.get(sentence)
        if not filename or filename in {x["file"] for x in saved.values()}:
            continue

        audio = row.get("audio") or {}
        raw = audio.get("bytes")
        if raw is None and audio.get("path"):
            path = Path(audio["path"])
            if path.is_file():
                raw = path.read_bytes()
        if not raw:
            continue

        (out / filename).write_bytes(raw)
        saved[sentence] = {
            "file": filename,
            "sentence": sentence,
            "transcription": str(row.get("transcription", sentence)),
            "speaker_id": str(row.get("speaker_id", "not-specified")),
            "source": SOURCE,
            "license": LICENSE,
            "credit": "Nahw.ai — Nahw Arabic Tashkeel Speech Dataset",
        }
        print(f"Saved {filename} ({len(raw):,} bytes)")

        if len(saved) == len(TARGETS):
            break

    (out / "manifest.json").write_text(
        json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    missing = sorted(set(TARGETS) - set(saved))
    if missing:
        print("Could not find exact audio rows for: " + ", ".join(missing), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
