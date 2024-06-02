import Editor, { Monaco } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import { DiffEditor } from '@monaco-editor/react'
import FileTabs from '@/components/file-tabs/file-tabs'
import { useCodeEditorState } from '@/contexts/CodeEditorContext'
import { useSearchParams } from 'next/navigation'

// Source: https://github.com/OpenDevin/OpenDevin/blob/main/frontend/src/components/CodeEditor.tsx
export default function CodeEditor({
    isExpandedVariant = false,
    showEditorBorders,
    path,
}: {
    isExpandedVariant?: boolean
    showEditorBorders: boolean
    path: string
}): JSX.Element {
    const searchParams = useSearchParams()
    const chatId = searchParams.get('chat')
    const {
        files,
        selectedFileId,
        setSelectedFileId,
        diffEnabled,
        setDiffEnabled,
    } = useCodeEditorState()

    const handleEditorDidMount = (
        editor: editor.IStandaloneCodeEditor,
        monaco: Monaco
    ) => {
        monaco.editor.defineTheme('theme', {
            base: 'vs-dark',
            inherit: true,
            rules: [],
            colors: {
                // 'editor.background': bgColor,
            },
        })

        monaco.editor.setTheme('theme')
    }

    if (!selectedFileId || !chatId || chatId === 'New') {
        return (
            <>
                <FileTabs
                    files={files}
                    selectedFileId={selectedFileId ?? files[0]?.id}
                    setSelectedFileId={setSelectedFileId}
                    diffEnabled={diffEnabled}
                    setDiffEnabled={setDiffEnabled}
                    chatId={chatId}
                    className={showEditorBorders ? '' : 'mr-[13px]'}
                    isExpandedVariant={isExpandedVariant}
                />
                {files.length > 0 && (
                    <PathDisplay path={'/Users/devon/projects/hello_world'} />
                )}
                <div className="w-full bg-workspace rounded-b-lg mt-[-2px]">
                    {selectedFileId && (
                        <BothEditorTypes
                            diffEnabled={diffEnabled}
                            file={files?.find(f => f.id === selectedFileId)}
                            handleEditorDidMount={handleEditorDidMount}
                        />
                    )}
                </div>
            </>
        )
    }

    // if (!file || !selectedFileId || !files) {
    //     return (
    //         <p className="text-lg flex justify-center items-center h-full w-full">
    //             Loading...
    //         </p>
    //     )
    // }

    const bgColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--bg-workspace')
        .trim()

    if (isExpandedVariant) {
        return (
            <div className="w-full bg-workspace rounded-b-lg overflow-hidden">
                <BothEditorTypes
                    diffEnabled={diffEnabled}
                    file={files?.find(f => f.id === selectedFileId)}
                    handleEditorDidMount={handleEditorDidMount}
                />
            </div>
        )
    }

    return (
        <div className="flex flex-col w-full h-full">
            <FileTabs
                files={files}
                selectedFileId={selectedFileId}
                setSelectedFileId={setSelectedFileId}
                diffEnabled={diffEnabled}
                setDiffEnabled={setDiffEnabled}
                chatId={chatId}
                className={showEditorBorders ? '' : ''}
                isExpandedVariant={isExpandedVariant}
            />
            {files && <PathDisplay path={path} />}
            <div className="flex w-full h-full bg-bg-workspace rounded-b-lg mt-[-2px]">
                {selectedFileId && (
                    <BothEditorTypes
                        diffEnabled={diffEnabled}
                        file={files?.find(f => f.id === selectedFileId)}
                        handleEditorDidMount={handleEditorDidMount}
                    />
                )}
            </div>
        </div>
    )
}

const BothEditorTypes = ({ diffEnabled, file, handleEditorDidMount }) =>
    !diffEnabled ? (
        <Editor
            className="h-full"
            theme="vs-dark"
            defaultLanguage={'python'}
            language={file.language}
            defaultValue={''}
            value={file.value.lines}
            onMount={handleEditorDidMount}
            path={file.path}
            options={{ readOnly: true, fontSize: 10 }}
        />
    ) : (
        <DiffEditor
            className="h-full"
            theme="vs-dark"
            original={file.value.lines}
            modified={file.value.lines}
            language={file.language}
            onMount={handleEditorDidMount}
            options={{ readOnly: true, fontSize: 10 }}
        ></DiffEditor>
    )

const PathDisplay = ({ path }: { path: string }) => (
    <div className="-mt-[1px] px-3 py-1 bg-night border-t border-outlinecolor">
        <p className="text-xs text-neutral-500">
            {path ? convertPath(path) : ''}
        </p>
    </div>
)

function convertPath(path) {
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
