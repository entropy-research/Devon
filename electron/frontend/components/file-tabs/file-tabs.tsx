import React from 'react'
import { Maximize, FileDiff } from 'lucide-react'
import ActionItem from './action-item'
import {
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import EditorWidget from '@/components/agent-workspace/agent-tabs/editor-widget/editor-widget'
import { File } from '@/lib/types'

// The file tabs at the top of the editor widget. Also used in the shell widget
const FileTabs = ({
    files,
    selectedFileId,
    setSelectedFileId,
    diffEnabled,
    setDiffEnabled,
    chatId,
    className,
    isExpandedVariant,
}: {
    files: any[]
    selectedFileId: string
    setSelectedFileId: (id: string) => void
    diffEnabled: boolean
    setDiffEnabled: (value: boolean) => void
    chatId: string | null
    className?: string
    isExpandedVariant: boolean
}) => {
    return (
        <div
            className={`flex justify-between bg-[#141414] items-center ${className}`}
        >
            <div className="flex items-center justify-start">
                {files.map((file: File, index: number) => (
                    <button
                        key={file.id}
                        className={`flex px-2 justify-center items-center px-1 py-[6px] text-sm border-t-[1.5px] min-w-[100px] ${file.id === selectedFileId ? `border-t-primary rounded-t-sm bg-night border-b-[1px] border-b-night ${index === 0 ? 'border-r-[1px] border-r-outlinecolor' : 'border-x-[1px] border-x-outlinecolor'} z-10` : 'border-transparent outline outline-[1px] outline-outlinecolor'}`}
                        onClick={() => setSelectedFileId(file.id)}
                    >
                        {file.name}
                    </button>
                ))}
            </div>
            {/* <div className="flex pr-3 h-full gap-2 items-center pb-1">
                {!isExpandedVariant && (
                    <ActionItem
                        active={false}
                        icon={
                            <Maximize className="h-[1.2rem] w-[1.2rem] text-gray-300" />
                        }
                        dialogContent={
                            <DialogContent className="h-full max-w-screen block p-0 mt-10 pt-10">
                                <EditorWidget
                                    isExpandedVariant
                                    chatId={chatId}
                                />
                            </DialogContent>
                        }
                    />
                )}
                <ActionItem
                    active={diffEnabled}
                    icon={
                        <FileDiff className="h-[1.2rem] w-[1.2rem] text-gray-300" />
                    }
                    clickAction={() => setDiffEnabled(!diffEnabled)}
                />
            </div> */}
        </div>
    )
}

export default FileTabs
