import { useRef, useEffect, useState, useMemo } from 'react'
import { Maximize, FileDiff, X, Bot } from 'lucide-react'
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
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip'

interface CustomScrollbarProps {
    children: ReactNode
    innerRef?: React.RefObject<HTMLDivElement>
}

const CustomScrollbar: React.FC<CustomScrollbarProps> = ({
    children,
    innerRef,
}) => {
    return (
        <div ref={innerRef} className="horizontal-scrollbar overflow-x-auto">
            {children}
        </div>
    )
}

// The file tabs at the top of the editor panel. Also used in the shell panel
const FileTabs = ({
    files,
    selectedFileId,
    setSelectedFileId,
    onCloseTab,
    className,
    isExpandedVariant,
    loading = false,
    initialFiles,
}: {
    files: any[]
    selectedFileId: string | null
    setSelectedFileId: (id: string) => void
    onCloseTab: (id: string) => void
    className?: string
    isExpandedVariant: boolean
    loading?: boolean
    initialFiles: File[]
}) => {
    const fileRefs = useRef(new Map<string, HTMLButtonElement>())
    const scrollContainerRef = useRef<HTMLDivElement>(null)
    const [hoveredFileId, setHoveredFileId] = useState<string | null>(null)

    const scrollIntoView = (fileId: string) => {
        if (fileId && fileRefs.current.has(fileId)) {
            const fileElement = fileRefs.current.get(fileId)
            const scrollContainer = scrollContainerRef.current
            if (fileElement && scrollContainer) {
                const elementRect = fileElement.getBoundingClientRect()
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
    }

    const fileMatchMap = useMemo(() => {
        const map = new Map<string, File>()
        initialFiles.forEach(file => {
            map.set(file.id, file)
        })
        return map
    }, [initialFiles])

    const getFileMatch = useMemo(
        () => (fileId: string) => {
            return fileMatchMap.get(fileId)
        },
        [fileMatchMap]
    )

    useEffect(() => {
        if (selectedFileId) scrollIntoView(selectedFileId)
    }, [selectedFileId, files])

    const showSelectedTabSkeleton = false
    const showCloseWhenAgentHasOpen = false

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
                              <div
                                  key={file.id}
                                  className="relative"
                                  onMouseEnter={() => setHoveredFileId(file.id)}
                                  onMouseLeave={() => setHoveredFileId(null)}
                              >
                                  <button
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
                                      } group relative cursor-pointer w-full text-left ${
                                          file.id === selectedFileId
                                              ? ''
                                              : 'smooth-hover-2'
                                      }`}
                                      onClick={() => setSelectedFileId(file.id)}
                                  >
                                      {file.icon && (
                                          <Icon
                                              icon={file.icon}
                                              className="h-4 w-4 mr-2"
                                          />
                                      )}
                                      <span
                                          className={`mr-5 flex items-center ${
                                              file.id === selectedFileId
                                                  ? 'opacity-100'
                                                  : 'opacity-70'
                                          }`}
                                      >
                                          {file.name}
                                          {file.agentHasOpen}
                                          {getFileMatch(file.id)
                                              ?.agentHasOpen && (
                                              <TooltipProvider
                                                  delayDuration={100}
                                              >
                                                  <Tooltip>
                                                      <TooltipTrigger asChild>
                                                          <span className="inline-flex items-center">
                                                              <Bot
                                                                  className={`h-[16px] w-[16px] text-primary ${
                                                                      showCloseWhenAgentHasOpen
                                                                          ? 'ml-2 -mr-3'
                                                                          : 'ml-3 -mr-6'
                                                                  } -translate-y-[1px]`}
                                                              />
                                                          </span>
                                                      </TooltipTrigger>
                                                      <TooltipContent>
                                                          {/* Devon made changes to this file */}
                                                          Devon has this file
                                                          open
                                                      </TooltipContent>
                                                  </Tooltip>
                                              </TooltipProvider>
                                          )}
                                      </span>
                                  </button>
                                  {showCloseWhenAgentHasOpen ? (
                                      <CloseButton
                                          isSelected={
                                              file.id === selectedFileId
                                          }
                                          isHovered={file.id === hoveredFileId}
                                          onClick={() => onCloseTab(file.id)}
                                          fileName={file.name}
                                      />
                                  ) : (
                                      !getFileMatch(file.id) && (
                                          <CloseButton
                                              isSelected={
                                                  file.id === selectedFileId
                                              }
                                              isHovered={
                                                  file.id === hoveredFileId
                                              }
                                              onClick={() =>
                                                  onCloseTab(file.id)
                                              }
                                              fileName={file.name}
                                          />
                                      )
                                  )}
                              </div>
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

const CloseButton = ({
    isSelected,
    isHovered,
    onClick,
    fileName,
}: {
    isSelected: boolean
    isHovered: boolean
    onClick: () => void
    fileName: string
}) => {
    return (
        <button
            className={`absolute right-[5px] top-1/2 transform -translate-y-1/2 opacity-0 transition-opacity p-1 rounded-md smooth-hover z-10 ${
                isSelected || isHovered ? 'opacity-100' : ''
            }`}
            onClick={e => {
                e.stopPropagation()
                onClick()
            }}
            aria-label={`Close ${fileName}`}
        >
            <X
                className={`h-4 w-4 ${
                    isSelected ? 'text-white' : 'text-neutral-400'
                }`}
            />
        </button>
    )
}

export default FileTabs
