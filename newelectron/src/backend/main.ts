/* eslint-disable import/no-named-as-default-member */
import { app, BrowserWindow, dialog, ipcMain, safeStorage } from 'electron';
import path from 'path';
import { ChildProcess, execFile } from 'child_process'
import portfinder from 'portfinder'
import fs from 'fs'

function writeToLogFile(logMessage: string) {
  const logFilePath = path.join("/Users/mihirchintawar/", 'app.log');
  const timestamp = new Date().toISOString();
  const formattedMessage = `${timestamp} - ${logMessage}\n`;

  fs.appendFileSync(logFilePath, formattedMessage);
}



// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

let serverProcess: ChildProcess
portfinder.setBasePort(10000)
let use_port = NaN
const spawnAppWindow = async () => {

  const db_path = path.join(app.getPath('userData'), 'devon_environment.sqlite')

  await portfinder
  .getPortPromise()
  .then((port: number) => {
    use_port = port
    process.resourcesPath 
    let agent_path = path.join(__dirname, "devon_agent")
    if (fs.existsSync(path.join(process.resourcesPath, "devon_agent"))) {
      agent_path = path.join(process.resourcesPath, "devon_agent")
    }
    fs.chmodSync(agent_path, '755');

    serverProcess = execFile(
      agent_path,
      [
        'server',
        '--port',
        port.toString(),
        '--db_path',
        db_path,
        // '--model',
        // modelName as string,
        // '--api_key',
        // api_key as string,
        // '--api_base',
        // api_base as string,
        // '--prompt_type',
        // prompt_type as string,
      ],
      {
        signal: controller.signal,
      }
    )

    serverProcess.stdout?.on('data', (data: unknown) => {
      writeToLogFile(`Server: ${data}`)
      console.log(`Server: ${data}`)
    })

    serverProcess.stderr?.on('data', (data: unknown) => {
      writeToLogFile(`Server Error: ${data}`)
      console.error(`Server Error: ${data}`)
    })

    serverProcess.on('close', (code: unknown) => {
      console.log(`Server process exited with code ${code}`)
    })
  })
  .catch(error => {
    writeToLogFile(`Failed to find a free port: ${error}`)
    console.error('Failed to find a free port:', error)
    return { success: false, message: 'Failed to find a free port.' }
  })

// const RESOURCES_PATH = electronIsDev
//   ? path.join(__dirname, '../../assets')
//   : path.join(process.resourcesPath, 'assets')

// const getAssetPath = (...paths: string[]): string => {
//   return path.join(RESOURCES_PATH, ...paths)
// }

const PRELOAD_PATH = path.join(__dirname, 'preload.js')

let appWindow = new BrowserWindow({
  width: 800,
  height: 600,
  titleBarStyle: 'hidden',
  trafficLightPosition: { x: 15, y: 10 },
  // icon: getAssetPath('icon.png'),
  show: false,
  webPreferences: {
    preload: PRELOAD_PATH,
    contextIsolation: true,
    nodeIntegration: false,
    additionalArguments: [`--port=${use_port}`],
  },
})

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    appWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    appWindow.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  }

// appWindow.loadURL(
//   electronIsDev
//     ? `http://localhost:3000?port=${use_port}`
//     : `file://${path.join(__dirname, '../../frontend/build/index.html')}`
// )
appWindow.maximize()
appWindow.setMenu(null)
appWindow.show()
appWindow.webContents.openDevTools()
appWindow.on('closed', () => {
  appWindow = null
})
}

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  }

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
};
const controller = new AbortController()

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', ()=>{
  // For safeStorage of secrets
  if (safeStorage.isEncryptionAvailable()) {
    console.log('Encryption is available and can be used.')
  } else {
    console.log(
      'Encryption is not available. Fallback mechanisms might be required.'
    )
  }

  spawnAppWindow()

});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  // if (process.platform !== 'darwin') {
    app.quit();
  // }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});



app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (serverProcess.pid) {
    console.log('Killing server process with pid', serverProcess.pid)
    process.kill(serverProcess.pid, 'SIGTERM');
  }
  serverProcess.kill() // Make sure to kill the server process when the app is closing

  if (serverProcess.killed) {
    console.log('Server process was successfully killed.');
  } else {
    console.log('Failed to kill the server process.');
  }
})

/*
 * ======================================================================================
 *                                IPC Main Events
 * ======================================================================================
 */

ipcMain.handle('ping', () => {
  console.log('PONG!')
  return 'pong'
})

ipcMain.on('get-port', event => {
  event.reply('get-port-response', use_port)
})

ipcMain.on('get-file-path', event => {
  dialog
    .showOpenDialog({
      properties: ['openDirectory'],
    })
    .then(result => {
      if (!result.canceled && result.filePaths.length > 0) {
        event.reply('file-path-response', result.filePaths[0])
      } else {
        event.reply('file-path-response', 'cancelled')
      }
    })
    .catch(err => {
      console.error('Failed to open dialog:', err)
      event.reply('file-path-response', 'error')
    })
})

// IPC handlers for encrypting and decrypting data
ipcMain.handle('encrypt-data', async (event, plainText) => {
  try {
    const encrypted = safeStorage.encryptString(plainText)
    return encrypted.toString('hex') // send as string to render process
  } catch (error) {
    console.error('Encryption failed:', error)
    throw error
  }
})

ipcMain.handle('decrypt-data', async (event, encryptedHex) => {
  try {
    const encryptedBuffer = Buffer.from(encryptedHex, 'hex')
    const decrypted = safeStorage.decryptString(encryptedBuffer)
    return decrypted
  } catch (error) {
    console.error('Decryption failed:', error)
    throw error
  }
})

ipcMain.handle('save-data', async (event, plainText) => {
  if (safeStorage.isEncryptionAvailable()) {
    const encrypted = safeStorage.encryptString(plainText)
    const filePath = path.join(app.getPath('userData'), 'secureData.bin')
    if (!fs.existsSync(filePath)) {
      fs.writeFileSync(filePath, '');
    }
    try {
      fs.writeFileSync(filePath, encrypted)
      return { success: true }
    } catch (error) {
      console.error('Failed to save encrypted data:', error)
      return { success: false, message: 'Failed to save encrypted data' }
    }
  } else {
    return { success: false, message: 'Encryption not available' }
  }
})

ipcMain.handle('load-data', async () => {
  const filePath = path.join(app.getPath('userData'), 'secureData.bin')
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, '');
  }
  console.log("filePath", filePath)
  try {
    const encryptedData = fs.readFileSync(filePath)
    if (safeStorage.isEncryptionAvailable()) {
      const decrypted = safeStorage.decryptString(encryptedData)
      return { success: true, data: decrypted }
    } else {
      return { success: false, message: 'Decryption not available' }
    }
  } catch (error) {
    console.error('Failed to read encrypted data:', error)
    return { success: false, message: 'Failed to read encrypted data' }
  }
})

ipcMain.handle('check-has-encrypted-data', async () => {
  const filePath = path.join(app.getPath('userData'), 'secureData.bin')
  try {
    await fs.promises.access(filePath, fs.constants.F_OK)
    if (safeStorage.isEncryptionAvailable()) {
      return { success: true }
    } else {
      return { success: false, message: 'Data not available' }
    }
  } catch (error) {
    // This just means the file doesn't exist
    // console.error('Failed to get encrypted data:', error)
    return { success: false, message: 'Failed to get encrypted data' }
  }
})

ipcMain.handle('delete-encrypted-data', async () => {
  const filePath = path.join(app.getPath('userData'), 'secureData.bin')
  try {
    // Check if file exists before attempting to delete
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath) // Delete the file
      return { success: true, message: 'Encrypted data deleted successfully.' }
    } else {
      return { success: false, message: 'File does not exist.' }
    }
  } catch (error) {
    console.error('Failed to delete encrypted data:', error)
    return { success: false, message: 'Failed to delete encrypted data.' }
  }
})


// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
