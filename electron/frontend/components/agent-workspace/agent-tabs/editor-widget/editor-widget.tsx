import { useEffect, useState } from 'react'
import CodeEditor from './code-editor'
import { CodeEditorContextProvider } from '@/contexts/CodeEditorContext'
import { ChatProps } from '@/lib/chat.types'
import { fetchSessionState } from '@/lib/services/sessionService/use-session-state'
import FileTree from './file-tree/file-tree'
import ShellWidget from '@/components/agent-workspace/agent-tabs/shell-widget'

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
        lines: `# Hello world!`,
    },
}

const EditorWidget = ({
    chatId,
    isExpandedVariant = false,
}: {
    chatId: string | null
    isExpandedVariant?: boolean
}) => {
    const [files, setFiles] = useState([])

    useEffect(() => {
        if (!chatId || chatId === 'New') return

        async function getSessionState() {
            const res = await fetchSessionState(chatId)
            console.log(res.data)
            const editor = res.editor
            const ed = editor.files
            // Editor is a dictionary. Get the keys and values
            const _files: any = []

            for (let key in ed) {
                if (ed.hasOwnProperty(key)) {
                    // This check is necessary to exclude properties from the prototype chain
                    _files.push({
                        id: key,
                        name: key.split('/').pop(),
                        path: key,
                        language: 'python',
                        value: ed[key],
                    })
                }
            }
            if (!_files.length) {
                _files.push(boilerplateFile)
                _files.push(boilerplateFile2)
            }
            setFiles(_files)
        }
        const intervalId = setInterval(getSessionState, 2000)

        return () => {
            clearInterval(intervalId)
        }
    }, [chatId])

    const showEditorBorders = true

    return (
        <CodeEditorContextProvider tabFiles={files}>
            <div className={`flex flex-col h-full w-full ${showEditorBorders ? 'pb-3' : ''}`}>
                <div
                    className={`flex flex-row h-full ${showEditorBorders ? 'rounded-md border bg-midnight border-neutral-600 py-2 mr-3' : ''}`}
                >
                    <div className="flex-none w-48 bg-midnight">
                        <FileTree />
                    </div>
                    <div className="flex flex-col flex-grow w-full h-full">
                        <div className="flex-grow overflow-auto">
                            <CodeEditor
                                isExpandedVariant={isExpandedVariant}
                                showEditorBorders={showEditorBorders}
                            />
                        </div>
                        <div
                            className={`h-[23vh] ${showEditorBorders ? '' : ''}`}
                        >
                            <ShellWidget />
                        </div>
                    </div>
                </div>
            </div>
        </CodeEditorContextProvider>
    )
}

export default EditorWidget
