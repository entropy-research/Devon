import { useEffect, useState, useRef, useMemo, useCallback } from 'react'
import CodeEditor from './components/code-editor'
import ShellPanel from '@/panels/shell/shell-panel'
import { SessionMachineContext } from '@/contexts/session-machine-context'
import { Bot } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import FileTree from './components/file-tree/file-tree'
import { File } from '@/lib/types'
import {
    getLanguageFromFilename,
    getIconFromFilename,
} from '@/lib/programming-language-utils'
import useFileWatcher from './lib/hooks/use-file-watcher'
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable'
import EditorPanelHeader from './components/editor-panel-header'

const boilerplateFile = {
    id: 'main.py',
    name: 'main.py',
    path: 'main.py',
    language: 'python',
    value: {
        lines: `# Welcome to Devon!
`,
    },
}

const boilerplateFile2 = {
    id: 'hello.py',
    name: 'hello.py',
    path: 'hello.py',
    language: 'python',
    value: {
        lines: `# Hello world!
`,
    },
}

type FileEvent = {
    files: string[]
    openFiles: {
        path: string
        content: string
    }[]
}


const EditorPanel = ({
    isExpandedVariant = false,
}: {
    chatId: string | null
    isExpandedVariant?: boolean
}) => {
    const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
    const [openFiles, setOpenFiles] = useState<File<string>[]>([])
    const prevInitialFilesRef = useRef<File<string>[]>([])
    const [initialLoading, setInitialLoading] = useState(true)
    const [prevDirPath, setPrevDirPath] = useState<string | null>(null)
    const [files, setFiles] = useState<File<undefined>[]>([])


    const path = SessionMachineContext.useSelector(
        state => state.context?.sessionState?.path ?? ''
    )
    const showEditorBorders = true

    const agentFiles: File[] = SessionMachineContext.useSelector(state => {
        if (
            state.context.sessionState?.editor &&
            state.context.sessionState.editor.files
        ) {
            // console.log(state.context.sessionState.editor.files)


            return Object.keys(state.context.sessionState.editor.files).map(
                filepath => {
                    window.api.invoke('editor-add-open-file', filepath)
                    return {
                        id: filepath,
                        name: filepath.split('/').pop() ?? 'unnamed_file',
                        path: filepath,
                        language:
                            getLanguageFromFilename(
                                filepath.split('/').pop() ?? ''
                            ) ?? '',
                        value: state.context.sessionState.editor.files[filepath],
                        icon:
                            getIconFromFilename(filepath.split('/').pop() ?? '') ??
                            '',
                        agentHasOpen: true,
                    }
                }
            )
        } else {
            return [] as File[]
        }
    },(prevState,newState)=> {
        // Deep equality check for arrays
        if (prevState.length !== newState.length) {
            return false;
        }
        
        for (let i = 0; i < prevState.length; i++) {
            if (prevState[i].id !== newState[i].id) {
                return false;
            }
        }
        return true;
    })


    // const { files, initialLoading } = useFileWatcher(initialFiles, path)
    let dirPath = path
    useEffect(() => {
        const startWatching = async () => {
            if (!dirPath) {
                return () => { }
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
                return () => { }
            }
            const handleFileChanges = (events: FileEvent) => {
                if (initialLoading || loading) {
                    setInitialLoading(false)
                }
                setFiles(prevFiles => {
                    const fileMap = new Map(
                        prevFiles.map(file => [file.path, file])
                    )
   
                        events.files.forEach(file => {
                            fileMap.set(file, {
                                id: file,
                                name: file.split('/').pop() ?? 'unnamed_file',
                                path: file,
                                language: getLanguageFromFilename(file.split('/').pop() ?? '') ?? '',
                                value: undefined,
                                icon: getIconFromFilename(file.split('/').pop() ?? '') ?? '',
                            })
                        })
                    return Array.from(fileMap.values())
                })
                
                setOpenFiles(events.openFiles.map((file) => {
                    return {
                        id: file.path,
                        name: file.path.split('/').pop() ?? 'unnamed_file',
                        path: file.path,
                        language: getLanguageFromFilename(file.path.split('/').pop() ?? '') ?? '',
                        value: file.content,
                        icon: getIconFromFilename(file.path.split('/').pop() ?? '') ?? '',
                        }
                    }))
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

    useEffect(() => {
        const prevInitialFiles = prevInitialFilesRef.current

        // Detect new files in initialFiles
        const newFiles = agentFiles.filter(
            file =>
                !prevInitialFiles.some(prevFile => prevFile.path === file.path)
        )

        if (newFiles.length > 0) {
            setOpenFiles(prevOpenFiles => [...prevOpenFiles, ...newFiles])
            if (selectedFileId === null) {
                setSelectedFileId(newFiles[0].id)
            }
        }

        // Update the ref for the next comparison
        prevInitialFilesRef.current = agentFiles
    }, [agentFiles])

    useEffect(() => {
        openFiles.forEach(file => {
            if (!file.value) {
                window.api.invoke("editor-add-open-file", file.path)
            }
        })
    }, [openFiles])

    const handleFileSelect = useCallback(
        (fileId: string | null) => {
            setSelectedFileId(fileId)
            let selectedFile = files.find(file => file.id === fileId)

            if (selectedFile && !openFiles.some(file => file.id === fileId)) {
                selectedFile.value = "" 
                setOpenFiles(prevOpenFiles => [...prevOpenFiles, selectedFile as unknown as File<string>])
            }
        },
        [files, openFiles]
    )

    return (
        <div
            className={`flex flex-col h-full w-full ${showEditorBorders ? 'pb-7' : ''
                }`}
        >
            <div
                className={`flex flex-row h-full ${showEditorBorders
                        ? 'rounded-md border bg-midnight border-outlinecolor pt-0 mr-3 overflow-hidden'
                        : ''
                    }`}
            >
                <div
                    // direction="vertical"
                    className="flex flex-col flex-grow w-full h-full"
                >
                    <EditorPanelHeader path={path} initialLoading={initialLoading}/>
                    <div
                        // defaultSize={80}
                        className="flex overflow-hidden h-full"
                    >
                        <ResizablePanelGroup direction="horizontal">
                            <ResizablePanel
                                defaultSize={20}
                                className="flex-none w-40 bg-midnight border-r border-outlinecolor"
                            >
                                <FileTree
                                    files={files}
                                    selectedFileId={selectedFileId}
                                    setSelectedFileId={handleFileSelect}
                                    projectPath={path}
                                    initialLoading={initialLoading}
                                />
                            </ResizablePanel>
                            <ResizableHandle />
                            <ResizablePanel
                                defaultSize={80}
                                className="flex-grow flex flex-col overflow-hidden"
                            >
                                <CodeEditor
                                    files={openFiles}
                                    selectedFileId={selectedFileId}
                                    setSelectedFileId={handleFileSelect}
                                    isExpandedVariant={isExpandedVariant}
                                    showEditorBorders={showEditorBorders}
                                    path={path}
                                    initialFiles={agentFiles}
                                />
                            </ResizablePanel>
                        </ResizablePanelGroup>
                    </div>

                    {/* <ResizableHandle /> */}
                    <div
                        // defaultSize={20}
                        className={`h-[20vh] ${showEditorBorders ? '' : ''}`}
                    >
                        <ShellPanel path={path} />
                    </div>
                </div>
            </div>
        </div>
    )
}

export default EditorPanel
