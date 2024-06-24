import { useState } from 'react'
import CodeEditor from './components/code-editor'
import ShellPanel from '@/panels/shell/shell-panel'
import { SessionMachineContext } from '@/contexts/session-machine-context'
import { Bot } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import FileTree from './components/file-tree/file-tree'
import { File } from '@/lib/types'
import {
    getLanguageFromFilename,
    getIconFromFilename,
} from '@/lib/programming-language-utils'
import useFileWatcher from './lib/hooks/use-file-watcher'

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

const EditorPanel = ({
    isExpandedVariant = false,
}: {
    chatId: string | null
    isExpandedVariant?: boolean
}) => {
    const { toast } = useToast()
    const [selectedFileId, setSelectedFileId] = useState<string | null>(null)

    const messages = SessionMachineContext.useSelector(state =>
        state.context.serverEventContext.messages.filter(
            message => message.type === 'tool'
        )
    )
    const path = SessionMachineContext.useSelector(
        state => state.context?.sessionState?.path ?? ''
    )
    const showEditorBorders = true

    const initialFiles: File[] = SessionMachineContext.useSelector(state => {
        if (
            state.context.sessionState?.editor &&
            state.context.sessionState.editor.files
        ) {
            return Object.keys(state.context.sessionState.editor.files).map(
                filepath => ({
                    id: filepath,
                    name: filepath.split('/').pop() ?? 'unnamed_file',
                    path: filepath,
                    language: getLanguageFromFilename(
                        filepath.split('/').pop()
                    ),
                    value: state.context.sessionState.editor.files[filepath],
                    icon: getIconFromFilename(filepath.split('/').pop()),
                })
            )
        } else {
            return []
        }
    })
    const files = useFileWatcher(initialFiles, path)

    if (files && files.length > 0 && !selectedFileId) {
        setSelectedFileId(files[0].id)
    } else if ((!files || files.length === 0) && selectedFileId) {
        setSelectedFileId(null)
    }

    return (
        <div
            className={`flex flex-col h-full w-full ${
                showEditorBorders ? 'pb-7' : ''
            }`}
        >
            <div
                className={`flex flex-row h-full ${
                    showEditorBorders
                        ? 'rounded-md border bg-midnight border-outlinecolor pt-0 mr-3 overflow-hidden'
                        : ''
                }`}
            >
                <div className="flex flex-col flex-grow w-full h-full">
                    <div className="w-full border-b border-outlinecolor flex justify-center py-1 relative">
                        <div className="flex space-x-2 ml-2 mr-4 absolute left-1 top-[11px] opacity-80">
                            <div className="w-[9px] h-[9px] bg-red-500 rounded-full"></div>
                            <div className="w-[9px] h-[9px] bg-yellow-400 rounded-full"></div>
                            <div className="w-[9px] h-[9px] bg-green-500 rounded-full"></div>
                        </div>
                        <button
                            onClick={() =>
                                toast({
                                    title: 'Hey! ~ Devon waves at you ~ 👋',
                                })
                            }
                            className="group smooth-hover bg-night px-[100px] border border-outlinecolor rounded-md my-1 flex gap-[5px] items-center"
                        >
                            <Bot
                                size={12}
                                className="group-hover:smooth-hover group-hover:text-white text-neutral-400 mb-[2px] -ml-2"
                            />
                            <p className="group-hover:smooth-hover group-hover:text-white text-[0.8rem] text-neutral-400">
                                Devon
                            </p>
                        </button>
                    </div>
                    <div className="flex flex-grow overflow-hidden">
                        <div className="flex-none w-40 bg-midnight border-r border-outlinecolor">
                            <FileTree
                                files={files}
                                selectedFileId={selectedFileId}
                                setSelectedFileId={setSelectedFileId}
                                projectPath={path}
                            />
                        </div>
                        <div className="flex-grow flex flex-col overflow-hidden">
                            <CodeEditor
                                files={files}
                                selectedFileId={selectedFileId}
                                setSelectedFileId={setSelectedFileId}
                                isExpandedVariant={isExpandedVariant}
                                showEditorBorders={showEditorBorders}
                                path={path}
                            />
                        </div>
                    </div>
                    <div className={`h-[23vh] ${showEditorBorders ? '' : ''}`}>
                        <ShellPanel messages={messages} />
                    </div>
                </div>
            </div>
        </div>
    )
}

export default EditorPanel
