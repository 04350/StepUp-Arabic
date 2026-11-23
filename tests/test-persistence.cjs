const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");

const html = fs.readFileSync("index.html", "utf8");
function extractFunction(name) {
  const start = html.indexOf("function " + name + "(");
  assert(start >= 0, "Missing function: " + name);
  const next = html.indexOf("\nfunction ", start + 1);
  return html.slice(start, next >= 0 ? next : html.indexOf("</script>", start));
}
const key = html.match(/const KEY="([^"]+)"/)?.[1];
const emptyText = html.match(/const EMPTY=(\{[^\n]+\});/)?.[1];
assert(key && emptyText, "Storage key or empty state is missing");
const empty = vm.runInNewContext("(" + emptyText + ")");
const curriculumMatch = html.match(/const CURRICULUM = (\\{[\\s\\S]*?\\});[\\s\\S]*?const LETTERS=/);
assert(curriculumMatch, "Curriculum is required for backup validation tests");
const curriculum = JSON.parse(curriculumMatch[1]);
const allLessons = [
  ...curriculum.spoken.map(lesson => ({ ...lesson, track: "spoken" })),
  ...curriculum.formal.map(lesson => ({ ...lesson, track: "formal" }))
];
const functions = ["normalizeState", "loadState", "save", "createBackupPayload", "validateBackupState", "restoreBackupPayload"].map(extractFunction).join("\\n");

function makeContext({ localStorage, nativeStore }) {
  const window = {
    StepUpNative: {
      loadProgress() { return nativeStore.value || ""; },
      saveProgress(json) { nativeStore.value = json; nativeStore.writes++; return true; }
    }
  };
  const context = {
    JSON, Date, Number, Array, Object, console,
    window,
    localStorage,
    updateStats() {},
    $() { return { textContent: "" }; }
  };
  vm.createContext(context);
  vm.runInContext(
    "const KEY=" + JSON.stringify(key) + ";\n" +
    "const EMPTY=" + JSON.stringify(empty) + ";\n" +
    "const ALL_LESSONS=" + JSON.stringify(allLessons) + ";\n" +
    functions + "\n" +
    "let state=loadState();\n" +
    "globalThis.readState=()=>state;\n" +
    "globalThis.writeState=x=>{state=x;};",
    context
  );
  return context;
}

const memory = new Map();
const native = { value: "", writes: 0 };
const normalStorage = {
  getItem(k) { return memory.has(k) ? memory.get(k) : null; },
  setItem(k, v) { memory.set(k, String(v)); }
};
const browserContext = makeContext({ localStorage: normalStorage, nativeStore: native });
const current = JSON.parse(JSON.stringify(browserContext.readState()));
assert.equal(current.preferences.activeTrack, "formal", "Default track should be formal");
current.completed.push("ms-a1");
current.preferences.activeTrack = "spoken";
current.scores["ms-a1"] = 90;
current.favorites = ["sp-01|مَرْحَبَا"];
current.reviewStats = {"sp-01|مَرْحَبَا": {repetitions: 2, intervalDays: 3, lastReviewedAt: "2026-11-23T10:00:00.000Z", dueAt: 1795773600000}};
current.preferences.theme = "dark";
current.preferences.dailyGoal = 15;
current.preferences.audioSpeed = 0.75;
current.preferences.arabicFontSize = 1.3;
current.finalExams.push({at:"2026-11-18T12:00:00.000Z",score:90,correct:9,total:10,lessons:["ms-a1"]});
browserContext.writeState(current);
assert.equal(browserContext.save(), true, "Save should succeed in browser storage");
assert.ok(memory.has(key), "Browser localStorage should contain saved state");
assert.ok(native.value, "Native backup should also receive saved state");
assert.equal(native.writes, 1, "Native progress file should be written on save");

const reloadedContext = makeContext({ localStorage: normalStorage, nativeStore: native });
const reloaded = JSON.parse(JSON.stringify(reloadedContext.readState()));
assert.deepEqual(reloaded.completed, ["ms-a1"], "Completed lessons should survive restart");
assert.equal(reloaded.preferences.activeTrack, "spoken", "Selected learning track should survive restart");
assert.equal(reloaded.scores["ms-a1"], 90, "Lesson score should survive restart");
assert.deepEqual(reloaded.favorites, ["sp-01|مَرْحَبَا"], "Favorite words should survive restart");
assert.equal(reloaded.reviewStats["sp-01|مَرْحَبَا"].repetitions, 2, "Spaced repetition schedule should survive restart");
assert.equal(reloaded.preferences.theme, "dark", "Theme preference should survive restart");
assert.equal(reloaded.preferences.dailyGoal, 15, "Daily learning goal should survive restart");
assert.equal(reloaded.preferences.audioSpeed, 0.75, "Audio speed should survive restart");
assert.equal(reloaded.preferences.arabicFontSize, 1.3, "Arabic font size should survive restart");
assert.equal(reloaded.finalExams[0].score,90,"Final exam history should survive restart");
const exported = browserContext.createBackupPayload();
assert.equal(exported.app, "StepUp Arabic", "Backup must identify its application");
assert.equal(exported.schema, 2, "Backup must have a supported schema version");
assert.ok(exported.exportedAt, "Backup must include an export timestamp");
assert.equal(exported.state.finalExams[0].score,90,"Backup must include final exam results");
assert.deepEqual(JSON.parse(JSON.stringify(exported.state.completed)), ["ms-a1"]);
const restoredPayload = browserContext.restoreBackupPayload(JSON.parse(JSON.stringify(exported)));
assert.deepEqual(JSON.parse(JSON.stringify(restoredPayload.completed)), ["ms-a1"], "Versioned backup should restore completed lessons");
const legacyPayload = browserContext.restoreBackupPayload({ completed: ["ms-a1"], scores: { "ms-a1": 90 }, mistakes: {}, preferences: { activeTrack: "spoken" } });
assert.deepEqual(JSON.parse(JSON.stringify(legacyPayload.completed)), ["ms-a1"], "Legacy unwrapped backup should restore");
assert.equal(legacyPayload.preferences.arabicFontSize, 1, "Legacy backups should receive the default Arabic font size");
assert.throws(() => browserContext.restoreBackupPayload({ app: "Different App", schema: 2, state: {} }), /אינו גיבוי/);
assert.throws(() => browserContext.restoreBackupPayload({ app: "StepUp Arabic", schema: 99, state: {} }), /גרסת הגיבוי/);
assert.throws(() => browserContext.restoreBackupPayload({ app: "StepUp Arabic", schema: 2, state: [] }), /מבנה הגיבוי/);
assert.throws(() => browserContext.restoreBackupPayload({ app: "StepUp Arabic", schema: 2 }), /מבנה הגיבוי/);

const validEnvelope = JSON.parse(JSON.stringify(browserContext.createBackupPayload()));
const badCompleted = JSON.parse(JSON.stringify(validEnvelope));
badCompleted.state.completed = ["lesson-does-not-exist"];
assert.throws(() => browserContext.restoreBackupPayload(badCompleted), /מזהה שיעור לא מוכר/);
const badScores = JSON.parse(JSON.stringify(validEnvelope));
badScores.state.scores = {"ms-a1": 140};
assert.throws(() => browserContext.restoreBackupPayload(badScores), /ציון לא תקין/);
const badFavorites = JSON.parse(JSON.stringify(validEnvelope));
badFavorites.state.favorites = ["not-a-real-lesson|word"];
assert.throws(() => browserContext.restoreBackupPayload(badFavorites), /מועדף שאינו קיים/);
const missingRequired = JSON.parse(JSON.stringify(validEnvelope));
delete missingRequired.state.reviewStats;
assert.throws(() => browserContext.restoreBackupPayload(missingRequired), /חסר שדה חובה/);

assert.throws(() => browserContext.restoreBackupPayload(null), /מבנה הגיבוי/);

// If WebView localStorage is unavailable, Android's private progress file is the fallback.
const brokenStorage = {
  getItem() { throw new Error("storage unavailable"); },
  setItem() { throw new Error("storage unavailable"); }
};
const nativeFallback = { value: native.value, writes: 0 };
const androidContext = makeContext({ localStorage: brokenStorage, nativeStore: nativeFallback });
const fallbackState = JSON.parse(JSON.stringify(androidContext.readState()));
assert.deepEqual(fallbackState.completed, ["ms-a1"], "Android native save should recover completed lessons");
assert.equal(fallbackState.preferences.activeTrack, "spoken", "Android native save should recover selected track");
fallbackState.answered = 12;
androidContext.writeState(fallbackState);
assert.equal(androidContext.save(), true, "Native-only save should succeed");
assert.equal(JSON.parse(nativeFallback.value).answered, 12, "Native progress file should be updated");

// When both stores contain valid data, load the newer Android atomic save.
const stale = { ...empty, completed: [], lastSavedAt: "2025-01-01T00:00:00.000Z" };
const fresh = { ...empty, completed: ["ms-a1"], preferences: { activeTrack: "spoken" }, lastSavedAt: "2026-11-18T13:00:00.000Z" };
memory.set(key, JSON.stringify(stale));
const newerNative = { value: JSON.stringify(fresh), writes: 0 };
const newestContext = makeContext({ localStorage: normalStorage, nativeStore: newerNative });
assert.deepEqual(JSON.parse(JSON.stringify(newestContext.readState())).completed, ["ms-a1"], "The most recent valid save should win");

// Malformed local data must fall back to the native save rather than resetting progress.
memory.set(key, "{broken-json");
const corruptedContext = makeContext({ localStorage: normalStorage, nativeStore: native });
assert.deepEqual(JSON.parse(JSON.stringify(corruptedContext.readState())).completed, ["ms-a1"]);

// Full cross-platform backup interchange: Android -> Windows -> Android.
const androidOnlyStore = { value: "", writes: 0 };
const androidOnlyContext = makeContext({ localStorage: brokenStorage, nativeStore: androidOnlyStore });
const androidProgress = JSON.parse(JSON.stringify(androidOnlyContext.readState()));
androidProgress.completed = ["ms-a1", "sp-01"];
androidProgress.scores = {"ms-a1": 95};
androidProgress.favorites = ["sp-01|مَرْحَبَا"];
androidProgress.reviewStats = {"sp-01|مَرْحَبَا": {repetitions: 3, intervalDays: 7, lastReviewedAt: "2026-11-23T10:00:00.000Z", dueAt: 1795773600000}};
androidProgress.preferences.activeTrack = "spoken";
androidProgress.preferences.theme = "dark";
androidProgress.preferences.dailyGoal = 20;
androidProgress.preferences.audioSpeed = 0.75;
androidProgress.preferences.arabicFontSize = 1.5;
androidOnlyContext.writeState(androidProgress);
assert.equal(androidOnlyContext.save(), true, "Android source device should save native progress");
const androidBackup = androidOnlyContext.createBackupPayload();

const windowsMemory = new Map();
const windowsStorage = {
  getItem(k) { return windowsMemory.has(k) ? windowsMemory.get(k) : null; },
  setItem(k, v) { windowsMemory.set(k, String(v)); }
};
const windowsNative = { value: "", writes: 0 };
const windowsContext = makeContext({ localStorage: windowsStorage, nativeStore: windowsNative });
const fromAndroid = windowsContext.restoreBackupPayload(JSON.parse(JSON.stringify(androidBackup)));
windowsContext.writeState(fromAndroid);
assert.equal(windowsContext.save(), true, "Windows should import and save the Android backup");
const windowsReload = makeContext({ localStorage: windowsStorage, nativeStore: windowsNative });
const windowsState = JSON.parse(JSON.stringify(windowsReload.readState()));
assert.deepEqual(windowsState.completed, ["ms-a1", "sp-01"], "Android progress should transfer to Windows");
assert.deepEqual(windowsState.favorites, ["sp-01|مَرْحَبَا"], "Favorites should transfer to Windows");
assert.equal(windowsState.reviewStats["sp-01|مَرْحَبَا"].intervalDays, 7, "Review schedule should transfer to Windows");
assert.equal(windowsState.preferences.arabicFontSize, 1.5, "Arabic font setting should transfer to Windows");

const windowsBackup = windowsReload.createBackupPayload();
const androidTargetStore = { value: "", writes: 0 };
const androidTarget = makeContext({ localStorage: brokenStorage, nativeStore: androidTargetStore });
const fromWindows = androidTarget.restoreBackupPayload(JSON.parse(JSON.stringify(windowsBackup)));
androidTarget.writeState(fromWindows);
assert.equal(androidTarget.save(), true, "Android should import and save the Windows backup");
const androidTargetReload = makeContext({ localStorage: brokenStorage, nativeStore: androidTargetStore });
const androidRestored = JSON.parse(JSON.stringify(androidTargetReload.readState()));
assert.deepEqual(androidRestored.completed, ["ms-a1", "sp-01"], "Windows progress should transfer back to Android");
assert.equal(androidRestored.scores["ms-a1"], 95, "Exam scores should survive two-way transfer");
assert.equal(androidRestored.preferences.audioSpeed, 0.75, "Audio settings should survive two-way transfer");
assert.equal(androidRestored.preferences.theme, "dark", "Theme should survive two-way transfer");

console.log("Persistence tests passed: save/restore, corrupt data recovery, schema validation and Android <-> Windows backup interchange.");
