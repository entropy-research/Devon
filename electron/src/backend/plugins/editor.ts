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


// File Watcher
// We care about two things
// 1. Content of open files in the editore
// 2. File tree

// Both of these should update when their contents change, we can use Parcel to watch for changes.

type File = {
    path: string
    content?: string
}

type FileEvent = {
    type: string
    path: string
}

type Path = string

class EditorFileManager {
    private files: Set<Path>
    private openFiles: Map<Path, File>

    constructor() {
        this.files = new Set()
        this.openFiles = new Map()
    }

    async addOpenFile(filename: string) {
        const content = await fsPromise.readFile(filename, 'utf8')
        this.openFiles.set(filename, { path: filename, content })
    }

    handleEvent(changedFiles: FileEvent[]) {
        changedFiles.forEach((file: {
            type: string
            path: string
        }) => {
            console.log("changed file", file)

            let changed = false

            if (file.type === 'create') {
                this.files.add(file.path)
                changed = true
            }
            else if (file.type === 'delete') {
                this.files.delete(file.path)
                changed = true
            }

            if (this.openFiles.has(file.path)) {
                if (file.type === 'update') {
                    fsPromise.readFile(file.path, 'utf8')
                        .then(content => {
                            this.openFiles.set(file.path, { path: file.path, content: content })
                        })
                        .catch(err => {
                            console.error(`Error reading file ${file.path}:`, err)
                        })
                    changed = true
                }
                else if (file.type === 'create') {
                    this.addOpenFile(file.path)
                    changed = true
                }
                else if (file.type === 'delete') {
                    if (this.openFiles.has(file.path)) {
                        this.openFiles.delete(file.path)
                    }
                    changed = true
                }
            }
        })
        return {
            files: Array.from(this.files),
            openFiles: Array.from(this.openFiles.values()),
        }
    }

}

let editorFileManager = new EditorFileManager()


ipcMain.handle('editor-add-open-file', async (event, filename) => { 
    await editorFileManager.addOpenFile(filename)
    console.log("added open file", filename)
    let state = editorFileManager.handleEvent([])
    console.log("state", state)
    event.sender.send('editor-file-changed', state)
})


ipcMain.handle('watch-dir', async (event, dirPath) => {
    // const fileContents : string[]= [];
    editorFileManager = new EditorFileManager()

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
                    // const content = await fsPromise.readFile(filePath, 'utf8')
                    // fileContents.push(filePath)
                    fileEvents.push({
                        type: 'create',
                        path: filePath,
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
        let state = editorFileManager.handleEvent(initialEvents)
        // Give some time for event listener to establish
        setTimeout(() => {
            console.log("initial state", state)
            event.sender.send('editor-file-changed', state)
        }, 1000)

        let timeoutId: NodeJS.Timeout | null = null

        const subscription = await parcelWatcher.subscribe(
            dirPath,
            async (err: any, events: any) => {
                if (err) {
                    console.error('Error watching files:', err)
                    return
                }

                const updatedEvents: FileEvent[] = []
                for (const e of events) {
                    if (shouldIgnoreFile(e.path)) {
                        continue
                    }

                    updatedEvents.push(e)

                    // if (e.type === 'update') {
                    //     try {
                    //         const newContent = await fsPromise.readFile(
                    //             e.path,
                    //             'utf8'
                    //         )
                    //         if (fileContents.get(e.path) !== newContent) {
                    //             fileContents.push(e.path)
                    //             updatedEvents.push({ ...e, newContent })
                    //         }
                    //     } catch (readErr) {
                    //         console.error(
                    //             `Error reading file ${e.path}:`,
                    //             readErr
                    //         )
                    //     }
                    // } else if (e.type === 'create' || e.type === 'delete') {
                    //     updatedEvents.push(e)
                    // }
                }

                // Debounce the event sending
                if (timeoutId) {
                    clearTimeout(timeoutId)
                }
                timeoutId = setTimeout(() => {
                    state = editorFileManager.handleEvent(updatedEvents)
                    event.sender.send('editor-file-changed', state)
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
