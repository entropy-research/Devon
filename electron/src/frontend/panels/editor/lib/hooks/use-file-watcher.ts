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
                return () => {}
            }

            const success = await window.api.invoke('watch-dir', dirPath)
            if (!success) {
                console.error('Failed to start watching directory')
                return () => {}
            }

            const handleFileChanges = (events: FileEvent[]) => {
                setFiles(prevFiles => {
                    const fileMap = new Map(
                        prevFiles.map(file => [file.path, file])
                    )

                    events.forEach((event: FileEvent) => {
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
                                value: { lines: event.newContent || '' }, // Read new content if available
                                icon: getIconFromFilename(
                                    event.path.split('/').pop()
                                ),
                            }
                            fileMap.set(event.path, file)
                        } else if (event.type === 'delete') {
                            fileMap.delete(event.path)
                        }
                    })

                    return Array.from(fileMap.values())
                })
            }

            window.api.receive('file-changes', handleFileChanges)

            return () => {
                window.api.send('unsubscribe')
                window.api.removeAllListeners('file-changes')
            }
        }

        let cleanup: () => void

        startWatching().then(cleanupFn => {
            cleanup = cleanupFn
        })

        return () => {
            if (cleanup) {
                cleanup()
            }
            setFiles([])
        }
    }, [dirPath])

    return files
}

export default useFileWatcher
