#!/usr/bin/env node
/**
 * Build-time-only audio generation for Modern Standard Arabic and letter names.
 * Nabra's Apache-2.0 model runs locally on CPU. The WAVs, not the model/runtime,
 * are included in the end-user installers.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const ROOT = process.cwd();
const NABRA_ROOT = path.join(ROOT, ".build", "nabra-tts");
const { NabraTTS } = await import(pathToFileURL(path.join(NABRA_ROOT, "dist", "index.js")).href);
const HTML = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const OUT = path.join(ROOT, "audio", "generated");
fs.mkdirSync(OUT, { recursive: true });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const curriculumMatch = HTML.match(/const CURRICULUM = (\{[\s\S]*?\});[\s\S]*?const LETTERS=/);
assert(curriculumMatch, "Cannot locate course curriculum");
const curriculum = JSON.parse(curriculumMatch[1]);
const lettersMatch = HTML.match(/const LETTERS=(\[[\s\S]*?\]);\s*const KEY=/);
assert(lettersMatch, "Cannot locate Arabic alphabet");
const letters = JSON.parse(lettersMatch[1]);
assert(curriculum.formal && curriculum.formal.length === 29, "Expected 29 MSA lessons");
assert(letters.length === 28, "Expected 28 Arabic letters");

const letterNames = [
  "أَلِف", "بَاء", "تَاء", "ثَاء", "جِيم", "حَاء", "خَاء", "دَال",
  "ذَال", "رَاء", "زَاي", "سِين", "شِين", "صَاد", "ضَاد", "طَاء",
  "ظَاء", "عَيْن", "غَيْن", "فَاء", "قَاف", "كَاف", "لَام", "مِيم",
  "نُون", "هَاء", "وَاو", "يَاء",
];
assert(letterNames.length === letters.length, "Arabic letter-name map does not match the alphabet");

const require = createRequire(path.join(NABRA_ROOT, "package.json"));
const ortDist = path.dirname(require.resolve("onnxruntime-web")) + path.sep;
const modelBase = "https://huggingface.co/oddadmix/Nabra-7M-Distill-ONNX/resolve/main";

console.log("Loading the offline MSA Arabic voice model...");
const tts = await NabraTTS.load({
  worker: false,
  dtype: "fp16",
  device: "wasm",
  modelUrl: modelBase + "/onnx/model_fp16.onnx",
  voiceUrl: modelBase + "/voices/af_msa.bin",
  wasmPaths: pathToFileURL(ortDist).href,
  cache: false,
  numThreads: 1,
});

const generated = [];
async function writeSpeech(text, filename, lesson, type) {
  const { audio, sampleRate } = await tts.generate(text, { speed: 0.92 });
  assert(sampleRate === 24000, "Unexpected Nabra sample rate");
  assert(audio && audio.length > 1200 && audio.every(Number.isFinite), "Invalid audio for " + text);
  const peak = audio.reduce((max, value) => Math.max(max, Math.abs(value)), 0);
  assert(peak > 0.002, "Nabra produced silent audio for " + text);
  const blob = tts.toWav(audio);
  const bytes = Buffer.from(await blob.arrayBuffer());
  assert(bytes.length > 1000 && bytes.toString("ascii", 0, 4) === "RIFF", "Invalid WAV output");
  fs.writeFileSync(path.join(OUT, filename), bytes);
  generated.push({ file: "generated/" + filename, text, lesson, type, voice: "Nabra MSA", language: "Modern Standard Arabic", license: "Apache-2.0" });
  console.log("Generated " + filename + " (" + bytes.length.toLocaleString() + " bytes)");
}

try {
  for (const lesson of curriculum.formal) {
    for (let i = 0; i < lesson.words.length; i++) {
      const text = lesson.words[i][0];
      const filename = lesson.id + "-" + String(i + 1).padStart(2, "0") + ".wav";
      await writeSpeech(text, filename, lesson.id, "vocabulary");
    }
  }
  for (let i = 0; i < letterNames.length; i++) {
    const filename = "letter-" + String(i + 1).padStart(2, "0") + ".wav";
    await writeSpeech(letterNames[i], filename, "alphabet", "letter-name");
  }
  const manifest = {
    generator: "Nabra-7M-Distill",
    model: "oddadmix/Nabra-7M-Distill-ONNX",
    model_license: "Apache-2.0",
    language: "Modern Standard Arabic",
    sample_rate: 24000,
    files: generated,
  };
  fs.writeFileSync(path.join(OUT, "formal-manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
  console.log("Generated " + generated.length + " MSA and alphabet WAV recordings.");
} finally {
  await tts.dispose();
}

