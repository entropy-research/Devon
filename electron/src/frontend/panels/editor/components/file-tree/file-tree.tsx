import { TreeView } from './tree-view'
import { File } from '@/lib/types'
import { TreeViewElement } from './tree-view-api'
export default function FileTree({
    files,
    selectedFileId,
    setSelectedFileId,
    projectPath,
}: {
    files: File[]
    selectedFileId: string
    setSelectedFileId: (id: string) => void
    projectPath: string
}) {
    const fileTree = buildFileTree(files, projectPath)

    return (
        <TreeView
            files={files}
            selectedFileId={selectedFileId}
            setSelectedFileId={setSelectedFileId}
            elements={fileTree}
            initialSelectedId={selectedFileId ?? undefined}
            indicator
            loading={!projectPath && files.length === 0}
            projectName={projectPath ? projectPath.split('/').pop() : undefined}
        />
    )
}

const buildFileTree = (
    files: File[],
    projectPath: string
): TreeViewElement[] => {
    const tree: { [key: string]: any } = {}
    function addTrailingSlash(str: string) {
        if (!str.endsWith('/')) {
            return str + '/'
        }
        return str
    }

    files.forEach(file => {
        const relativePath = file.path.replace(
            addTrailingSlash(projectPath),
            ''
        )
        const parts = relativePath.split('/')
        let current = tree

        parts.forEach((part, index) => {
            if (!current[part]) {
                current[part] = {
                    id: file.path,
                    name: part,
                    children: index === parts.length - 1 ? null : {},
                    icon: index === parts.length - 1 ? file.icon : undefined,
                }
            }
            current = current[part].children || {}
        })

        current.__fileData = file // Store the original file data
    })

    const convertToArray = (obj: { [key: string]: any }): TreeViewElement[] => {
        return Object.keys(obj).map(key => {
            const children = obj[key].children
                ? convertToArray(obj[key].children)
                : []
            return {
                ...obj[key],
                children: children.length > 0 ? children : undefined,
            }
        })
    }

    return convertToArray(tree)
}
