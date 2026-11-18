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
const functions = ["normalizeState", "loadState", "save"].map(extractFunction).join("\n");

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

// Malformed local data must fall back to the native save rather than resetting progress.
memory.set(key, "{broken-json");
const corruptedContext = makeContext({ localStorage: normalStorage, nativeStore: native });
assert.deepEqual(JSON.parse(JSON.stringify(corruptedContext.readState())).completed, ["ms-a1"]);
console.log("Persistence tests passed: browser save, restart restore, Android fallback and recovery from malformed local data.");
