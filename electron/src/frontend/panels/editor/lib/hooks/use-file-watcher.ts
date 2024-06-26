import { useEffect, useState } from 'react'
import {
    getLanguageFromFilename,
    getIconFromFilename,
} from '@/lib/programming-language-utils'
import { File } from '@/lib/types'

type FileEvent = {
    files : string[]
    openFiles : string[]
}

const useFileWatcher = (initialFiles: File[], dirPath: string) => {
    const [files, setFiles] = useState<File<undefined>[]>(initialFiles)
    const [initialLoading, setInitialLoading] = useState(true)
    const [prevDirPath, setPrevDirPath] = useState<string | null>(null)

    useEffect(() => {
        const startWatching = async () => {
            if (!dirPath) {
                return () => {}
            }
            let loading = false
            if (prevDirPath !== dirPath) {
                setInitialLoading(true)
                loading = true
                setPrevDirPath(dirPath)
            }

            const success = await window.api.invoke('watch-dir', dirPath)
            if (!success) {
                console.error('Failed to start watching directory')
                return () => {}
            }
            const handleFileChanges = (events: FileEvent[]) => {
                if (initialLoading || loading) {
                    setInitialLoading(false)
                }
                setFiles(prevFiles => {
                    const fileMap = new Map(
                        prevFiles.map(file => [file.path, file])
                    )
                    events.forEach((event: FileEvent) => {
                        event.files.forEach(file => {
                            fileMap.set(file, {
                                id: file,
                                name: file.split('/').pop() ?? 'unnamed_file',
                                path: file,
                                language: getLanguageFromFilename(file.split('/').pop() ?? '') ?? '',
                                value: undefined,
                                icon: getIconFromFilename(file.split('/').pop() ?? '') ?? '',
                            })
                        })
                    })
                    return Array.from(fileMap.values())
                })
            }

            window.api.receive('editor-file-changed', handleFileChanges)

            return () => {
                window.api.send('unsubscribe')
                window.api.removeAllListeners('editor-file-changed')
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

    return { files, initialLoading }
}

export default useFileWatcher
