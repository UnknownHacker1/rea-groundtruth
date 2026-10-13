const s = require("electron");
s.app.whenReady().then(() => { const w = new s.BrowserWindow({ webPreferences: { contextIsolation: false } }); w.loadFile("index.html"); });
s.ipcMain.handle("get-connections", async () => []);
