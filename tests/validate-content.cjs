const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync("index.html", "utf8");
function assert(ok, message) { if (!ok) throw new Error(message); }
const match = html.match(/const CURRICULUM = (\{[\s\S]*?\});[\s\S]*?const LETTERS=/);
assert(match, "Curriculum object is missing or malformed");
const curriculum = JSON.parse(match[1]);
assert(curriculum.spoken.length === 20, "Expected exactly 20 spoken lessons");
assert(curriculum.formal.length === 20, "Expected exactly 20 formal lessons");
curriculum.formal.find(x => x.id === "ms-05").words.push(["فِي الصَّبَاحِ","בבוקר","fī aṣ-ṣabāḥ","משפט קצר להאזנה","msa-in-morning.wav"]);
curriculum.formal.find(x => x.id === "ms-07").words.push(["في مَدِينَةٍ صَغيرَة","בעיר קטנה","fī madīna ṣaghīra","משפט קצר להאזנה","msa-city-small.wav"]);
const all = [...curriculum.spoken, ...curriculum.formal];
const ids = new Set();
let vocabCount = 0;
for (const lesson of all) {
  assert(!ids.has(lesson.id), "Duplicate lesson ID: " + lesson.id);
  ids.add(lesson.id);
  assert(lesson.title && lesson.description && lesson.goals, "Lesson metadata missing: " + lesson.id);
  assert(Array.isArray(lesson.words) && lesson.words.length >= 6, "Too few words in " + lesson.id);
  const words = new Set();
  for (const word of lesson.words) {
    assert(word.length >= 4 && word.slice(0,4).every(x => typeof x === "string" && x.trim()), "Incomplete vocab in " + lesson.id);
    assert(!words.has(word[0]), "Duplicate word in " + lesson.id + ": " + word[0]);
    words.add(word[0]); vocabCount++;
  }
}
assert(vocabCount >= 250, "Expected at least 250 vocabulary items; found " + vocabCount);
assert((html.match(/\["[اأإآب-ي]"/g) || []).length >= 28, "Arabic alphabet forms are missing");
assert(html.includes("localStorage"), "Local progress storage missing");
assert(html.includes("StepUp-Arabic-backup.json"), "Backup export missing");
assert(html.includes("data-audio"), "Audio player handling missing");
assert(html.includes("msa-in-morning.wav") && html.includes("msa-city-small.wav"), "Human listening sample references missing");
assert(fs.existsSync("scripts/fetch_audio.py"), "Audio fetch script missing");
const fetchScript = fs.readFileSync("scripts/fetch_audio.py", "utf8");
assert(fetchScript.includes("CC BY 4.0") || fetchScript.includes("CC-BY-4.0"), "Audio source licence must be documented");

assert(!/<script[^>]+src=/.test(html), "Runtime external scripts are not allowed");
assert(!/<link[^>]+href=["']https?:/.test(html), "External runtime stylesheet is not allowed");
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(m => !/\bsrc\s*=/.test(m[1]));
assert(scripts.length, "No inline application script found");
scripts.forEach((m, i) => new vm.Script(m[2].replace(/const CURRICULUM = \{[\s\S]*?\};/, "const CURRICULUM = {};"), { filename: "inline-" + (i + 1) + ".js" }));
const exampleCount = all.filter(x => Array.isArray(x.examples) && x.examples.length).length;
assert(exampleCount === 40, "Every lesson must contain at least one example sentence");
const teachingCount = all.filter(x => typeof x.teaching === "string" && x.teaching.trim()).length;
assert(teachingCount === 40, "Every lesson must contain a teaching explanation");
const bankStart = html.indexOf("function makeQuestionBank(l){");
const bankEnd = html.indexOf("\nfunction teachingMarkup(l)", bankStart);
assert(bankStart >= 0 && bankEnd > bankStart, "Per-lesson question bank function is missing");
const bankSource = html.slice(bankStart, bankEnd);
const bankContext = { shuffle: items => items.slice() };
vm.createContext(bankContext);
vm.runInContext(bankSource, bankContext);
for (const lesson of all) {
  const bank = bankContext.makeQuestionBank(lesson);
  const audioWords = lesson.words.filter(word => word[4]).length;
  assert(bank.length === lesson.words.length * 2 + audioWords, "Each vocabulary item must generate two questions plus one for every audio item: " + lesson.id);
  assert(bank.filter(question => question.audio).length === audioWords, "Each bundled recording must generate a listening question: " + lesson.id);
  const ids = new Set();
  for (const question of bank) {
    assert(!ids.has(question.id), "Duplicate question ID in " + lesson.id);
    ids.add(question.id);
    assert(question.options.length === 4, "Each question must have four answer options");
    assert(new Set(question.options).size === 4, "Question options must be unique");
    assert(question.options.includes(question.answer), "Correct answer is missing from options");
  }
}
assert(html.includes("examplesMarkup"), "Example sentence display is missing");
console.log(JSON.stringify({ spokenLessons: curriculum.spoken.length, formalLessons: curriculum.formal.length, vocabularyItems: vocabCount, lessonsWithExamples: exampleCount, lessonsWithExplanations: teachingCount, generatedQuestionsPerLesson: "2 per vocabulary item plus 1 for each human audio clip", alphabetForms: 28, javascriptSyntax: "passed" }, null, 2));
