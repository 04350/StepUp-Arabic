#!/usr/bin/env python3
"""Fetch Noto Sans Arabic and its SIL Open Font License for offline app packaging."""
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audio" / "fonts"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansarabic"
FILES = {
    "NotoSansArabic.ttf": f"{BASE}/NotoSansArabic%5Bwdth%2Cwght%5D.ttf",
    "OFL.txt": f"{BASE}/OFL.txt",
}

def fetch(name: str, url: str, minimum: int) -> None:
    request = Request(url, headers={"User-Agent": "StepUp-Arabic-build/1.0"})
    with urlopen(request, timeout=120) as response:
        data = response.read()
    if len(data) < minimum:
        raise RuntimeError(f"Downloaded {name} is unexpectedly small ({len(data)} bytes)")
    if name.endswith(".ttf") and data[:4] not in (b"\x00\x01\x00\x00", b"OTTO"):
        raise RuntimeError("Noto Sans Arabic download is not a valid TrueType/OpenType font")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_bytes(data)
    print(f"Bundled {name}: {len(data):,} bytes")

def main() -> None:
    fetch("NotoSansArabic.ttf", FILES["NotoSansArabic.ttf"], 100_000)
    fetch("OFL.txt", FILES["OFL.txt"], 2_000)

if __name__ == "__main__":
    main()
