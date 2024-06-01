import { useEffect, useRef, useState } from 'react'
import CodeEditor from './code-editor'
import { CodeEditorContextProvider } from '@/contexts/CodeEditorContext'
import FileTree from './file-tree/file-tree'
import ShellWidget from '@/components/agent-workspace/agent-tabs/shell-widget'
import { SessionMachineContext } from '@/app/home'
import { File } from '@/lib/types'

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

const EditorWidget = ({
    chatId,
    isExpandedVariant = false,
}: {
    chatId: string | null
    isExpandedVariant?: boolean
}) => {
    let messages = SessionMachineContext.useSelector(state =>
        state.context.serverEventContext.messages.filter(
            message => message.type === 'tool'
        )
    )
    const state = SessionMachineContext.useSelector(state => state)
    const showEditorBorders = true

    return (
        <CodeEditorContextProvider chatId={chatId}>
            <div
                className={`flex flex-col h-full w-full ${showEditorBorders ? 'pb-3' : ''}`}
            >
                <div
                    className={`flex flex-row h-full ${showEditorBorders ? 'rounded-md border bg-midnight border-neutral-600 pt-2 mr-3 overflow-hidden' : ''}`}
                >
                    <div className="flex-none w-48 bg-midnight">
                        <FileTree />
                    </div>
                    <div className="flex flex-col flex-grow w-full h-full">
                        <div className="flex-grow overflow-auto">
                            <CodeEditor
                                isExpandedVariant={isExpandedVariant}
                                showEditorBorders={showEditorBorders}
                                path={state.context.path}
                            />
                        </div>
                    </div>
                </div>
                <div className={`h-[23vh] ${showEditorBorders ? '' : ''}`}>
                    <ShellWidget messages={messages} />
                </div>
            </div>
        </CodeEditorContextProvider>
    )
}

export default EditorWidget
