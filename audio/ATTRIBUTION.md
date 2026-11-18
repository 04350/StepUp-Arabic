# Audio attribution

The WAV files placed in this folder by scripts/fetch_audio.py are unmodified excerpts from:

**Nahw.ai — Nahw Arabic Tashkeel Speech Dataset**  
Source: https://huggingface.co/datasets/NahwAI/arabic-tashkeel-speech  
License: Creative Commons Attribution 4.0 International (CC BY 4.0)  
Dataset authors: Nahw.ai  
Dataset description: native Arabic speakers, recordings reviewed by human annotators, 16 kHz audio.

Only these exact neutral sentence clips are selected for the first build:
- في الصباح — msa-in-morning.wav
- في مدينة صغيرة — msa-city-small.wav
- في ذات يوم — msa-one-day.wav
- على كوكب بعيد — msa-on-distant-planet.wav
- طعامهم واحد — msa-their-food-is-the-same.wav

Attribution is provided as required by CC BY 4.0. No endorsement by Nahw.ai is implied. The source language is general Arabic/MSA-style read speech; it is not labelled as Palestinian dialect, and the app must not present it as such.

The fetch script selects rows by exact unvowelled sentence and copies the original WAV bytes without editing them.
