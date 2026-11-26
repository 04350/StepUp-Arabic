#!/usr/bin/env python3
"""Generate all spoken-track word WAVs with the Apache-2.0 Sofelia Palestinian TTS model.

The model is used only during the build. Generated WAV files are bundled into both
installers, so end users do not need Python, an Arabic Windows language pack, or Internet.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
import wave
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from kokoro import KModel
from misaki import espeak

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "index.html"
WORK = ROOT / ".build" / "sofelia"
OUT = ROOT / "audio" / "generated"
MODEL_REPO = "https://huggingface.co/hamdallah/Sofelia-TTS-82M/resolve/main"
MODEL_FILES = {
    "kokoro_sofelia_82M.pth": (f"{MODEL_REPO}/kokoro_sofelia_82M.pth", 100_000_000),
    "config.json": (f"{MODEL_REPO}/config.json", 1000),
    "sofelia_frontend.py": (f"{MODEL_REPO}/sofelia_frontend.py", 1000),
    "ar_lexicon.json": (f"{MODEL_REPO}/ar_lexicon.json", 100),
    "voices/eliaa.pt": (f"{MODEL_REPO}/voices/eliaa.pt", 100_000),
}


def download(url: str, destination: Path, min_size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size >= min_size:
        return
    request = urllib.request.Request(url, headers={"User-Agent": "StepUp-Arabic-build/1.0"})
    temporary = destination.with_suffix(destination.suffix + ".download")
    print(f"Downloading {destination.name} from the model repository...", flush=True)
    with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as out:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            out.write(block)
    if temporary.stat().st_size < min_size:
        raise RuntimeError(f"Downloaded {destination.name} is too small")
    temporary.replace(destination)


def read_curriculum() -> dict:
    html = HTML.read_text(encoding="utf-8")
    match = re.search(r"const CURRICULUM = (\{[\s\S]*?\});[\s\S]*?const LETTERS=", html)
    if not match:
        raise RuntimeError("Cannot locate the course curriculum in index.html")
    return json.loads(match.group(1))


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, (url, minimum) in MODEL_FILES.items():
        download(url, WORK / filename, minimum)

    # Import the model's frontend from the downloaded, Apache-2.0 repository.
    sys.path.insert(0, str(WORK))
    from sofelia_frontend import text_to_phonemes as dialect_phonemize

    config = str(WORK / "config.json")
    weights = str(WORK / "kokoro_sofelia_82M.pth")
    voice_path = WORK / "voices" / "eliaa.pt"
    device = torch.device("cpu")
    torch.set_num_threads(min(4, torch.get_num_threads()))

    print("Loading Sofelia Palestinian Arabic voice (Eliaa)...", flush=True)
    model = KModel(repo_id="hexgrad/Kokoro-82M", config=config, model=weights).to(device).eval()
    voice = torch.load(voice_path, map_location="cpu", weights_only=True)
    g2p = espeak.EspeakG2P(language="ar")

    curriculum = read_curriculum()
    generated = []
    skipped = []

    def synthesize(text: str, destination: Path) -> None:
        phonemes = dialect_phonemize(text, g2p)[:510]
        if not phonemes:
            raise RuntimeError(f"Sofelia produced no phonemes for: {text}")
        style_index = min(len(phonemes) - 1, voice.shape[0] - 1)
        with torch.inference_mode():
            result = model(phonemes, voice[style_index].to(device), 1.0, return_output=False)
        audio = result.detach().cpu().numpy().squeeze().astype(np.float32)
        if audio.ndim != 1 or audio.size < 1200 or not np.isfinite(audio).all():
            raise RuntimeError(f"Invalid generated audio for: {text}")
        peak = float(np.max(np.abs(audio)))
        if peak < 0.002:
            raise RuntimeError(f"Generated audio is silent for: {text}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(destination), audio, 24000, subtype="PCM_16")

    for lesson in curriculum.get("spoken", []):
        lesson_id = lesson["id"]
        for index, word in enumerate(lesson.get("words", []), start=1):
            if len(word) < 1 or not str(word[0]).strip():
                raise RuntimeError(f"Missing Arabic text in {lesson_id}, word {index}")
            filename = f"{lesson_id}-{index:02d}.wav"
            path = OUT / filename
            synthesize(str(word[0]), path)
            generated.append({"file": f"generated/{filename}", "text": word[0], "lesson": lesson_id, "voice": "Sofelia / Eliaa", "language": "Palestinian Arabic", "license": "Apache-2.0"})

        # Generate a bundled offline recording for every lesson example sentence.
        for example_index, example in enumerate(lesson.get("examples", []), start=1):
            if len(example) < 2 or not str(example[0]).strip():
                raise RuntimeError(f"Invalid example sentence in {lesson_id}")
            example_filename = f"{lesson_id}-example-{example_index:02d}.wav"
            synthesize(str(example[0]), OUT / example_filename)
            generated.append({
                "file": f"generated/{example_filename}",
                "text": example[0],
                "translation": example[1],
                "lesson": lesson_id,
                "type": "example-sentence",
                "voice": "Sofelia / Eliaa",
                "language": "Palestinian Arabic",
                "license": "Apache-2.0",
            })

    manifest = {
        "generator": "Sofelia-TTS-82M",
        "model": "hamdallah/Sofelia-TTS-82M",
        "model_license": "Apache-2.0",
        "speaker": "Eliaa",
        "language": "Palestinian Arabic",
        "sample_rate": 24000,
        "files": generated,
    }
    (OUT / "spoken-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(generated)} Palestinian Arabic word recordings.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
