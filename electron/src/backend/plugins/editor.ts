import { ipcMain } from 'electron'
import * as fsPromise from 'fs/promises'
import path from 'path'

const parcelWatcher = require('@parcel/watcher')

const IGNORE_PATTERNS = [
    '.DS_Store',
    '._*',
    '.AppleDouble',
    'Thumbs.db',
    'desktop.ini',
    '.*.swp',
    '.*.swo',
    '.*~',
    '*.tmp',
    'node_modules',
    '.git',
    '__pycache__',
]

const shouldIgnoreFile = (filePath: string): boolean => {
    return IGNORE_PATTERNS.some(pattern => {
        const regex = new RegExp(
            pattern.replace(/\./g, '\\.').replace(/\*/g, '.*')
        )
        return regex.test(filePath)
    })
}

ipcMain.handle('watch-dir', async (event, dirPath) => {
    const fileContents = new Map()

    const readDirectory = async (dir: string): Promise<any> => {
        const files = await fsPromise.readdir(dir, { withFileTypes: true })
        const fileEvents = []

        for (const file of files) {
            const filePath = path.join(dir, file.name)
            if (shouldIgnoreFile(filePath)) {
                continue
            }

            if (file.isDirectory()) {
                fileEvents.push(...(await readDirectory(filePath)))
            } else {
                try {
                    const content = await fsPromise.readFile(filePath, 'utf8')
                    fileContents.set(filePath, content)
                    fileEvents.push({
                        type: 'create',
                        path: filePath,
                        newContent: content,
                    })
                } catch (err) {
                    console.error(`Error reading file ${filePath}:`, err)
                }
            }
        }

        return fileEvents
    }

    try {
        // Initial read of the directory
        const initialEvents = await readDirectory(dirPath)

        // Give some time for event listener to establish
        setTimeout(() => {
            event.sender.send('file-changes', initialEvents)
        }, 1000)

        let timeoutId: NodeJS.Timeout | null = null

        const subscription = await parcelWatcher.subscribe(
            dirPath,
            async (err: any, events: any) => {
                if (err) {
                    console.error('Error watching files:', err)
                    return
                }

                const updatedEvents = []
                for (const e of events) {
                    if (shouldIgnoreFile(e.path)) {
                        continue
                    }

                    if (e.type === 'update') {
                        try {
                            const newContent = await fsPromise.readFile(
                                e.path,
                                'utf8'
                            )
                            if (fileContents.get(e.path) !== newContent) {
                                fileContents.set(e.path, newContent)
                                updatedEvents.push({ ...e, newContent })
                            }
                        } catch (readErr) {
                            console.error(
                                `Error reading file ${e.path}:`,
                                readErr
                            )
                        }
                    } else if (e.type === 'create' || e.type === 'delete') {
                        updatedEvents.push(e)
                    }
                }

                // Debounce the event sending
                if (timeoutId) {
                    clearTimeout(timeoutId)
                }
                timeoutId = setTimeout(() => {
                    event.sender.send('file-changes', updatedEvents)
                }, 500) // Adjust debounce timing as needed
            }
        )

        // Listen for the unsubscribe event from the renderer process
        ipcMain.once('unsubscribe', () => {
            if (subscription) {
                subscription.unsubscribe()
            }
        })

        return true
    } catch (error) {
        console.error('Failed to watch directory:', error)
        return false
    }
})
