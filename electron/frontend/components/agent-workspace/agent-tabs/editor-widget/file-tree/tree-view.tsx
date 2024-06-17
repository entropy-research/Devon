'use client'

import { cn } from '@/lib/utils'
import React, { forwardRef, useCallback, useRef } from 'react'
import useResizeObserver from 'use-resize-observer'
import { useVirtualizer } from '@tanstack/react-virtual'
import {
    Tree,
    Folder,
    File,
    TreeViewElement,
} from './tree-view-api'
import { Icon } from '@iconify/react' // https://iconify.design/docs/icon-components/react/
import { Skeleton } from '@/components/ui/skeleton'

interface TreeViewComponentProps extends React.HTMLAttributes<HTMLDivElement> {}

type TreeViewProps = {
    initialSelectedId?: string
    elements: TreeViewElement[]
    files: any[]
    selectedFileId: string
    setSelectedFileId: (id: string) => void
    indicator?: boolean
    loading?: boolean
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
}: TreeViewProps) => {
    const containerRef = useRef<HTMLDivElement>(null)

    const { getVirtualItems, getTotalSize } = useVirtualizer({
        count: elements.length,
        getScrollElement: () => containerRef.current,
        estimateSize: useCallback(() => 40, []),
        overscan: 5,
    })

    const { height = getTotalSize(), width } = useResizeObserver({
        ref: containerRef,
    })

    if (loading) {
        return (
            <div
                ref={containerRef}
                id="tree-container-ref"
                className={cn(
                    'rounded-md overflow-hidden py-1 relative h-full',
                    className
                )}
            >
                <div style={{ width }} className="overflow-y-auto pt-2">
                    {Array.from({ length: 2 }).map((_, index) => (
                        <div
                            key={index}
                            className="mb-3 flex gap-3 px-[12px] items-center"
                        >
                            <Skeleton className="w-4 h-4 rounded-[3px] bg-night" />
                            <Skeleton className="w-full h-3 rounded-[3px] flex-1 bg-night" />
                        </div>
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div
            ref={containerRef}
            id="tree-container-ref"
            className={cn(
                'rounded-md overflow-hidden py-1 relative h-full',
                className
            )}
        >
            <Tree
                files={files}
                selectedFileId={selectedFileId}
                setSelectedFileId={setSelectedFileId}
                initialSelectedId={initialSelectedId}
                initialExpendedItems={initialExpendedItems}
                elements={elements}
                style={{ height, width }}
                className="h-full overflow-y-auto"
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
