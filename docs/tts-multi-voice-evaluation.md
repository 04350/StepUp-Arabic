# Multi-voice TTS evaluation for StepUp Arabic 2.0

This document records why an additional synthetic voice has not yet been enabled in the shipped build. The production requirement is: no paid service, offline WAV files, permissive distribution license, and Palestinian Arabic as the first priority.

## Current production voices

- Palestinian spoken track: Sofelia TTS 82M, speaker Eliaa. Apache-2.0. This model is small enough for the current CPU build workflow, but its model card explicitly documents one female voice.
- MSA track and letter names: Nabra-7M-Distill. Apache-2.0. The current checkpoint provides one MSA voice.

## Candidates reviewed

### Sofelia-TTS (larger voice-cloning checkpoint)

Model: https://huggingface.co/hamdallah/Sofelia-TTS

- Apache-2.0 license and Palestinian Arabic generation.
- Supports voice cloning from a 3–10 second reference sample.
- Approximately 0.5–0.6B parameters and the documented training/inference setup targets H100/A100-class GPU hardware.
- This is not a ready-made multiple-speaker model: every additional voice needs a properly licensed reference recording and separate validation.
- It is not used in the normal build because the current CI is CPU-based and the project does not yet have multiple voice-reference recordings with explicit permissions for voice cloning.

### Sofelia Palestinian multi-speaker training checkpoint

Repository: https://huggingface.co/hamdallah/sofelia-tts-checkpoints

- Apache-2.0 license and a documented multi-speaker Stage-2 checkpoint described as Kore + Sirin.
- The checkpoint file is approximately 1.82 GB and is a raw training-state checkpoint, not a ready-to-load Kokoro inference model.
- The repository's extraction script derives a speaker voicepack from representative WAV files for each speaker. Those source speaker recordings / separate voicepacks are not included in the repository's public file listing.
- This is the most relevant Palestinian multi-speaker lead, but it cannot yet produce two verified voices without correctly matched, authorized reference WAVs and a checkpoint-conversion / voicepack extraction test.
- It is not bundled into the app or normal build while those prerequisites are missing.

### Level TTS Arabic

Model: https://huggingface.co/gijl/level-tts-ar

- The model card advertises dialect code `ps` for Palestinian Arabic and zero-shot voice cloning.
- The repository is approximately 7.84 GB and includes an inference checkpoint of around 871 MB plus a much larger training checkpoint.
- No declared license is displayed on the model card. It is therefore not eligible for redistribution in StepUp Arabic unless the author provides a suitable license.
- Not included in the production app.

### A3S

Model: https://huggingface.co/MahmoudIbrahim/A3S

- Apache-2.0 license and three documented Arabic speaker identities (omar, hanouf, fahad).
- The model documents Arabic support for MSA, Saudi and Emirati Arabic, not Palestinian Arabic.
- Approximately 0.6B parameters and its sample generation instructions use a GPU.
- Could be evaluated later as an optional MSA voice set, but it must not be labelled Palestinian or added to the CPU build without a successful generation and quality test.

### Shami-TTS Multi

Model: https://huggingface.co/Tushe/shami-tts-multi

- Ten speaker identities, five male and five female, with Levantine speech.
- The published model card declares CC BY-NC 4.0. That non-commercial restriction is not acceptable for inclusion in a distributable application without separate written permission and legal review.
- Not included in the production app.

## Production decision

Keep the verified Sofelia and Nabra voices as the reliable offline baseline. Do not fake multiple speaker identities by changing pitch or playback speed. Add a new production voice only after all of the following have passed:

1. The model and every dependency permit redistribution in the application.
2. Model inference works on the available Windows build runner without a paid API.
3. At least a sample set of words and full example sentences is generated successfully.
4. Native Arabic quality, accent and consistency are reviewed.
5. Every generated WAV is verified and bundled in both Windows and Android builds.
6. The speaker name, dialect, model and license are recorded in the generated manifests.

Until then, the app accurately identifies the existing Palestinian voice as a single synthetic speaker.
