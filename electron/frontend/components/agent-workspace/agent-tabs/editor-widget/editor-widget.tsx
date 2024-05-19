import { useEffect, useState } from 'react'
import CodeEditor from './code-editor'
import { CodeEditorContextProvider } from '@/contexts/CodeEditorContext'
import { ChatProps } from '@/lib/chat.types'
import { fetchSessionState } from '@/lib/services/sessionService/use-session-state'
import FileTree from './file-tree/file-tree'

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
            const { PAGE_SIZE, data, editor } = await fetchSessionState(chatId)
            // Editor is a dictionary. Get the keys and values
            const _files: any = []
            for (let key in editor) {
                if (editor.hasOwnProperty(key)) {
                    // This check is necessary to exclude properties from the prototype chain
                    _files.push({
                        id: key,
                        name: key.split('/').pop(),
                        path: key,
                        language: 'python',
                        value: editor[key],
                    })
                }
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
            <div className="flex flex-row h-full pl-5">
                <div className="flex-none w-48">
                    <FileTree />
                </div>
                <div className="flex-grow">
                    <CodeEditor isExpandedVariant={isExpandedVariant} />
                </div>
            </div>
        </CodeEditorContextProvider>
    )
}

export default EditorWidget
