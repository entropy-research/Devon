import React from 'react'
import { TreeView } from './tree-view'
import { useCodeEditorState } from '@/contexts/CodeEditorContext'

export default function FileTree() {
    const { files, selectedFileId } = useCodeEditorState()
    return (
        <TreeView
            elements={files}
            initialSelectedId={selectedFileId ?? undefined}
            indicator
            loading={files.length === 0}
        />
    )
}
