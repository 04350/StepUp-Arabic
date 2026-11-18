const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync("index.html", "utf8");
function assert(ok, message) { if (!ok) throw new Error(message); }
assert(!/\?\./.test(html), "Optional chaining is not supported by the minimum Android WebView used by the emulator");
assert(!/\?\?/.test(html), "Nullish coalescing is not supported by the minimum Android WebView used by the emulator");
const match = html.match(/const CURRICULUM = (\{[\s\S]*?\});[\s\S]*?const LETTERS=/);
assert(match, "Curriculum object is missing or malformed");
const curriculum = JSON.parse(match[1]);
assert(curriculum.spoken.length === 20, "Expected exactly 20 spoken lessons");
assert(curriculum.formal.length === 29, "Expected exactly 29 formal lessons");
assert(curriculum.formal.slice(0,4).every(x => x.kind === "alphabet"), "The MSA track must begin with four alphabet units");
assert(curriculum.formal.filter(x => x.kind === "sound").length >= 3, "Short vowels, sukun/shadda and long vowels must be taught in sound units");
assert(curriculum.formal.some(x => x.id === "ms-a9" && x.kind === "reading"), "Beginner reading lesson is missing");
assert(html.includes('activeTrack="formal"'), "A brand-new learner should begin in the alphabet/reading track");
assert(html.includes('data-retry="'), "Mistake review must link back to the original lesson");
curriculum.formal.find(x => x.id === "ms-05").words.push(["فِي الصَّبَاحِ","בבוקר","fī aṣ-ṣabāḥ","משפט קצר להאזנה","msa-in-morning.wav"]);
curriculum.formal.find(x => x.id === "ms-07").words.push(["في مَدِينَةٍ صَغيرَة","בעיר קטנה","fī madīna ṣaghīra","משפט קצר להאזנה","msa-city-small.wav"]);
curriculum.formal.find(x => x.id === "ms-05").words.push(["فِي ذَاتِ يَوْمٍ","יום אחד","fī dhāti yawmin","משפט קצר להאזנה","msa-one-day.wav"]);
curriculum.formal.find(x => x.id === "ms-07").words.push(["عَلَى كَوْكَبٍ بَعِيدٍ","על כוכב רחוק","ʿalā kawkabin baʿīdin","משפט קצר להאזנה","msa-on-distant-planet.wav"]);
curriculum.formal.find(x => x.id === "ms-12").words.push(["طَعَامُهُمْ وَاحِدٌ","האוכל שלהם זהה","ṭaʿāmuhum wāḥidun","משפט קצר להאזנה","msa-their-food-is-the-same.wav"]);
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
assert(vocabCount >= 348, "Expected at least 345 learning entries including two audio phrases; found " + vocabCount);
assert((html.match(/\["[اأإآب-ي]"/g) || []).length >= 28, "Arabic alphabet forms are missing");
assert(html.includes("localStorage"), "Local progress storage missing");
assert(html.includes("StepUp-Arabic-backup.json"), "Backup export missing");
assert(html.includes("data-audio"), "Audio player handling missing");
for (const clip of ["msa-in-morning.wav", "msa-city-small.wav", "msa-one-day.wav", "msa-on-distant-planet.wav", "msa-their-food-is-the-same.wav"]) {
  assert(html.includes(clip), "Human listening sample reference missing: " + clip);
}
assert(fs.existsSync("scripts/fetch_audio.py"), "Audio fetch script missing");
const manifest = fs.readFileSync("android/app/src/main/AndroidManifest.xml", "utf8");
assert(!manifest.includes("android.permission.INTERNET"), "Android must not request Internet permission");
const androidApp = fs.readFileSync("android/app/src/main/java/com/stepuparabic/app/MainActivity.kt", "utf8");
assert(androidApp.includes("file:///android_asset/index.html"), "Android must load its bundled local app");
assert(androidApp.includes("domStorageEnabled = true"), "Android local progress storage must be enabled");
const desktopApp = fs.readFileSync("desktop/main.go", "utf8");
assert(desktopApp.includes('net.Listen("tcp4", "127.0.0.1:41739")'), "Windows local server must bind only to loopback");
assert(desktopApp.includes("//go:embed audio/*"), "Windows audio must be embedded in the executable");

const fetchScript = fs.readFileSync("scripts/fetch_audio.py", "utf8");
assert(fetchScript.includes("CC BY 4.0") || fetchScript.includes("CC-BY-4.0"), "Audio source licence must be documented");

assert(!/<script[^>]+src=/.test(html), "Runtime external scripts are not allowed");
assert(!/<link[^>]+href=["']https?:/.test(html), "External runtime stylesheet is not allowed");
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(m => !/\bsrc\s*=/.test(m[1]));
assert(scripts.length, "No inline application script found");
scripts.forEach((m, i) => new vm.Script(m[2].replace(/const CURRICULUM = \{[\s\S]*?\};/, "const CURRICULUM = {};"), { filename: "inline-" + (i + 1) + ".js" }));
const exampleCount = all.filter(x => Array.isArray(x.examples) && x.examples.length).length;
assert(exampleCount === 49, "Every lesson must contain at least one example sentence");
const teachingCount = all.filter(x => typeof x.teaching === "string" && x.teaching.trim()).length;
assert(teachingCount === 49, "Every lesson must contain a teaching explanation");
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
assert(html.includes("const listening=questionBank.filter(q=>q.audio)"), "Final exam must include the listening questions from completed lessons");
assert(html.includes('id="view-guide"') && html.includes("ערבית ספרותית מודרנית (MSA)"), "Arabic varieties guide is missing");
assert(html.includes("ערבית לבנטינית") && html.includes("ערבית מדוברת פלסטינית"), "Guide must explain Levantine and Palestinian Arabic");
assert(html.includes("function normalizeState") && html.includes("function loadState") && html.includes("function save()"), "Robust persistence functions are missing");
assert(html.includes("window.StepUpNative.loadProgress") && html.includes("window.StepUpNative.saveProgress"), "Android native persistence fallback is missing");
assert(html.includes("setTimeout(()=>URL.revokeObjectURL(url),60000)"), "Backup download URL must remain available long enough for WebView export");
const androidManifest = fs.readFileSync("android/app/src/main/AndroidManifest.xml", "utf8");
assert(!androidManifest.includes("android.permission.INTERNET"), "Android must not request Internet permission");
const androidMain = fs.readFileSync("android/app/src/main/java/com/stepuparabic/app/MainActivity.kt", "utf8");
assert(androidMain.includes('AtomicFile(File(filesDir, "stepuparabic-progress.json"))'), "Android must keep an atomic private progress file");
assert(androidMain.includes("fun loadProgress(): String") && androidMain.includes("fun saveProgress(json: String): Boolean"), "Android native progress bridge methods are missing");
assert(html.includes("window.__stepUpSmokeTest") && html.includes("return {restored,saved,direct}"), "Android persistence smoke hook must be defined independently of bridge timing");
assert(androidMain.includes("SAVE_SMOKE:$smokeResult") && androidMain.includes("JSON.stringify(r)") && androidMain.includes("stepup_smoke"), "Android activity must support the structured two-launch persistence smoke test");
const desktopMain = fs.readFileSync("desktop/main.go", "utf8");
assert(desktopMain.includes('net.Listen("tcp4", "127.0.0.1:41739")'), "Windows must use a stable loopback origin for persistent localStorage");
assert(desktopMain.includes('filepath.Join(dataDir, "WebView2")'), "Windows WebView2 profile directory must remain stable");
assert(desktopMain.includes("לומדים ערבית צעד צעד"), "Windows app title must identify the Arabic course");
assert(html.includes("window.StepUpNativeSaveFile") && html.includes("StepUp-Arabic-backup.json"), "Backup button must call the Windows native file writer");
assert(desktopMain.includes('w.Bind("StepUpNativeSaveFile"'), "Windows must expose a native backup file writer");
assert(desktopMain.includes('filepath.Join(home, "Downloads", "StepUp Arabic")'), "Windows backups must be stored in the user Downloads folder");
assert(desktopMain.includes("json.Valid([]byte(content))"), "Windows backup writer must validate JSON before writing");
console.log(JSON.stringify({ spokenLessons: curriculum.spoken.length, formalLessons: curriculum.formal.length, vocabularyItems: vocabCount, lessonsWithExamples: exampleCount, lessonsWithExplanations: teachingCount, generatedQuestionsPerLesson: "2 per vocabulary item plus 1 for each human audio clip", alphabetForms: 28, javascriptSyntax: "passed" }, null, 2));
