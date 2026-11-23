# Audio and font attribution

## Human-recorded MSA sentence clips

The five WAV files in the root of this folder are unmodified excerpts from:

**Nahw.ai — Nahw Arabic Tashkeel Speech Dataset**  
Source: https://huggingface.co/datasets/NahwAI/arabic-tashkeel-speech  
License: Creative Commons Attribution 4.0 International (CC BY 4.0)  
Dataset authors: Nahw.ai  
Dataset description: native Arabic speakers, recordings reviewed by human annotators, 16 kHz audio.

The selected clips are:
- في الصباح — msa-in-morning.wav
- في مدينة صغيرة — msa-city-small.wav
- في ذات يوم — msa-one-day.wav
- على كوكب بعيد — msa-on-distant-planet.wav
- طعامهم واحد — msa-their-food-is-the-same.wav

These are the only human-recorded sentence clips in this release. They are general Arabic/MSA-style read speech, not Palestinian dialect. No endorsement by Nahw.ai is implied. The fetch script selects exact sentence matches and copies the original WAV bytes without editing them.

## Generated Palestinian Arabic word speech

The files under `generated/sp-*.wav` are synthesized at build time with:

- Model: Sofelia TTS 82M — https://huggingface.co/hamdallah/Sofelia-TTS-82M
- Model license: Apache License 2.0
- Voice pack: Eliaa
- Intended variety: Levantine/Palestinian Arabic
- Output: 24 kHz mono PCM WAV

The model is used only by the build process. The end-user EXE and APK contain the finished WAV files; they do not contain or run the model, Python, PyTorch, or an online speech service. These files are synthetic speech, not human-recorded lesson clips. The model card notes that it uses a single voice and that numbers/dates/times may be expanded with MSA pronunciation.

## Generated MSA words and Arabic letter names

The files under `generated/ms-*.wav` and `generated/letter-*.wav` are synthesized at build time with:

- Model: Nabra-7M-Distill — https://huggingface.co/oddadmix/Nabra-7M-Distill
- ONNX export: https://huggingface.co/oddadmix/Nabra-7M-Distill-ONNX
- Model and generator license: Apache License 2.0
- Intended variety: Modern Standard Arabic (MSA)
- Output: 24 kHz mono PCM WAV

The Nabra engine runs only during the build process. Only the resulting WAV files are packaged in the Windows and Android installers. The model is not downloaded or executed on the user's device.

## Bundled Arabic typeface

- Typeface: Noto Sans Arabic
- Source: https://github.com/google/fonts/tree/main/ofl/notosansarabic
- License: SIL Open Font License 1.1
- The exact `OFL.txt` license is included beside the bundled `NotoSansArabic.ttf` file under `fonts/`.

## Offline operation

All generated and human-recorded WAV files, the Arabic font, and its license are included in both installers. After installation, playback and Arabic text rendering do not require an Arabic Windows language pack, a separate speech engine, or an Internet connection.

The build-generated manifests under `generated/` identify each text, lesson, voice/model, language variety, and license.


## Generated lesson example sentences (StepUp Arabic 2.0)

All example sentences attached to the 57 lessons receive a separate generated WAV file during the build:
- Palestinian spoken track: Sofelia TTS 82M, Eliaa voice, Apache-2.0 model.
- Modern Standard Arabic track: Nabra-7M-Distill, Apache-2.0 model.
- Output: 24 kHz mono PCM WAV.
These are AI-synthesized examples, not human recordings. The translation and lesson ID are recorded in the generated manifest.


## Asset and license audit

The authoritative inventory of bundled audio and font assets is maintained in `docs/license-audit.md`. The CI verifier cross-checks each generated WAV against its source text, lesson ID, dialect label and model-license metadata, and checks the five human-recorded clips against their CC BY 4.0 attribution manifest. Build-time TTS dependencies are not packaged in the end-user installers.
