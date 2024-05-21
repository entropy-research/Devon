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
        <div className="flex justify-between bg-midnight mr-[13px] items-center">
            <div className="flex items-center justify-start">
                {files.map((file: any) => (
                    <button
                        key={file.id}
                        className={`flex px-2 justify-center items-center px-1 py-2 text-sm border-t-[1.5px] min-w-[100px] ${file.id === selectedFileId ? 'border-t-primary rounded-t-sm bg-night' : 'border-transparent'}`}
                        onClick={() => updateSelectedFile(file)}
                    >
                        {file.name}
                    </button>
                ))}
            </div>
            <div className="flex pr-3 h-full gap-2 items-center">
                <ActionItem
                    active={false}
                    icon={
                        <Maximize className="h-[1.2rem] w-[1.2rem] text-gray-300" />
                    }
                    dialogContent={
                        <DialogContent className="h-full max-w-screen block p-0 pt-10">
                            <EditorWidget isExpandedVariant chatId={chatId} />
                        </DialogContent>
                    }
                />
                <ActionItem
                    active={diffEnabled}
                    icon={
                        <FileDiff className="h-[1.2rem] w-[1.2rem] text-gray-300" />
                    }
                    clickAction={() => setDiffEnabled(!diffEnabled)}
                />
            </div>
        </div>
    )
}

export default FileTabs
