import path from 'node:path'
import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import log from 'electron-log'
import electronUpdater from 'electron-updater'
import electronIsDev from 'electron-is-dev'
import ElectronStore from 'electron-store'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
import { Message, StoreSchema } from './types.js'
import {
  addMessageToHistory,
  getConversationHistory,
} from './electronStoreUtils.js'
import { readFile, writeFile } from 'fs/promises'
import {
  addMessage,
  getMessages,
  createOrUpdateChat,
  getChats,
  createChat,
  getChatById,
} from './database.js'
import { spawn } from 'child_process'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const { autoUpdater } = electronUpdater
let appWindow: BrowserWindow | null = null

const schema: ElectronStore.Schema<StoreSchema> = {
  conversationHistory: {
    type: 'array',
    default: [],
    items: {
      type: 'object',
      properties: {
        id: { type: 'string' },
        role: { type: 'string' },
        content: { type: 'string' },
      },
      required: ['id', 'role', 'content'],
    },
  },
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const store = new ElectronStore<StoreSchema>({ schema })

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
  // eslint-disable-next-line @typescript-eslint/no-var-requires
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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
let CHAT_DATA_PATH: string

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let serverProcess: any = null

app.on('ready', () => {
  new AppUpdater()
  serverProcess = spawn('python', ['./backend/server.py'])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  serverProcess.stdout.on('data', (data: any) => {
    console.log(`Server: ${data}`)
  })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  serverProcess.stderr.on('data', (data: any) => {
    console.error(`Server Error: ${data}`)
  })

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  serverProcess.on('close', (code: any) => {
    console.log(`Server process exited with code ${code}`)
  })
  // CHAT_DATA_PATH = path.join(app.getPath('userData'), 'store', 'chatData.json')
  // mkdir(path.dirname(CHAT_DATA_PATH), { recursive: true }).catch(console.error)
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

ipcMain.handle('sample:ping', () => {
  console.log('PONG!')
  return 'pong'
})

ipcMain.handle('ping', () => {
  console.log('PONG!')
  return 'pong'
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

// ipcMain.handle('add-message', (event, message: Message) => {
//   addMessageToHistory(store, message)
//   console.log('SUCCESS!', event, message)
//   return { success: true }
// })

ipcMain.handle('add-message', async (event, message: Message) => {
  try {
    addMessage(message.id, message.role, message.content)
    return { success: true }
  } catch (error) {
    console.error('Error adding message to database', error)
    if (error instanceof Error) {
      return { success: false, error: error.message }
    }
    return { success: false, error: 'An unknown error occurred' }
  }
})

ipcMain.handle('create-or-update-chat', async (event, chat) => {
  try {
    createOrUpdateChat(chat)
    return { success: true }
  } catch (error) {
    console.error('Error creating or updating chat in database', error)
    if (error instanceof Error) {
      return { success: false, error: error.message }
    }
    return { success: false, error: 'An unknown error occurred' }
  }
})

ipcMain.handle('get-chats', async (event, userId) => {
  try {
    const chats = getChats()
    return { success: true, data: chats }
  } catch (error) {
    console.error('Error fetching chats from database', error)
    if (error instanceof Error) {
      return { success: false, error: error.message }
    }
    return { success: false, error: 'An unknown error occurred' }
  }
})

ipcMain.handle('create-chat', async (event, chat) => {
  try {
    createChat(chat)
    return { success: true }
  } catch (error) {
    console.error('Error creating chat in database', error)
    if (error instanceof Error) {
      return { success: false, error: error.message }
    }
    return { success: false, error: 'An unknown error occurred' }
  }
})

ipcMain.handle('get-messages', async () => {
  try {
    const messages = getMessages()
    return { success: true, data: messages }
  } catch (error) {
    console.error('Error fetching messages from database', error)
    if (error instanceof Error) {
      return { success: false, error: error.message }
    }
    return { success: false, error: 'An unknown error occurred' }
  }
})

ipcMain.handle('get-conversation-history', () => {
  const history = getConversationHistory(store)
  console.log(history)
  return history
})

ipcMain.handle('get-user-data-path', () => {
  return app.getPath('userData')
})

// Function to load chat data
export async function loadChatData() {
  try {
    const data = await readFile(CHAT_DATA_PATH, 'utf8')
    return JSON.parse(data)
  } catch (error: unknown) {
    // if (error.code === 'ENOENT') {
    //   // File not found, return default empty array
    //   return []
    // } else {
    //   throw error // Rethrow unexpected errors
    // }
    console.error('Failed to read chat data:', error)
  }
}

// Function to save chat data
export async function saveChatData(chatData: unknown) {
  const data = JSON.stringify(chatData, null, 4) // Pretty print JSON
  await writeFile(CHAT_DATA_PATH, data, 'utf8')
}

ipcMain.handle('get-chat-by-id', async (event, id) => {
  try {
    const chat = getChatById(id)
    return { success: true, data: chat }
  } catch (error) {
    console.error('Error fetching chat by ID from database', error)
    if (error instanceof Error) {
      return { success: false, error: error.message }
    }
    return { success: false, error: 'An unknown error occurred' }
  }
})
