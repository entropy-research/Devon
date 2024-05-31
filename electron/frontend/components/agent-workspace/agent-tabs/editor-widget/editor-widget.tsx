import { useEffect, useRef, useState } from 'react'
import CodeEditor from './code-editor'
import { CodeEditorContextProvider } from '@/contexts/CodeEditorContext'
import { fetchSessionState } from '@/lib/services/sessionService/sessionService'
import FileTree from './file-tree/file-tree'
import ShellWidget from '@/components/agent-workspace/agent-tabs/shell-widget'
import { SessionMachineContext } from '@/app/home'

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
    // const [files, setFiles] = useState([])

    let files = useRef([])

    let messages = SessionMachineContext.useSelector(state => state.context.serverEventContext.messages.filter(message => message.type === 'tool'))
    console.log(messages)
    const state = SessionMachineContext.useSelector((state) => state);

    useEffect(()=>{
        async function getSessionState() {
            const res = await fetchSessionState(chatId)
            if (!res || !res?.editor || !res?.editor.files) return
            const editor = res.editor
            const f = editor.files
            // Editor is a dictionary. Get the keys and values
            const _files: any = []

            for (let key in f) {
                if (f.hasOwnProperty(key)) {
                    // This check is necessary to exclude properties from the prototype chain
                    _files.push({
                        id: key,
                        name: key.split('/').pop(),
                        path: key,
                        language: 'python',
                        value: f[key],
                    })
                }
            }
            if (!files || _files?.length === 0) {
                _files.push(boilerplateFile)
                _files.push(boilerplateFile2)
            }
            files.current = _files
        }
        getSessionState()
    },[messages])
    
    console.log(files.current)

    const showEditorBorders = true

    return (
        <CodeEditorContextProvider tabFiles={files.current}>
            <div className={`flex flex-col h-full w-full ${showEditorBorders ? 'pb-3' : ''}`}>
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
                <div
                    className={`h-[23vh] ${showEditorBorders ? '' : ''}`}
                >
                    <ShellWidget messages={messages} />
                </div>
            </div>
        </CodeEditorContextProvider>
    )
}

export default EditorWidget
