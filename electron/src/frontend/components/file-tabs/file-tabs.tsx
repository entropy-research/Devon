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
import { Icon } from '@iconify/react' // https://iconify.design/docs/icon-components/react/
import { Skeleton } from '@/components/ui/skeleton'

// The file tabs at the top of the editor widget. Also used in the shell widget
const FileTabs = ({
    files,
    selectedFileId,
    setSelectedFileId,
    // diffEnabled,
    // setDiffEnabled,
    // chatId,
    className,
    isExpandedVariant,
    loading = false,
}: {
    files: any[]
    selectedFileId: string
    setSelectedFileId: (id: string) => void
    // diffEnabled: boolean
    // setDiffEnabled: (value: boolean) => void
    // chatId: string | null
    className?: string
    isExpandedVariant: boolean
    loading?: boolean
}) => {
    return (
        <div
            className={`flex justify-between bg-[#141414] items-center ${className}`}
        >
            <div className="flex items-center justify-start">
                {false // used to be "loading" commenting out for now
                    ? Array.from({ length: 2 }).map((_, index) => (
                          <button
                              key={index}
                              className={`flex justify-center items-center px-4 ${false ? 'pr-5' : ''} py-[6px] text-sm border-t-[1.5px] ${index === 0 ? `border-t-primary rounded-t-sm bg-night border-b-[1px] border-b-night ${index === 0 ? 'border-r-[1px] border-r-outlinecolor' : 'border-x-[1px] border-x-outlinecolor'} z-10` : 'border-transparent outline outline-[1px] outline-outlinecolor'}`}
                          >
                              <Skeleton
                                  key={index}
                                  className={`w-[68px] h-3 my-[3px] rounded-[3px] ${index === 0 ? 'bg-neutral-800' : 'bg-night'}`}
                              />
                          </button>
                      ))
                    : files.map((file: File, index: number) => (
                          <button
                              key={file.id}
                              className={`flex justify-center items-center px-4 ${file.icon ? 'pr-5' : ''} py-[6px] text-sm border-t-[1.5px] ${file.id === selectedFileId ? `border-t-primary rounded-t-sm bg-night border-b-[1px] border-b-night ${index === 0 ? 'border-r-[1px] border-r-outlinecolor' : 'border-x-[1px] border-x-outlinecolor'} z-10` : 'border-transparent outline outline-[1px] outline-outlinecolor'}`}
                              onClick={() => setSelectedFileId(file.id)}
                          >
                              {file.icon && (
                                  <Icon
                                      icon={file.icon}
                                      className="h-4 w-4 mr-2"
                                  />
                              )}
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
