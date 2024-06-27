import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import * as AccordionPrimitive from '@radix-ui/react-accordion'
import { FileIcon } from 'lucide-react'
import React, {
    createContext,
    forwardRef,
    useCallback,
    useContext,
    useEffect,
    useState,
} from 'react'
import { Button } from '@/components/ui/button'
import { Icon } from '@iconify/react'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip'

type TreeViewElement = {
    id: string
    name: string
    isSelectable?: boolean
    children?: TreeViewElement[]
    icon?: string
}

type TreeContextProps = {
    selectedId: string | undefined
    expendedItems: string[] | undefined
    indicator: boolean
    handleExpand: (id: string) => void
    selectItem: (id: string) => void
    setExpendedItems?: React.Dispatch<
        React.SetStateAction<string[] | undefined>
    >
    openIcon?: React.ReactNode
    closeIcon?: React.ReactNode
    direction: 'rtl' | 'ltr'
}

const TreeContext = createContext<TreeContextProps | null>(null)

const useTree = () => {
    const context = useContext(TreeContext)
    if (!context) {
        throw new Error('useTree must be used within a TreeProvider')
    }
    return context
}

interface TreeViewComponentProps extends React.HTMLAttributes<HTMLDivElement> {}

type Direction = 'rtl' | 'ltr' | undefined

type TreeViewProps = {
    files: any[]
    selectedFileId: string | null
    setSelectedFileId: (id: string) => void
    initialSelectedId?: string
    indicator?: boolean
    elements?: TreeViewElement[]
    initialExpendedItems?: string[]
    openIcon?: React.ReactNode
    closeIcon?: React.ReactNode
} & TreeViewComponentProps

const Tree = forwardRef<HTMLDivElement, TreeViewProps>(
    (
        {
            className,
            files,
            selectedFileId,
            setSelectedFileId,
            elements,
            initialSelectedId,
            initialExpendedItems,
            children,
            indicator = true,
            openIcon,
            closeIcon,
            dir,
            ...props
        },
        ref
    ) => {
        const [expendedItems, setExpendedItems] = useState<
            string[] | undefined
        >(initialExpendedItems)

        const selectItem = useCallback(
            (id: string) => {
                const findFileById = (
                    files: any[],
                    id: string
                ): any | undefined => {
                    for (const file of files) {
                        if (file.id === id) {
                            return file
                        }
                        if (file.children) {
                            const found = findFileById(file.children, id)
                            if (found) {
                                return found
                            }
                        }
                    }
                    return undefined
                }
                setSelectedFileId(id)
            },
            [setSelectedFileId]
        )

        const handleExpand = useCallback((id: string) => {
            setExpendedItems(prev => {
                if (prev?.includes(id)) {
                    return prev.filter(item => item !== id)
                }
                return [...(prev ?? []), id]
            })
        }, [])

        const expandSpecificTargetedElements = useCallback(
            (elements?: TreeViewElement[], selectId?: string) => {
                if (!elements || !selectId) return
                const findParent = (
                    currentElement: TreeViewElement,
                    currentPath: string[] = []
                ) => {
                    const isSelectable = currentElement.isSelectable ?? true
                    const newPath = [...currentPath, currentElement.id]
                    if (currentElement.id === selectId) {
                        if (isSelectable) {
                            setExpendedItems(prev => [
                                ...(prev ?? []),
                                ...newPath,
                            ])
                        } else {
                            if (newPath.includes(currentElement.id)) {
                                newPath.pop()
                                setExpendedItems(prev => [
                                    ...(prev ?? []),
                                    ...newPath,
                                ])
                            }
                        }
                        return
                    }
                    if (
                        isSelectable &&
                        currentElement.children &&
                        currentElement.children.length > 0
                    ) {
                        currentElement.children.forEach(child => {
                            findParent(child, newPath)
                        })
                    }
                }
                elements.forEach(element => {
                    findParent(element)
                })
            },
            []
        )

        // Uncommenting this will make it so the folder has to be open if a selected item is in the dir
        // useEffect(() => {
        //     if (initialSelectedId) {
        //         expandSpecificTargetedElements(elements, initialSelectedId)
        //     }
        // }, [initialSelectedId, elements])

        const direction = dir === 'rtl' ? 'rtl' : 'ltr'

        return (
            <TreeContext.Provider
                value={{
                    selectedId: selectedFileId ?? undefined,
                    expendedItems,
                    handleExpand,
                    selectItem,
                    setExpendedItems,
                    indicator,
                    openIcon,
                    closeIcon,
                    direction,
                }}
            >
                <div className={cn('size-full', className)}>
                    <ScrollArea
                        id="tree-scroll-area"
                        ref={ref}
                        className="h-full relative pl-1"
                        dir={dir as Direction}
                    >
                        <AccordionPrimitive.Root
                            {...props}
                            type="multiple"
                            defaultValue={expendedItems}
                            value={expendedItems}
                            className="flex flex-col"
                            onValueChange={value =>
                                setExpendedItems(prev => [
                                    ...(prev ?? []),
                                    value[0],
                                ])
                            }
                            dir={dir as Direction}
                        >
                            {children}
                        </AccordionPrimitive.Root>
                    </ScrollArea>
                </div>
            </TreeContext.Provider>
        )
    }
)

Tree.displayName = 'Tree'

const TreeIndicator = forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
    const { direction } = useTree()

    return (
        <div
            dir={direction}
            ref={ref}
            className={cn(
                'h-full w-px bg-batman absolute left-4 rtl:right-1.5 py-3 rounded-md hover:bg-slate-300 duration-300 ease-in-out',
                className
            )}
            {...props}
        />
    )
})

TreeIndicator.displayName = 'TreeIndicator'

interface FolderComponentProps
    extends React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item> {}

type FolderProps = {
    expendedItems?: string[]
    element: string
    isSelectable?: boolean
    isSelect?: boolean
} & FolderComponentProps

const Folder = forwardRef<
    HTMLDivElement,
    FolderProps & React.HTMLAttributes<HTMLDivElement>
>(
    (
        {
            className,
            element,
            value,
            isSelectable = true,
            isSelect,
            children,
            ...props
        },
        ref
    ) => {
        const {
            direction,
            handleExpand,
            expendedItems,
            indicator,
            setExpendedItems,
            openIcon,
            closeIcon,
        } = useTree()

        return (
            <AccordionPrimitive.Item
                {...props}
                value={value}
                className="relative overflow-hidden h-full"
            >
                {/* <TooltipProvider delayDuration={1500}>
                    <Tooltip>
                        <TooltipTrigger asChild> */}
                <AccordionPrimitive.Trigger
                    className={cn(
                        `flex items-center cursor-pointer text-sm pr-1 rtl:pl-1 rtl:pr-0 duration-200 ease-in-out w-full rounded-xs py-1 px-2 hover:bg-batman toned-text-color`,
                        {
                            'bg-editor-night': isSelect && isSelectable,
                            'cursor-pointer': isSelectable,
                            'cursor-not-allowed opacity-50': !isSelectable,
                        },
                        className
                    )}
                    disabled={!isSelectable}
                    onClick={() => handleExpand(value)}
                >
                    {expendedItems?.includes(value)
                        ? openIcon ?? (
                              <Icon
                                  icon="vscode-icons:default-folder-opened"
                                  className="h-4 w-4 mr-2 ml-[2px]"
                              />
                          )
                        : closeIcon ?? (
                              <Icon
                                  icon="vscode-icons:default-folder"
                                  className="h-4 w-4 mr-2 ml-[2px]"
                              />
                          )}
                    <span className="flex-1 truncate text-left">{element}</span>
                </AccordionPrimitive.Trigger>
                {/* </TooltipTrigger>
                        <TooltipContent side="right" align="end">
                            <p>{value}</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider> */}

                <AccordionPrimitive.Content className="text-sm data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down relative overflow-hidden h-full">
                    {element && indicator && (
                        <TreeIndicator aria-hidden="true" />
                    )}
                    <AccordionPrimitive.Root
                        dir={direction}
                        type="multiple"
                        className="flex flex-col gap-1 py-1 ml-5 rtl:mr-5 "
                        defaultValue={expendedItems}
                        value={expendedItems}
                        onValueChange={value => {
                            setExpendedItems?.(prev => [
                                ...(prev ?? []),
                                value[0],
                            ])
                        }}
                    >
                        {children}
                    </AccordionPrimitive.Root>
                </AccordionPrimitive.Content>
            </AccordionPrimitive.Item>
        )
    }
)

Folder.displayName = 'Folder'

const File = forwardRef<
    HTMLButtonElement,
    {
        value: string
        handleSelect?: (id: string) => void
        isSelectable?: boolean
        isSelect?: boolean
        fileIcon?: string
    } & React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>
>(
    (
        {
            value,
            className,
            handleSelect,
            isSelectable = true,
            isSelect,
            fileIcon,
            children,
            ...props
        },
        ref
    ) => {
        const { direction, selectedId, selectItem } = useTree()
        const isSelected = isSelect ?? selectedId === value
        return (
            <AccordionPrimitive.Item value={value} className="relative w-full">
                <TooltipProvider delayDuration={1500}>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <AccordionPrimitive.Trigger
                                ref={ref}
                                {...props}
                                dir={direction}
                                disabled={!isSelectable}
                                aria-label="File"
                                className={cn(
                                    'flex items-center cursor-pointer text-sm pr-1 rtl:pl-1 rtl:pr-0 duration-200 ease-in-out w-full rounded-xs py-1 px-2 hover:bg-batman toned-text-color',
                                    {
                                        'bg-editor-night': isSelected && isSelectable,
                                    },
                                    isSelectable
                                        ? 'cursor-pointer'
                                        : 'opacity-50 cursor-not-allowed',
                                    className
                                )}
                                onClick={() => selectItem(value)}
                            >
                                {fileIcon ? (
                                    <Icon
                                        icon={fileIcon}
                                        className="h-4 w-4 ml-[2px] mr-2"
                                    />
                                ) : (
                                    <FileIcon className="h-4 w-4 ml-[2px] mr-2 text-gray-300" />
                                )}
                                {children}
                                {isSelected && (
                                    <span className="absolute top-0 left-0 h-full w-[1.5px] bg-primary" />
                                )}
                            </AccordionPrimitive.Trigger>
                        </TooltipTrigger>
                        <TooltipContent side="right" align="end">
                            <p>{value}</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </AccordionPrimitive.Item>
        )
    }
)

File.displayName = 'File'

const CollapseButton = forwardRef<
    HTMLButtonElement,
    {
        elements: TreeViewElement[]
        expandAll?: boolean
    } & React.HTMLAttributes<HTMLButtonElement>
>(({ className, elements, expandAll = false, children, ...props }, ref) => {
    const { expendedItems, setExpendedItems } = useTree()

    const expendAllTree = useCallback(
        (elements: TreeViewElement[]) => {
            const expandTree = (element: TreeViewElement) => {
                const isSelectable = element.isSelectable ?? true
                if (
                    isSelectable &&
                    element.children &&
                    element.children.length > 0
                ) {
                    setExpendedItems?.(prev => [...(prev ?? []), element.id])
                    element.children.forEach(expandTree)
                }
            }

            elements.forEach(expandTree)
        },
        [setExpendedItems]
    )

    const closeAll = useCallback(() => {
        setExpendedItems?.([])
    }, [setExpendedItems])

    useEffect(() => {
        if (expandAll) {
            expendAllTree(elements)
        }
    }, [elements, expandAll, expendAllTree])

    return (
        <Button
            variant={'ghost'}
            className="h-8 w-fit p-1 absolute bottom-1 right-2"
            onClick={
                expendedItems && expendedItems.length > 0
                    ? closeAll
                    : () => expendAllTree(elements)
            }
            ref={ref}
            {...props}
        >
            {children}
            <span className="sr-only">Toggle</span>
        </Button>
    )
})

CollapseButton.displayName = 'CollapseButton'

export { Tree, Folder, File, CollapseButton, type TreeViewElement }
