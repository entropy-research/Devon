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

const EditorPanel = ({
    isExpandedVariant = false,
}: {
    chatId: string | null
    isExpandedVariant?: boolean
}) => {
    const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
    const [openFiles, setOpenFiles] = useState<File[]>([])
    const prevInitialFilesRef = useRef<File[]>([])

    const messages = SessionMachineContext.useSelector(state =>
        state.context.serverEventContext.messages.filter(
            message => message.type === 'tool'
        )
    )
    const path = SessionMachineContext.useSelector(
        state => state.context?.sessionState?.path ?? ''
    )
    const showEditorBorders = true

    const initialFiles: File[] = SessionMachineContext.useSelector(state => {
        if (
            state.context.sessionState?.editor &&
            state.context.sessionState.editor.files
        ) {
            return Object.keys(state.context.sessionState.editor.files).map(
                filepath => ({
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
                })
            )
        } else {
            return [] as File[]
        }
    })

    const { files, initialLoading } = useFileWatcher(initialFiles, path)

    useEffect(() => {
        const prevInitialFiles = prevInitialFilesRef.current

        // Detect new files in initialFiles
        const newFiles = initialFiles.filter(
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
        prevInitialFilesRef.current = initialFiles
    }, [initialFiles])

    const handleFileSelect = useCallback(
        (fileId: string | null) => {
            setSelectedFileId(fileId)
            const selectedFile = files.find(file => file.id === fileId)
            if (selectedFile && !openFiles.some(file => file.id === fileId)) {
                setOpenFiles(prevOpenFiles => [...prevOpenFiles, selectedFile])
            }
        },
        [files, openFiles]
    )

    return (
        <div
            className={`flex flex-col h-full w-full ${
                showEditorBorders ? 'pb-7' : ''
            }`}
        >
            <div
                className={`flex flex-row h-full ${
                    showEditorBorders
                        ? 'rounded-md border bg-midnight border-outlinecolor pt-0 mr-3 overflow-hidden'
                        : ''
                }`}
            >
                <div
                    // direction="vertical"
                    className="flex flex-col flex-grow w-full h-full"
                >
                    <EditorPanelHeader path={path} />
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
                                    files={files}
                                    selectedFileId={selectedFileId}
                                    setSelectedFileId={handleFileSelect}
                                    isExpandedVariant={isExpandedVariant}
                                    showEditorBorders={showEditorBorders}
                                    path={path}
                                    initialFiles={openFiles}
                                />
                            </ResizablePanel>
                        </ResizablePanelGroup>
                    </div>

                    {/* <ResizableHandle /> */}
                    <div
                        // defaultSize={20}
                        className={`h-[20vh] ${showEditorBorders ? '' : ''}`}
                    >
                        <ShellPanel messages={messages} />
                    </div>
                </div>
            </div>
        </div>
    )
}

export default EditorPanel
