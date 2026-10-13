# rea-groundtruth

Checking what [REA](https://github.com/morluto/rea) reports against what is actually in the code.

REA is great at telling you how an app works. But when an agent builds on REA's answer, a silent miss looks exactly like "this app has no such thing." This repo runs REA on targets where the truth is known (source-available apps and tiny hand-written fixtures) and records where its output and reality disagree, with a one-command repro for each case.

Tested with `rea-agents` 6.4.0 on Windows 11 x64, Node 22.22.

## Finding 1: webpack-bundled Electron main processes come back empty

**Real app.** MongoDB Compass 1.43.4 (source-available, installed build). `rea analyze-javascript-application` on its `app.asar` finishes cleanly and reports:

| What REA reports | Value |
|---|---|
| browser_windows | 0 |
| explicit_web_preferences | 0 |
| IPC operations | 0 |
| IPC main handlers | 0 |

The shipped `build/main.js` (844 KB, webpack 5) contains `new s.BrowserWindow(...)`, 8 `ipcMain` references, and a window created with `contextIsolation:false` and `enableRemoteModule:true`. So REA did not just miss plumbing. It also missed a security-relevant window configuration.

**Why.** Webpack does not call `require("electron")` where Electron is used. It puts the call in a module-registry entry and hands the result around:

```js
var m = {45840: e => { e.exports = require("electron") }};
const s = n(45840);           // or: a = n.n(n(45840)); a().ipcMain
new s.BrowserWindow({...});
```

REA follows direct requires and lexical aliases. It does not follow the registry lookup `n(45840)`, so every Electron API reached through it is invisible.

**Minimal repro.** The same app is written four ways in [`repro/webpack-electron`](repro/webpack-electron): one window, one `ipcMain.handle("get-connections")`.

```
python scripts/run_repro.py
```

```
variant     windows  handlers  channels  verdict
plain             1         1         1  ok
namespace         1         1         1  ok
webpack           0         0         0  MISSED
interop           0         0         0  MISSED

truth:            1         1         1
```

`plain` and `namespace` (the form fixed in morluto/rea#1802) pass. Both webpack shapes, the direct registry call and the `n.n()` default-interop helper, report nothing. The result's only related caveat is a generic "missing findings do not establish absence" note. Nothing points at the unresolved registry lookup.

**Why it matters.** Most production Electron apps ship a webpack or similar bundled main process. On those apps, an agent asking REA "what IPC does the renderer reach?" or "are any windows created without context isolation?" currently gets a confident-looking zero.

## Finding 2: installed Windows apps are rejected by default

Running REA on the installed Compass `app.asar` fails with `artifact_integrity_mismatch`. A native `.node` file in `app.asar.unpacked` doesn't match the hash declared in the archive, because Windows release pipelines code-sign native binaries after packing. REA's error message explains this and names the fix (`--integrity-policy record-and-continue`), which then works. This is documented behavior, not a bug. Still, expect it on most signed Windows Electron apps: Compass had 14 such contradictions.

## Layout

```
repro/webpack-electron/   four variants of the same tiny Electron app
scripts/run_repro.py      runs REA on each and diffs against the known truth
```

Nothing from Compass is redistributed here. Findings about it cite only counts and short identifiers.

## Contributing

Know an app whose source you can check REA's output against? Add a fixture or a case with the truth spelled out, and the command that shows the gap.

## License

MIT
