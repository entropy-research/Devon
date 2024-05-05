import React from 'react'
import Editor, { Monaco } from '@monaco-editor/react'
// import { useSelector } from "react-redux";
import type { editor } from 'monaco-editor'
import { DiffEditor } from '@monaco-editor/react'
import FileTabs from '@/components/file-tabs/file-tabs'
import { useCodeEditorState } from '@/contexts/CodeEditorContext'

// import { RootState } from "../store";

// export default function EditorWidget() {
//     return <CodeEditor />
// }

// Source: https://github.com/OpenDevin/OpenDevin/blob/main/frontend/src/components/CodeEditor.tsx
export default function CodeEditor({
    isExpandedVariant = false,
}: {
    isExpandedVariant?: boolean
}): JSX.Element {
    const {
        files,
        file,
        setFile,
        selectedFileId,
        setSelectedFileId,
        diffEnabled,
        setDiffEnabled,
    } = useCodeEditorState()

    if (!file || !selectedFileId || !files) {
        return <div>Loading...</div>
    }

    const code = ''

    function updateSelectedFile(file: any) {
        setFile(file)
        setSelectedFileId(file.id)
    }

    const bgColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--bg-workspace')
        .trim()

    const handleEditorDidMount = (
        editor: editor.IStandaloneCodeEditor,
        monaco: Monaco
    ) => {
        monaco.editor.defineTheme('my-theme', {
            base: 'vs-dark',
            inherit: true,
            rules: [],
            colors: {
                // 'editor.background': bgColor,
            },
        })

        monaco.editor.setTheme('my-theme')
    }

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
            />
            <div className="w-full h-full bg-bg-workspace rounded-b-lg overflow-hidden mt-[-2px]">
                <BothEditorTypes
                    diffEnabled={diffEnabled}
                    file={file}
                    handleEditorDidMount={handleEditorDidMount}
                />
            </div>
        </>
    )
}

const BothEditorTypes = ({ diffEnabled, file, handleEditorDidMount }) =>
    !diffEnabled ? (
        <Editor
            className="h-full"
            theme="vs-dark"
            defaultLanguage={file.language}
            language={file.language}
            defaultValue={file.value}
            value={file.value}
            onMount={handleEditorDidMount}
        />
    ) : (
        <DiffEditor
            height="100%"
            theme="vs-dark"
            original={file.value}
            modified={file.value}
            language={file.language}
            onMount={handleEditorDidMount}
        ></DiffEditor>
    )
