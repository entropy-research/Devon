import { ipcMain } from 'electron'
import * as fsPromise from 'fs/promises'
import path from 'path'

const parcelWatcher = require('@parcel/watcher')

ipcMain.handle('watch-dir', async (event, dirPath) => {
    const fileContents = new Map()

    const readDirectory = async (dir: string): Promise<any> => {
        const files = await fsPromise.readdir(dir, { withFileTypes: true })
        const fileEvents = []

        for (const file of files) {
            const filePath = path.join(dir, file.name)
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

        const subscription = await parcelWatcher.subscribe(
            dirPath,
            async (err: any, events: any) => {
                if (err) {
                    console.error('Error watching files:', err)
                    return
                }

                const updatedEvents = []
                for (const e of events) {
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
                event.sender.send('file-changes', updatedEvents)
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
