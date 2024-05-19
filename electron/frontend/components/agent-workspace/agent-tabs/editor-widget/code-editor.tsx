import Editor, { Monaco } from '@monaco-editor/react'
// import { useSelector } from "react-redux";
import type { editor } from 'monaco-editor'
import { DiffEditor } from '@monaco-editor/react'
import FileTabs from '@/components/file-tabs/file-tabs'
import { useCodeEditorState } from '@/contexts/CodeEditorContext'
import { useSearchParams } from 'next/navigation'

const boilerplateFile = {
    id: 'main.py',
    name: 'main.py',
    path: 'main.py',
    language: 'python',
    value: {
        lines: `# Welcome to Devon!`,
    },
}

// Source: https://github.com/OpenDevin/OpenDevin/blob/main/frontend/src/components/CodeEditor.tsx
export default function CodeEditor({
    isExpandedVariant = false,
}: {
    isExpandedVariant?: boolean
}): JSX.Element {
    const searchParams = useSearchParams()
    const chatId = searchParams.get('chat')
    const {
        files,
        file,
        setFile,
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
                    files={[boilerplateFile]}
                    selectedFileId={boilerplateFile.id}
                    updateSelectedFile={updateSelectedFile}
                    diffEnabled={diffEnabled}
                    setDiffEnabled={setDiffEnabled}
                    chatId={chatId}
                />
                <div className="w-full h-full bg-bg-workspace rounded-b-lg overflow-hidden mt-[-2px]">
                    {boilerplateFile && (
                        <BothEditorTypes
                            diffEnabled={diffEnabled}
                            file={boilerplateFile}
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

    function updateSelectedFile(file: any) {
        setFile(file)
        setSelectedFileId(file.id)
    }

    const bgColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--bg-workspace')
        .trim()

    if (isExpandedVariant) {
        return (
            <div className="w-full h-full bg-bg-workspace rounded-b-lg overflow-hidden">
                <BothEditorTypes
                    diffEnabled={diffEnabled}
                    file={file}
                    handleEditorDidMount={handleEditorDidMount}
                />
            </div>
        )
    }

    return (
        <>
            <FileTabs
                files={files}
                selectedFileId={selectedFileId}
                updateSelectedFile={updateSelectedFile}
                diffEnabled={diffEnabled}
                setDiffEnabled={setDiffEnabled}
                chatId={chatId}
            />
            <div className="w-full h-full bg-bg-workspace rounded-b-lg overflow-hidden mt-[-2px]">
                {file && (
                    <BothEditorTypes
                        diffEnabled={diffEnabled}
                        file={file}
                        handleEditorDidMount={handleEditorDidMount}
                    />
                )}
            </div>
        </>
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
            options={{ readOnly: true }}
        />
    ) : (
        <DiffEditor
            height="100%"
            theme="vs-dark"
            original={file.value.lines}
            modified={file.value.lines}
            language={file.language}
            onMount={handleEditorDidMount}
            options={{ readOnly: true }}
        ></DiffEditor>
    )
