const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync("index.html", "utf8");
function assert(ok, message) { if (!ok) throw new Error(message); }
assert(html.includes('id="view-home"'), "Missing home view");
assert(html.includes('id="view-letters"'), "Missing alphabet view");
assert(html.includes('id="view-spoken"') && html.includes('id="view-formal"'), "Both learning tracks are required");
assert((html.match(/\["[اأإآب-ي]"/g) || []).length >= 28, "Expected Arabic alphabet entries");
assert(html.includes("localStorage"), "Local progress storage is missing");
assert(html.includes("StepUp-Arabic-backup.json"), "Backup export is missing");
const scripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].filter(m => !/\bsrc\s*=/.test(m[1]));
assert(scripts.length, "No inline application script found");
scripts.forEach((m, i) => new vm.Script(m[2], { filename: "inline-" + (i + 1) + ".js" }));
console.log(JSON.stringify({ tracks: 2, prototype: "passed", javascriptSyntax: "passed" }, null, 2));
