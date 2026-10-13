const { app, BrowserWindow, ipcMain } = require("electron");
app.whenReady().then(() => {
  const win = new BrowserWindow({ webPreferences: { contextIsolation: false, nodeIntegration: true } });
  win.loadFile("index.html");
});
ipcMain.handle("get-connections", async () => []);
