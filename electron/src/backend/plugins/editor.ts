import { ipcMain } from 'electron'
import * as fsPromise from 'fs/promises'

const parcelWatcher = require('@parcel/watcher')

ipcMain.handle('watch-dir', async (event, dirPath) => {
    const fileContents = new Map()
    const listeners: any = []

    try {
        console.log('got here')
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
                            console.log(newContent)
                            if (fileContents.get(e.path) !== newContent) {
                                fileContents.set(e.path, newContent)
                                // listeners?.forEach(l => l(e.path, newContent))
                            }
                            updatedEvents.push({ ...e, newContent })
                        } catch (readErr) {
                            console.error(
                                `Error reading file ${e.path}:`,
                                readErr
                            )
                        }
                    } else {
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
