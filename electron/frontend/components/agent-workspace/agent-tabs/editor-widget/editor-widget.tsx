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
        lines: `# Welcome to Devon!`,
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
            const { editor } = await fetchSessionState(chatId)
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

    return (
        <CodeEditorContextProvider tabFiles={files}>
            <div className="flex flex-row h-full w-full pr-[2px]">
                <div className="flex-none w-48 bg-midnight">
                    <FileTree />
                </div>
                <div className="flex-grow w-full h-full">
                    <div className="h-2/3 -mr-[13px]">
                        <CodeEditor isExpandedVariant={isExpandedVariant} />
                    </div>
                    <div className="">
                    <ShellWidget />
                    </div>
                </div>
            </div>
        </CodeEditorContextProvider>
    )
}

export default EditorWidget
