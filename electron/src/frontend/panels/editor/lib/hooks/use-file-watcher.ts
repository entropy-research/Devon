import { useEffect, useState } from 'react'

import {
    getLanguageFromFilename,
    getIconFromFilename,
} from '@/lib/programming-language-utils'
import { File } from '@/lib/types'

type FileEvent = {
    type: 'create' | 'update' | 'delete'
    path: string
    newContent?: string
}

const useFileWatcher = (initialFiles: File[], dirPath: string) => {
    const [files, setFiles] = useState<File[]>(initialFiles)

    useEffect(() => {
        const startWatching = async () => {
            if (!dirPath) {
                return
            }
            console.log('Starting file watcher', dirPath)
            const success = await window.api.invoke('watch-dir', dirPath)
            if (!success) {
                console.error('Failed to start watching directory')
                return
            }

            window.api.receive('file-changes', (events: FileEvent[]) => {
                const updatedFiles = [...files]
                events.forEach((event: FileEvent) => {
                    const fileIndex = updatedFiles.findIndex(
                        file => file.path === event.path
                    )

                    if (event.type === 'create' || event.type === 'update') {
                        const file = {
                            id: event.path,
                            name: event.path.split('/').pop() ?? 'unnamed_file',
                            path: event.path,
                            language: getLanguageFromFilename(
                                event.path.split('/').pop()
                            ),
                            value: { lines: event.newContent || '' }, // Read new content if available
                            icon: getIconFromFilename(
                                event.path.split('/').pop()
                            ),
                        }

                        if (fileIndex === -1) {
                            updatedFiles.push(file)
                        } else {
                            updatedFiles[fileIndex] = file
                        }
                    } else if (event.type === 'delete' && fileIndex !== -1) {
                        updatedFiles.splice(fileIndex, 1)
                    }
                })

                setFiles(updatedFiles)
            })

            return () => {
                window.api.send('unsubscribe')
                window.api.removeAllListeners('file-changes')
            }
        }

        startWatching()
    }, [dirPath])

    return files
}

export default useFileWatcher
