import { useEffect, useState, useRef, useCallback } from 'react'
import Editor, { Monaco } from '@monaco-editor/react'
import type { editor, Selection } from 'monaco-editor'
import FileTabs from '@/panels/editor/components/file-tabs/file-tabs'
import { File } from '@/lib/types'
import { atom, useAtom } from 'jotai'
import { ICodeSnippet } from '@/panels/chat/components/ui/code-snippet'
import { getRelativePath, getFileName } from '@/lib/utils'

export const selectedCodeSnippetAtom = atom<ICodeSnippet | null>(null)

export default function CodeEditor({
    files,
    selectedFileId,
    setSelectedFileId,
    isExpandedVariant = false,
    showEditorBorders,
    path,
    initialFiles,
}: {
    files: File[]
    selectedFileId: string | null
    setSelectedFileId: (id: string | null) => void
    isExpandedVariant?: boolean
    showEditorBorders: boolean
    path: string
    initialFiles: File[]
}): JSX.Element {
    const [popoverVisible, setPopoverVisible] = useState(false)
    const [popoverPosition, setPopoverPosition] = useState({ top: 0, left: 0 })
    const [selectionInfo, setSelectionInfo] = useState<ICodeSnippet | null>(
        null
    )
    const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)
    const monacoRef = useRef<Monaco | null>(null)
    const [openFiles, setOpenFiles] = useState<File[]>(initialFiles)
    const fileSelectionsRef = useRef<Record<string, Selection | null>>({})

    const addFileToOpenFiles = useCallback((file: File) => {
        setOpenFiles(prevOpenFiles => {
            if (!prevOpenFiles.some(f => f.id === file.id)) {
                return [...prevOpenFiles, file]
            }
            return prevOpenFiles
        })
    }, [])

    const handleFileSelect = useCallback(
        (id: string) => {
            setSelectedFileId(id)
            const selectedFile = files.find(f => f.id === id)
            if (selectedFile) {
                addFileToOpenFiles(selectedFile)
            }
        },
        [setSelectedFileId, files, addFileToOpenFiles]
    )

    const handleCloseTab = useCallback(
        (id: string) => {
            setOpenFiles(prevOpenFiles =>
                prevOpenFiles.filter(file => file.id !== id)
            )
            if (selectedFileId === id) {
                const remainingFiles = openFiles.filter(file => file.id !== id)
                if (remainingFiles.length > 0) {
                    setSelectedFileId(
                        remainingFiles[remainingFiles.length - 1].id
                    )
                } else {
                    setSelectedFileId(null)
                }
            }
        },
        [openFiles, selectedFileId, setSelectedFileId]
    )

    const updateSelectionInfo = useCallback(
        (
            editor: editor.IStandaloneCodeEditor,
            monaco: Monaco,
            selection: Selection,
            fileId: string
        ) => {
            const range = new monaco.Range(
                selection.startLineNumber,
                selection.startColumn,
                selection.endLineNumber,
                selection.endColumn
            )
            const lineHeight = editor.getOption(
                monaco.editor.EditorOption.lineHeight
            )
            const scrollTop = editor.getScrollTop()
            const top =
                editor.getTopForLineNumber(range.endLineNumber) +
                lineHeight +
                50 -
                scrollTop
            const tooltipXOffset = 57
            const left = tooltipXOffset

            const selectedText = editor.getModel()?.getValueInRange(range)
            const relativePath = getRelativePath(fileId, path)
            const fileName = getFileName(fileId)
            const language =
                files?.find(f => f.id === fileId)?.language ?? 'text'

            setSelectionInfo({
                id: `${relativePath}:${selection.startLineNumber}-${selection.endLineNumber}`,
                fullPath: fileId,
                relativePath,
                fileName,
                selection: selectedText ?? '',
                startLineNumber: selection.startLineNumber,
                endLineNumber: selection.endLineNumber,
                startColumn: selection.startColumn,
                endColumn: selection.endColumn,
                language,
            })

            setPopoverPosition({ top, left })
            setPopoverVisible(true)
        },
        [files, path]
    )

    const handleEditorDidMount = useCallback(
        (editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
            editorRef.current = editor
            monacoRef.current = monaco
            monaco.editor.defineTheme('theme', {
                base: 'vs-dark',
                inherit: true,
                rules: [],
                colors: {},
            })
            monaco.editor.setTheme('theme')
        },
        []
    )

    useEffect(() => {
        if (!editorRef.current || !monacoRef.current) return

        const editor = editorRef.current
        const monaco = monacoRef.current

        const handleMouseUp = () => {
            const selection = editor.getSelection()
            if (selection && !selection.isEmpty()) {
                setPopoverVisible(true)
            }
        }

        const handleSelectionChange = (
            e: editor.ICursorSelectionChangedEvent
        ) => {
            const selection = editor.getSelection()
            if (selectedFileId && selection && !selection.isEmpty()) {
                fileSelectionsRef.current[selectedFileId] = selection
                updateSelectionInfo(editor, monaco, selection, selectedFileId)
            } else {
                setPopoverVisible(false)
            }
        }

        const disposable = editor.onDidChangeCursorSelection(
            handleSelectionChange
        )

        // Restore selection when switching tabs or opening a new file
        if (selectedFileId) {
            const storedSelection = fileSelectionsRef.current[selectedFileId]
            if (storedSelection) {
                editor.setSelection(storedSelection)
                updateSelectionInfo(
                    editor,
                    monaco,
                    storedSelection,
                    selectedFileId
                )
            } else {
                // Clear selection and hide popover when opening a new file
                setPopoverVisible(false)
                editor.setSelection(new monaco.Selection(0, 0, 0, 0))
            }
        }
        window.addEventListener('mouseup', handleMouseUp)

        return () => {
            disposable.dispose()
            window.removeEventListener('mouseup', handleMouseUp)
        }
    }, [
        selectedFileId,
        updateSelectionInfo,
        editorRef.current,
        monacoRef.current,
    ])

    useEffect(() => {
        if (selectedFileId) {
            const selectedFile = files.find(f => f.id === selectedFileId)
            if (selectedFile) {
                addFileToOpenFiles(selectedFile)
            }
        }
    }, [selectedFileId, files, addFileToOpenFiles])

    const [, setSelectedCodeSnippet] = useAtom<ICodeSnippet | null>(
        selectedCodeSnippetAtom
    )

    const handleAddCodeReference = () => {
        if (selectionInfo) {
            setSelectedCodeSnippet(selectionInfo)
        }
        // setPopoverVisible(false)
    }

    return (
        <div className="flex flex-col h-full overflow-hidden relative">
            <div className="flex-none overflow-x-auto whitespace-nowrap bg-night border-b border-outlinecolor">
                <FileTabs
                    files={openFiles}
                    selectedFileId={selectedFileId}
                    setSelectedFileId={handleFileSelect}
                    onCloseTab={handleCloseTab}
                    className={showEditorBorders ? '' : ''}
                    isExpandedVariant={isExpandedVariant}
                    loading={files.length === 0}
                />
            </div>
            {files && (
                <PathDisplay path={path} selectedFileId={selectedFileId} />
            )}
            <div className="flex-grow w-full bg-midnight rounded-b-lg mt-[-2px] overflow-auto">
                {selectedFileId && (
                    <BothEditorTypes
                        file={files?.find(f => f.id === selectedFileId)}
                        handleEditorDidMount={handleEditorDidMount}
                    />
                )}
                {popoverVisible && (
                    <button
                        onClick={handleAddCodeReference}
                        className="absolute bg-night px-3 py-2 rounded-md shadow border hover:border-primary smooth-hover text-sm hover:bg-night z-50"
                        style={{
                            top: popoverPosition.top,
                            left: popoverPosition.left,
                        }}
                    >
                        Mention snippet in chat
                    </button>
                )}
            </div>
        </div>
    )
}

const BothEditorTypes = ({
    file,
    handleEditorDidMount,
}: {
    file: File | undefined
    handleEditorDidMount: (
        editor: editor.IStandaloneCodeEditor,
        monaco: Monaco
    ) => void
}) => (
    <Editor
        className="h-full"
        theme="vs-dark"
        defaultLanguage={'python'}
        language={file?.language ?? 'python'}
        defaultValue={''}
        value={file?.value?.lines ?? file?.value ?? ''}
        onMount={handleEditorDidMount}
        path={file?.path}
        options={{ readOnly: true, fontSize: 10 }}
    />
)

function getPathBeforeLastSlash(str: string) {
    // Remove trailing slash if it exists
    str = str.replace(/\/$/, '')

    // Find the position of the last slash
    const lastSlashIndex = str.lastIndexOf('/')

    // Return the substring before the last slash
    return lastSlashIndex !== -1 ? str.substring(0, lastSlashIndex) : ''
}

const PathDisplay = ({
    path,
    selectedFileId,
}: {
    path: string
    selectedFileId: string | null
}) => (
    <div
        className={`px-3 pb-[4px] ${
            selectedFileId ? 'bg-night -mt-[2px]' : 'pt-[3px]'
        }`}
    >
        <p className="text-xs text-neutral-500">
            {selectedFileId
                ? convertPath(
                      selectedFileId.replace(getPathBeforeLastSlash(path), '')
                  )
                : path
                ? convertPath(path)
                : ''}
        </p>
    </div>
)

export function convertPath(path: string) {
    // Split the path based on the separator, either "/" or "\"
    const parts = path.split(/[/\\]/)

    // Remove unwanted parts (e.g., initial "Users" or "C:" for Windows paths)
    const filteredParts = parts.filter(
        part => part && part !== 'Users' && !part.includes(':')
    )

    // Join the remaining parts with the custom separator
    const customPath = filteredParts.join(' > ')

    return customPath
}
