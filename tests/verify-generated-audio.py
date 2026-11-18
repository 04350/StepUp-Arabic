#!/usr/bin/env python3
"""Verify every course word and alphabet letter has a real, non-silent offline WAV."""
from __future__ import annotations

import array
import json
import re
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
GENERATED = AUDIO / "generated"
FONTS = AUDIO / "fonts"
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(pattern: str, label: str):
    match = re.search(pattern, HTML)
    require(match is not None, f"Cannot read {label} from index.html")
    return json.loads(match.group(1))


def verify_wav(path: Path, label: str) -> None:
    require(path.is_file(), f"Missing offline audio: {label} ({path})")
    require(path.stat().st_size > 1000, f"Audio file is too small: {label}")
    with wave.open(str(path), "rb") as wav:
        require(wav.getnchannels() == 1, f"Expected mono audio: {label}")
        require(wav.getframerate() == 24000, f"Expected 24 kHz audio: {label}")
        require(wav.getsampwidth() == 2, f"Expected 16-bit PCM audio: {label}")
        require(wav.getcomptype() == "NONE", f"Expected uncompressed PCM audio: {label}")
        require(wav.getnframes() >= 1200, f"Audio is too short: {label}")
        raw = wav.readframes(wav.getnframes())
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    require(bool(samples), f"Audio has no PCM samples: {label}")
    peak = max(abs(value) for value in samples)
    require(peak > 50, f"Audio is silent: {label}")


curriculum = load_json(r"const CURRICULUM = (\{[\s\S]*?\});[\s\S]*?const LETTERS=", "curriculum")
letters = load_json(r"const LETTERS=(\[[\s\S]*?\]);\s*const KEY=", "Arabic alphabet")
require(len(curriculum["spoken"]) == 20, "Expected 20 Palestinian Arabic lessons")
require(len(curriculum["formal"]) == 29, "Expected 29 MSA lessons")
require(len(letters) == 28, "Expected 28 Arabic letters")

expected_spoken = 0
expected_formal = 0
for track, expected in (("spoken", "Palestinian Arabic"), ("formal", "Modern Standard Arabic")):
    for lesson in curriculum[track]:
        for index, word in enumerate(lesson["words"], start=1):
            require(word and str(word[0]).strip(), f"Empty word in {lesson['id']} at {index}")
            filename = f"{lesson['id']}-{index:02d}.wav"
            verify_wav(GENERATED / filename, f"{expected}: {lesson['id']} word {index} ({word[0]})")
            if track == "spoken":
                expected_spoken += 1
            else:
                expected_formal += 1

for index, letter in enumerate(letters, start=1):
    verify_wav(GENERATED / f"letter-{index:02d}.wav", f"Arabic letter {letter[0]}")

spoken_manifest = json.loads((GENERATED / "spoken-manifest.json").read_text(encoding="utf-8"))
formal_manifest = json.loads((GENERATED / "formal-manifest.json").read_text(encoding="utf-8"))
require(len(spoken_manifest["files"]) == expected_spoken, "Palestinian manifest count does not match curriculum")
require(len(formal_manifest["files"]) == expected_formal + len(letters), "MSA/alphabet manifest count does not match curriculum")
require(spoken_manifest["language"] == "Palestinian Arabic", "Spoken track voice is not labelled Palestinian")
require(formal_manifest["language"] == "Modern Standard Arabic", "Formal track voice is not labelled MSA")

for human_clip in (
    "msa-in-morning.wav",
    "msa-city-small.wav",
    "msa-one-day.wav",
    "msa-on-distant-planet.wav",
    "msa-their-food-is-the-same.wav",
):
    verify_wav(AUDIO / human_clip, f"Human MSA clip {human_clip}")

font = FONTS / "NotoSansArabic.ttf"
require(font.is_file() and font.stat().st_size > 100_000, "Bundled Arabic font is missing")
font_bytes = font.read_bytes()
require(font_bytes[:4] in (b"\x00\x01\x00\x00", b"OTTO"), "Bundled Arabic font is invalid")
require((FONTS / "OFL.txt").is_file(), "SIL Open Font License text is missing")

print(json.dumps({
    "palestinian_word_audio": expected_spoken,
    "msa_word_audio": expected_formal,
    "arabic_letter_name_audio": len(letters),
    "human_msa_sentence_audio": 5,
    "total_wav_files": expected_spoken + expected_formal + len(letters) + 5,
    "arabic_font": "valid, bundled with OFL.txt",
    "format": "24 kHz mono 16-bit PCM WAV",
}, ensure_ascii=False, indent=2))
