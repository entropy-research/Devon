'use client'

import { cn } from '@/lib/utils'
import React, { forwardRef, useCallback, useRef } from 'react'
import useResizeObserver from 'use-resize-observer'
import { useVirtualizer } from '@tanstack/react-virtual'
import {
    Tree,
    Folder,
    File,
    CollapseButton,
    TreeViewElement,
} from './tree-view-api'

interface TreeViewComponentProps extends React.HTMLAttributes<HTMLDivElement> {}

type TreeViewProps = {
    initialSelectedId?: string
    elements: TreeViewElement[]
    indicator?: boolean
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
    elements,
    className,
    initialSelectedId,
    initialExpendedItems,
    expandAll,
    indicator = false,
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
                initialSelectedId={initialSelectedId}
                initialExpendedItems={initialExpendedItems}
                elements={elements}
                // style={{ height, width }}
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
                {/* <CollapseButton elements={elements} expandAll={expandAll}>
          <span>Expand All</span>
        </CollapseButton> */}
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
                            >
                                <p className="truncate">{element?.name}</p>
                            </File>
                        )}
                    </li>
                ))}
        </ul>
    )
})

TreeItem.displayName = 'TreeItem'
