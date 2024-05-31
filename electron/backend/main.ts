import path from 'node:path'
import fs from 'fs'
import { app, BrowserWindow, ipcMain, dialog, safeStorage } from 'electron'
import log from 'electron-log'
import electronUpdater from 'electron-updater'
import electronIsDev from 'electron-is-dev'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import { ChildProcessWithoutNullStreams, spawn } from 'child_process'
import portfinder from 'portfinder'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const { autoUpdater } = electronUpdater
let appWindow: BrowserWindow | null = null

process.on('uncaughtException', error => {
  console.error('Uncaught Exception:', error)
})
process.on('unhandledRejection', reason => {
  console.error('Unhandled Rejection:', reason)
})

class AppUpdater {
  constructor() {
    log.transports.file.level = 'info'
    autoUpdater.logger = log
    autoUpdater.checkForUpdatesAndNotify()
  }
}

if (electronIsDev) {
  const { default: electronDebug } = await import('electron-debug')
  electronDebug({
    showDevTools: true,
    devToolsMode: 'right',
  })
}

const installExtensions = async () => {
  /**
   * NOTE:
   * As of writing this comment, Electron does not support the `scripting` API,
   * which causes errors in the REACT_DEVELOPER_TOOLS extension.
   * A possible workaround could be to downgrade the extension but you're on your own with that.
   */
  /*
	const {
		default: electronDevtoolsInstaller,
		//REACT_DEVELOPER_TOOLS,
		REDUX_DEVTOOLS,
	} = await import('electron-devtools-installer')
	// @ts-expect-error Weird behaviour
	electronDevtoolsInstaller.default([REDUX_DEVTOOLS]).catch(console.log)
	*/
}

const spawnAppWindow = async () => {
  if (electronIsDev) await installExtensions()

  const RESOURCES_PATH = electronIsDev
    ? path.join(__dirname, '../../assets')
    : path.join(process.resourcesPath, 'assets')

  const getAssetPath = (...paths: string[]): string => {
    return path.join(RESOURCES_PATH, ...paths)
  }

  const PRELOAD_PATH = path.join(__dirname, 'preload.js')

  appWindow = new BrowserWindow({
    width: 800,
    height: 600,
    titleBarStyle: 'hidden',
    trafficLightPosition: { x: 15, y: 10 },
    icon: getAssetPath('icon.png'),
    show: false,
    webPreferences: {
      preload: PRELOAD_PATH,
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  appWindow.loadURL(
    electronIsDev
      ? 'http://localhost:3000'
      : `file://${path.join(__dirname, '../../frontend/build/index.html')}`
  )
  appWindow.maximize()
  appWindow.setMenu(null)
  appWindow.show()
  appWindow.on('closed', () => {
    appWindow = null
  })
}

let serverProcess: ChildProcessWithoutNullStreams

const controller = new AbortController()

app.on('ready', () => {
  new AppUpdater()

  // For safeStorage of secrets
  if (safeStorage.isEncryptionAvailable()) {
    console.log('Encryption is available and can be used.')
  } else {
    console.log(
      'Encryption is not available. Fallback mechanisms might be required.'
    )
  }

  spawnAppWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  serverProcess.kill() // Make sure to kill the server process when the app is closing
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

portfinder.setBasePort(10001)
ipcMain.handle('spawn-devon-agent', async () => {
  try {
    portfinder
      .getPortPromise()
      .then((port: number) => {
        serverProcess = spawn('devon', ['server', '--port', port.toString()], {
          signal: controller.signal,
        })

        serverProcess.stdout.on('data', (data: unknown) => {
          console.log(`Server: ${data}`)
        })

        if (appWindow) {
          appWindow.webContents.send('server-port', port)
        }

        serverProcess.stderr.on('data', (data: unknown) => {
          console.error(`Server Error: ${data}`)
        })

        serverProcess.on('close', (code: unknown) => {
          console.log(`Server process exited with code ${code}`)
        })
      })
      .catch(error => {
        console.error('Failed to find a free port:', error)
        return { success: false, message: 'Failed to find a free port.' }
      })
    return { success: true }
  } catch (error) {
    console.error('Failed to spawn Python agent:', error)
    return { success: false, message: 'Failed to spawn Python agent.' }
  }
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
