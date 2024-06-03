import React from 'react'
import { TreeView } from './tree-view'
import { useCodeEditorState } from '@/contexts/CodeEditorContext'

// const convertFilesToTreeViewElements = (files: any[]): TreeViewElement[] => {
//     return files.map(file => ({
//         id: file.id,
//         name: file.name,
//         children: file.children
//             ? convertFilesToTreeViewElements(file.children)
//             : [],
//     }))
// }

export default function FileTree() {
    const { files, selectedFileId } = useCodeEditorState()

    return (
        <TreeView
            elements={files}
            initialSelectedId={selectedFileId ?? undefined}
            indicator
        />
    )
}
