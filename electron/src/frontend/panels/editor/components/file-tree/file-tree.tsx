import { useEffect } from 'react'
import { TreeView } from './tree-view'
import { File } from '@/lib/types'
import { TreeViewElement } from './tree-view-api'
import { getRelativePath } from '@/lib/utils'

export default function FileTree({
    files,
    selectedFileId,
    setSelectedFileId,
    projectPath,
    initialLoading,
}: {
    files: File[]
    selectedFileId: string | null
    setSelectedFileId: (id: string) => void
    projectPath: string
    initialLoading: boolean
}) {
    const fileTree = buildFileTree(files, projectPath)

    useEffect(() => {}, [initialLoading])

    return (
        <TreeView
            files={files}
            selectedFileId={selectedFileId}
            setSelectedFileId={setSelectedFileId}
            elements={fileTree}
            initialSelectedId={selectedFileId ?? undefined}
            indicator
            loading={(!projectPath && files.length === 0) || initialLoading}
            projectName={projectPath ? projectPath.split('/').pop() : undefined}
        />
    )
}

const buildFileTree = (
    files: File[],
    projectPath: string
): TreeViewElement[] => {
    const tree: { [key: string]: any } = {}

    files.forEach(file => {
        const parts = getRelativePath(file.path, projectPath).split('/')
        let current = tree
        let currentPath = projectPath
        parts.forEach((part, index) => {
            currentPath = `${currentPath}/${part}`
            const isLastPart = index === parts.length - 1

            if (!current[part]) {
                // This part doesn't exist in the tree yet, so we create it
                current[part] = {
                    id: currentPath,
                    name: part,
                    children: isLastPart ? undefined : {},
                    icon: isLastPart ? file.icon : undefined,
                    isFolder: !isLastPart,
                }
            } else if (isLastPart) {
                // This is a file and the node already exists, update it
                current[part].icon = file.icon
                current[part].isFolder = false
                current[part].children = undefined
            } else if (!current[part].children) {
                // This is a folder that was previously added as a file, convert it to a folder
                current[part].children = {}
                current[part].isFolder = true
            }

            if (!isLastPart) {
                current = current[part].children!
            }
        })
    })

    const convertToArray = (obj: { [key: string]: any }): TreeViewElement[] => {
        return Object.keys(obj).map(key => {
            const item = obj[key]
            const children = item.children
                ? convertToArray(item.children)
                : undefined
            return {
                ...item,
                children,
            }
        })
    }

    return convertToArray(tree)
}
