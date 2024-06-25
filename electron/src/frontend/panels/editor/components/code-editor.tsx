import { useEffect, useState, useRef } from 'react'
import Editor, { Monaco } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import FileTabs from '@/panels/editor/components/file-tabs/file-tabs'
import { File } from '@/lib/types'
import { atom, useAtom } from 'jotai'

export const selectedCodeSnippetAtom = atom<string | null>(null)

export default function CodeEditor({
    files,
    selectedFileId,
    setSelectedFileId,
    isExpandedVariant = false,
    showEditorBorders,
    path,
}: {
    files: File[]
    selectedFileId: string | null
    setSelectedFileId: (id: string) => void
    isExpandedVariant?: boolean
    showEditorBorders: boolean
    path: string
}): JSX.Element {
    const [popoverVisible, setPopoverVisible] = useState(false)
    const [popoverPosition, setPopoverPosition] = useState({ top: 0, left: 0 })
    const [selectionInfo, setSelectionInfo] = useState<{
        path: string | null
        selection: string
        startLineNumber: number
        endLineNumber: number
        startColumn: number
        endColumn: number
    } | null>(null)
    const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)

    const handleEditorDidMount = (
        editor: editor.IStandaloneCodeEditor,
        monaco: Monaco
    ) => {
        editorRef.current = editor
        monaco.editor.defineTheme('theme', {
            base: 'vs-dark',
            inherit: true,
            rules: [],
            colors: {
                // 'editor.background': bgColor,
            },
        })

        monaco.editor.setTheme('theme')

        editor.onDidChangeCursorSelection(e => {
            const selection = editor.getSelection()
            if (selection && !selection.isEmpty()) {
                const range = new monaco.Range(
                    selection.startLineNumber,
                    selection.startColumn,
                    selection.endLineNumber,
                    selection.endColumn
                )
                const lineHeight = editor.getOption(
                    monaco.editor.EditorOption.lineHeight
                )
                const top =
                    editor.getTopForLineNumber(range.endLineNumber) +
                    lineHeight +
                    50
                // const left = editor.getOffsetForColumn(
                //     range.startLineNumber,
                //     range.startColumn
                // ) + 20
                const lineNumberColWidth = 57
                const left = lineNumberColWidth

                const selectedText = editor.getModel()?.getValueInRange(range)
                const startLineNumber = selection.startLineNumber
                const endLineNumber = selection.endLineNumber
                const startColumn = selection.startColumn
                const endColumn = selection.endColumn

                setSelectionInfo({
                    path: selectedFileId,
                    selection: selectedText,
                    startLineNumber,
                    endLineNumber,
                    startColumn,
                    endColumn,
                })

                setPopoverPosition({ top, left })
                // setPopoverVisible(true)
            } else {
                setPopoverVisible(false)
            }
        })
    }

    // Add a mouseup event listener to show the popover
    useEffect(() => {
        const handleMouseUp = () => {
            const selection = editorRef.current?.getSelection()
            if (selection && !selection.isEmpty()) {
                setPopoverVisible(true)
            }
        }

        window.addEventListener('mouseup', handleMouseUp)
        return () => {
            window.removeEventListener('mouseup', handleMouseUp)
        }
    }, [])

    const [, setSelectedCodeSnippet] = useAtom<string | null>(
        selectedCodeSnippetAtom
    )

    const handleAddCodeReference = () => {
        if (selectionInfo) {
            const snippetText = `${selectionInfo.path}:${selectionInfo.startLineNumber}-${selectionInfo.endLineNumber}\n${selectionInfo.selection}`
            setSelectedCodeSnippet(snippetText)
            console.log('Code snippet added:', snippetText)
        }
        setPopoverVisible(false)
    }

    return (
        <div className="flex flex-col h-full overflow-hidden relative">
            <div className="flex-none overflow-x-auto whitespace-nowrap bg-night border-b border-outlinecolor">
                <FileTabs
                    files={files}
                    selectedFileId={selectedFileId ?? null}
                    setSelectedFileId={setSelectedFileId}
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
                        className="absolute bg-night px-3 py-2 rounded-md shadow border hover:border-primary smooth-hover text-sm hover:bg-night"
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
        value={file?.value?.lines ?? ''}
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
    selectedFileId: string
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
