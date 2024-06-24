import { useEffect, useState } from 'react'

import {
    getLanguageFromFilename,
    getIconFromFilename,
} from '@/lib/programming-language-utils'
import { File } from '@/lib/types'

type FileEvent = {
    type: 'create' | 'update' | 'delete'
    path: string
    newContent: string
}

const useFileWatcher = (initialFiles: File[], dirPath: string) => {
    const [files, setFiles] = useState<File[]>(initialFiles)

    useEffect(() => {
        const startWatching = async () => {
            if (!dirPath) {
                return
            }
            const success = await window.api.invoke('watch-dir', dirPath)
            if (!success) {
                console.error('Failed to start watching directory')
                return
            }

            window.api.receive(
                'file-changes',
                (events, _events: FileEvent[]) => {
                    // console.log('event', events)
                    console.log('File changes:', events)
                    const updatedFiles = [...files]
                    events.forEach((event: FileEvent) => {
                        console.log('new content', event.newContent)
                        const fileIndex = updatedFiles.findIndex(
                            file => file.path === event.path
                        )

                        if (
                            event.type === 'create' ||
                            event.type === 'update'
                        ) {
                            const file = {
                                id: event.path,
                                name:
                                    event.path.split('/').pop() ??
                                    'unnamed_file',
                                path: event.path,
                                language: getLanguageFromFilename(
                                    event.path.split('/').pop()
                                ),
                                value: { lines: event.newContent }, // You might want to read the file content here
                                icon: getIconFromFilename(
                                    event.path.split('/').pop()
                                ),
                            }

                            if (fileIndex === -1) {
                                updatedFiles.push(file)
                            } else {
                                updatedFiles[fileIndex] = file
                            }
                        } else if (
                            event.type === 'delete' &&
                            fileIndex !== -1
                        ) {
                            updatedFiles.splice(fileIndex, 1)
                        }
                    })

                    setFiles(updatedFiles)
                }
            )

            return () => {
                window.api.send('unsubscribe')
                window.api.removeAllListeners('file-changes')
            }
        }

        startWatching()
    }, [dirPath, files])

    return files
}

export default useFileWatcher
