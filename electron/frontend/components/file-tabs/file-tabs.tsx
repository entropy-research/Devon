import React from 'react'
import { Maximize, FileDiff } from 'lucide-react'
import ActionItem from './action-item'
import {
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import EditorWidget from '@/components/agent-workspace/agent-tabs/editor-widget/editor-widget'

// The file tabs at the top of the editor widget. Also used in the shell widget
const FileTabs = ({
    files,
    selectedFileId,
    updateSelectedFile,
    diffEnabled,
    setDiffEnabled,
    chatId,
}: {
    files: any[]
    selectedFileId: string
    updateSelectedFile: (file: any) => void
    diffEnabled: boolean
    setDiffEnabled: (value: boolean) => void
    chatId: string | null
}) => {
    return (
        <div className="flex justify-between w-full">
            <div className="flex items-center justify-start">
                {files.map((file: any) => (
                    <button
                        key={file.id}
                        className={`px-5 py-3 text-md border-t-4 min-w-[150px] ${file.id === selectedFileId ? 'border-t-aqua outline outline-gray-500 outline-[1.5px] rounded-t-lg' : 'border-transparent'}`}
                        onClick={() => updateSelectedFile(file)}
                    >
                        {file.name}
                    </button>
                ))}
            </div>
            <div className="flex px-2 pr-4 py-2 h-full gap-2">
                <ActionItem
                    active={false}
                    icon={<Maximize className="h-5 w-5 text-gray-450" />}
                    dialogContent={
                        <DialogContent className="h-full max-w-4xl block">
                            <DialogHeader className="mb-4">
                                <DialogTitle>Expanded Editor</DialogTitle>
                            </DialogHeader>
                            <EditorWidget isExpandedVariant chatId={chatId}/>
                        </DialogContent>
                    }
                />
                <ActionItem
                    active={diffEnabled}
                    icon={<FileDiff className="h-5 w-5 text-gray-300" />}
                    clickAction={() => setDiffEnabled(!diffEnabled)}
                />
            </div>
        </div>
    )
}

export default FileTabs
