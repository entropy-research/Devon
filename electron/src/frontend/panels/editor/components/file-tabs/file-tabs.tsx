import { useRef, useEffect, useLayoutEffect } from 'react'
import { Maximize, FileDiff } from 'lucide-react'
import ActionItem from './action-item'
import {
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import EditorPanel from '@/panels/editor/editor-panel'
import { File } from '@/lib/types'
import { Icon } from '@iconify/react' // https://iconify.design/docs/icon-components/react/
import { Skeleton } from '@/components/ui/skeleton'
import React, { ReactNode } from 'react'

interface CustomScrollbarProps {
    children: ReactNode
    innerRef?: React.RefObject<HTMLDivElement>
}

const CustomScrollbar: React.FC<CustomScrollbarProps> = ({ children, innerRef }) => {
    return (
        <div ref={innerRef} className="horizontal-scrollbar overflow-x-auto">{children}</div>
    )
}

// The file tabs at the top of the editor panel. Also used in the shell panel
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
    const fileRefs = useRef(new Map<string, HTMLButtonElement>())
    const scrollContainerRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (selectedFileId && fileRefs.current.has(selectedFileId)) {
            const selectedFileElement = fileRefs.current.get(selectedFileId)
            const scrollContainer = scrollContainerRef.current
            if (selectedFileElement && scrollContainer) {
                const elementRect = selectedFileElement.getBoundingClientRect()
                const containerRect = scrollContainer.getBoundingClientRect()

                if (elementRect.left < containerRect.left) {
                    // Element is out of view on the left side
                    scrollContainer.scrollLeft -=
                        containerRect.left - elementRect.left
                } else if (elementRect.right > containerRect.right) {
                    // Element is out of view on the right side
                    scrollContainer.scrollLeft +=
                        elementRect.right - containerRect.right
                }
            }
        }
    }, [selectedFileId])

    const showSelectedTabSkeleton = false

    return (
        <div
            className={`flex justify-between bg-[#141414] items-center group ${className}`}
        >
            <CustomScrollbar innerRef={scrollContainerRef}>
                <div className="flex items-center justify-start no-scrollbar">
                    {false // Set to loading or false
                        ? Array.from({ length: 2 }).map((_, index) => (
                              <button
                                  key={index}
                                  className={`flex justify-center items-center px-4 py-[8px] text-sm border-t-[1.5px] ${
                                      showSelectedTabSkeleton && index === 0
                                          ? `border-t-primary rounded-t-sm bg-night border-b-[1px] border-b-night border-r-[1px] border-r-outlinecolor z-10`
                                          : 'border-r border-r-outlinecolor border-t-transparent'
                                  }`}
                              >
                                  <Skeleton
                                      key={index}
                                      className={`w-[68px] h-3 my-[3px] rounded-[3px] ${
                                          showSelectedTabSkeleton && index === 0
                                              ? 'bg-neutral-800'
                                              : 'bg-night'
                                      }`}
                                  />
                              </button>
                          ))
                        : files.map((file: File, index: number) => (
                              <button
                                  key={file.id}
                                  ref={el => {
                                      if (el) {
                                          fileRefs.current.set(file.id, el)
                                      } else {
                                          fileRefs.current.delete(file.id)
                                      }
                                  }}
                                  className={`flex justify-center items-center px-4 ${
                                      file.icon ? 'pr-5' : ''
                                  } py-[6px] text-sm border-t-[1.5px] ${
                                      file.id === selectedFileId
                                          ? `border-t-primary rounded-t-sm bg-night border-b-[1px] border-b-night ${
                                                index === 0
                                                    ? 'border-r-[1px] border-r-outlinecolor'
                                                    : 'border-r-[1px] border-x-outlinecolor'
                                            } z-10`
                                          : 'border-t-transparent border-r border-b'
                                  }`}
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
            </CustomScrollbar>
            {/* <div className="flex pr-3 h-full gap-2 items-center pb-1">
                {!isExpandedVariant && (
                    <ActionItem
                        active={false}
                        icon={
                            <Maximize className="h-[1.2rem] w-[1.2rem] text-gray-300" />
                        }
                        dialogContent={
                            <DialogContent className="h-full max-w-screen block p-0 mt-10 pt-10">
                                <EditorPanel
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
