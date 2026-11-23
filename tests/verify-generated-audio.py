#!/usr/bin/env python3
"""Verify all bundled course WAVs, per-file manifests, and font licensing metadata."""
from __future__ import annotations
import array, json, re, sys, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO, GENERATED, FONTS = ROOT / "audio", ROOT / "audio" / "generated", ROOT / "audio" / "fonts"
HTML = (ROOT / "index.html").read_text(encoding="utf-8")

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

def load_json(pattern: str, label: str):
    match = re.search(pattern, HTML)
    require(match is not None, f"Cannot read {label} from index.html")
    return json.loads(match.group(1))

def verify_wav(path: Path, label: str, sample_rate: int = 24000) -> None:
    require(path.is_file(), f"Missing offline audio: {label} ({path})")
    require(path.stat().st_size > 1000, f"Audio file is too small: {label}")
    with wave.open(str(path), "rb") as wav:
        require(wav.getnchannels() == 1, f"Expected mono audio: {label}")
        require(wav.getframerate() == sample_rate, f"Expected {sample_rate} Hz audio: {label}")
        require(wav.getsampwidth() == 2, f"Expected 16-bit PCM audio: {label}")
        require(wav.getcomptype() == "NONE", f"Expected uncompressed PCM audio: {label}")
        require(wav.getnframes() >= 1200, f"Audio is too short: {label}")
        raw = wav.readframes(wav.getnframes())
    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    require(bool(samples), f"Audio has no PCM samples: {label}")
    require(max(abs(value) for value in samples) > 50, f"Audio is silent: {label}")

def verify_manifest(path: Path, expected: dict[str, tuple[str, str, str]], language: str, label: str) -> set[str]:
    require(path.is_file(), f"Missing {label} manifest: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    require(manifest.get("language") == language, f"{label} manifest has the wrong language label")
    require(manifest.get("model_license") == "Apache-2.0", f"{label} model license is missing or unexpected")
    entries = manifest.get("files")
    require(isinstance(entries, list), f"{label} manifest has no file list")
    seen: dict[str, dict] = {}
    for entry in entries:
        require(isinstance(entry, dict), f"{label} manifest contains an invalid entry")
        relative = entry.get("file")
        require(isinstance(relative, str) and relative.startswith("generated/"), f"{label} manifest contains an unsafe file path")
        filename = relative.removeprefix("generated/")
        require(filename not in seen, f"Duplicate {label} manifest entry: {filename}")
        seen[filename] = entry
        require(isinstance(entry.get("text"), str) and entry["text"].strip(), f"Missing source text for {filename}")
        require(entry.get("language") == language, f"Wrong dialect/language label for {filename}")
        require(entry.get("license") == "Apache-2.0", f"Missing model license metadata for {filename}")
    require(set(seen) == set(expected), f"{label} manifest file set does not match curriculum; missing={sorted(set(expected)-set(seen))}, extra={sorted(set(seen)-set(expected))}")
    for filename, (text, lesson_id, item_type) in expected.items():
        entry = seen[filename]
        require(entry.get("text") == text, f"Manifest transcript does not match curriculum: {filename}")
        require(entry.get("lesson") == lesson_id, f"Manifest lesson ID does not match curriculum: {filename}")
        require(entry.get("type") in (None, item_type), f"Manifest type does not match curriculum: {filename}")
        verify_wav(GENERATED / filename, f"{label}: {filename}")
    return set(seen)

curriculum = load_json(r"const CURRICULUM = (\{[\s\S]*?\});[\s\S]*?const LETTERS=", "curriculum")
letters = load_json(r"const LETTERS=(\[[\s\S]*?\]);\s*const KEY=", "Arabic alphabet")
require(len(curriculum["spoken"]) == 24, "Expected 24 Palestinian Arabic lessons")
require(len(curriculum["formal"]) == 33, "Expected 33 MSA lessons")
require(len(letters) == 28, "Expected 28 Arabic letters")

spoken_expected: dict[str, tuple[str, str, str]] = {}
formal_expected: dict[str, tuple[str, str, str]] = {}
example_counts, word_counts = {"spoken": 0, "formal": 0}, {"spoken": 0, "formal": 0}
for track, target in (("spoken", spoken_expected), ("formal", formal_expected)):
    for lesson in curriculum[track]:
        lesson_id = lesson["id"]
        for index, word in enumerate(lesson["words"], start=1):
            require(len(word) >= 4 and str(word[0]).strip(), f"Invalid word in {lesson_id}, item {index}")
            target[f"{lesson_id}-{index:02d}.wav"] = (word[0], lesson_id, "vocabulary")
            word_counts[track] += 1
        for index, example in enumerate(lesson.get("examples", []), start=1):
            require(len(example) >= 2 and str(example[0]).strip() and str(example[1]).strip(), f"Invalid example in {lesson_id}, item {index}")
            target[f"{lesson_id}-example-{index:02d}.wav"] = (example[0], lesson_id, "example-sentence")
            example_counts[track] += 1

letter_names = ["أَلِف","بَاء","تَاء","ثَاء","جِيم","حَاء","خَاء","دَال","ذَال","رَاء","زَاي","سِين","شِين","صَاد","ضَاد","طَاء","ظَاء","عَيْن","غَيْن","فَاء","قَاف","كَاف","لَام","مِيم","نُون","هَاء","وَاو","يَاء"]
require(len(letter_names) == len(letters), "Arabic letter-name mapping does not match alphabet length")
for index, name in enumerate(letter_names, start=1):
    formal_expected[f"letter-{index:02d}.wav"] = (name, "alphabet", "letter-name")

spoken_files = verify_manifest(GENERATED / "spoken-manifest.json", spoken_expected, "Palestinian Arabic", "Palestinian")
formal_files = verify_manifest(GENERATED / "formal-manifest.json", formal_expected, "Modern Standard Arabic", "MSA")
actual_generated = {path.name for path in GENERATED.glob("*.wav")}
expected_generated = spoken_files | formal_files
require(actual_generated == expected_generated, f"Unreferenced or missing generated WAV files; missing={sorted(expected_generated-actual_generated)}, orphaned={sorted(actual_generated-expected_generated)}")

human_targets = {"في الصباح":"msa-in-morning.wav","في مدينة صغيرة":"msa-city-small.wav","في ذات يوم":"msa-one-day.wav","على كوكب بعيد":"msa-on-distant-planet.wav","طعامهم واحد":"msa-their-food-is-the-same.wav"}
human_manifest_path = AUDIO / "manifest.json"
require(human_manifest_path.is_file(), "Human-recording attribution manifest is missing")
human_manifest = json.loads(human_manifest_path.read_text(encoding="utf-8"))
human_entries = list(human_manifest.values())
require(len(human_entries) == len(human_targets), "Human audio manifest count does not match selected clips")
for sentence, filename in human_targets.items():
    matches = [item for item in human_entries if item.get("file") == filename]
    require(len(matches) == 1, f"Human audio manifest entry missing or duplicated: {filename}")
    item = matches[0]
    require(item.get("sentence") == sentence, f"Human audio sentence metadata mismatch: {filename}")
    require(item.get("source") == "https://huggingface.co/datasets/NahwAI/arabic-tashkeel-speech", f"Human audio source missing: {filename}")
    require(item.get("license") == "CC BY 4.0", f"Human audio license missing: {filename}")
    require(item.get("credit") == "Nahw.ai — Nahw Arabic Tashkeel Speech Dataset", f"Human audio credit missing: {filename}")
    verify_wav(AUDIO / filename, f"Human MSA clip {filename}", sample_rate=16000)

font = FONTS / "NotoSansArabic.ttf"
require(font.is_file() and font.stat().st_size > 100_000, "Bundled Arabic font is missing")
font_bytes = font.read_bytes()
require(font_bytes[:4] in (b"\x00\x01\x00\x00", b"OTTO"), "Bundled Arabic font is invalid")
font_license = FONTS / "OFL.txt"
require(font_license.is_file(), "SIL Open Font License text is missing")
require("SIL OPEN FONT LICENSE" in font_license.read_text(encoding="utf-8", errors="replace").upper(), "Bundled font license text is not a valid OFL notice")

print(json.dumps({
    "palestinian_word_audio": word_counts["spoken"],
    "msa_word_audio": word_counts["formal"],
    "arabic_letter_name_audio": len(letters),
    "human_msa_sentence_audio": len(human_targets),
    "spoken_synthetic_example_audio": example_counts["spoken"],
    "formal_synthetic_example_audio": example_counts["formal"],
    "total_generated_wav_files": len(expected_generated),
    "total_wav_files_including_human": len(expected_generated) + len(human_targets),
    "per_file_transcripts_and_license_metadata": "verified",
    "arabic_font": "valid, bundled with SIL OFL notice",
    "format": "24 kHz mono 16-bit PCM WAV (human clips: 16 kHz)",
}, ensure_ascii=False, indent=2))
