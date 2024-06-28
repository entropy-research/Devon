import { cn } from '@/lib/utils'
import React, { forwardRef, useCallback, useRef, useState } from 'react'
import useResizeObserver from 'use-resize-observer'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Tree, Folder, File, TreeViewElement } from './tree-view-api'
import { Skeleton } from '@/components/ui/skeleton'
import * as AccordionPrimitive from '@radix-ui/react-accordion'
import { ChevronDown } from 'lucide-react'

interface TreeViewComponentProps extends React.HTMLAttributes<HTMLDivElement> {}

type TreeViewProps = {
    initialSelectedId?: string
    elements: TreeViewElement[]
    files: any[]
    selectedFileId: string | null
    setSelectedFileId: (id: string) => void
    indicator?: boolean
    loading?: boolean
    projectName?: string
} & (
    | {
          initialExpendedItems?: string[]
          expandAll?: false
      }
    | {
          initialExpendedItems?: undefined
          expandAll: true
      }
) &
    TreeViewComponentProps

const ACCORDION_ITEM_HEIGHT = 18

export const TreeView = ({
    files,
    selectedFileId,
    setSelectedFileId,
    elements,
    className,
    initialSelectedId,
    initialExpendedItems,
    expandAll,
    indicator = false,
    loading = false,
    projectName,
}: TreeViewProps) => {
    const containerRef = useRef<HTMLDivElement>(null)
    const [openItems, setOpenItems] = useState<string[]>(['1'])

    const { getVirtualItems, getTotalSize } = useVirtualizer({
        count: elements.length,
        getScrollElement: () => containerRef.current,
        estimateSize: useCallback(() => 40, []),
        overscan: 5,
    })

    const { height = getTotalSize(), width } = useResizeObserver({
        ref: containerRef,
    })

    return (
        <div
            ref={containerRef}
            id="tree-container-ref"
            className={cn(
                'rounded-md overflow-hidden py-1 relative h-full',
                className
            )}
        >
            <AccordionPrimitive.Root
                type="multiple"
                value={openItems}
                onValueChange={setOpenItems}
            >
                <AccordionPrimitive.Item value={'1'}>
                    <AccordionPrimitive.Trigger className="flex w-full">
                        {projectName && (
                            <span className="flex pl-1 pr-1 py-1 items-center w-full flex-1 truncate text-left">
                                <ChevronDown
                                    className={cn(
                                        'h-4 w-4 transition-transform duration-200 ease-in-out text-neutral-500 mr-[3px]',
                                        openItems.includes('1')
                                            ? ''
                                            : '-rotate-90'
                                    )}
                                />
                                <p className="uppercase text-xs font-semibold text-neutral-500 flex-1 truncate text-left">
                                    {projectName}
                                </p>
                            </span>
                        )}
                    </AccordionPrimitive.Trigger>
                    <AccordionPrimitive.Content className="text-sm data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down relative overflow-hidden h-full">
                        {loading ? (
                            <div
                                style={{ width }}
                                className="overflow-y-auto pt-2"
                            >
                                {Array.from({ length: 2 }).map((_, index) => (
                                    <div
                                        key={index}
                                        className="mb-3 flex gap-3 px-[12px] items-center"
                                    >
                                        <Skeleton className="w-4 h-4 rounded-[3px] bg-editor-night" />
                                        <Skeleton className="w-full h-3 rounded-[3px] flex-1 bg-editor-night" />
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <Tree
                                files={files}
                                selectedFileId={selectedFileId}
                                setSelectedFileId={setSelectedFileId}
                                initialSelectedId={initialSelectedId}
                                initialExpendedItems={initialExpendedItems}
                                elements={elements}
                                style={{
                                    height: height - ACCORDION_ITEM_HEIGHT,
                                    width,
                                }}
                                className="overflow-y-auto"
                                id="tree"
                            >
                                {getVirtualItems().map(element => (
                                    <TreeItem
                                        aria-label="Root"
                                        key={element.key}
                                        elements={[elements[element.index]]}
                                        indicator={indicator}
                                    />
                                ))}
                            </Tree>
                        )}
                    </AccordionPrimitive.Content>
                </AccordionPrimitive.Item>
            </AccordionPrimitive.Root>
        </div>
    )
}

TreeView.displayName = 'TreeView'

export const TreeItem = forwardRef<
    HTMLUListElement,
    {
        elements?: TreeViewElement[]
        indicator?: boolean
    } & React.HTMLAttributes<HTMLUListElement>
>(({ className, elements, indicator, ...props }, ref) => {
    return (
        <ul id="ul-ref" ref={ref} className="space-y-0 w-full" {...props}>
            {elements &&
                elements.map(element => (
                    <li key={element.id} className="w-full">
                        {element.children && element.children?.length > 0 ? (
                            <Folder
                                element={element.name}
                                value={element.id}
                                isSelectable={element.isSelectable}
                            >
                                <TreeItem
                                    key={element.id}
                                    aria-label={`folder ${element.name}`}
                                    elements={element.children}
                                    indicator={indicator}
                                />
                            </Folder>
                        ) : (
                            <File
                                value={element.id}
                                aria-label={`File ${element.name}`}
                                key={element.id}
                                isSelectable={element.isSelectable}
                                fileIcon={element.icon}
                            >
                                <p className="flex-1 truncate text-left">
                                    {element?.name}
                                </p>
                            </File>
                        )}
                    </li>
                ))}
        </ul>
    )
})

TreeItem.displayName = 'TreeItem'
