import React from 'react'
import { TreeView } from './tree-view'

export default function FileTree({ files, selectedFileId, setSelectedFileId }: { files: any[]; selectedFileId: string; setSelectedFileId: (id: string) => void }) {

    return (
        <TreeView
            files={files}
            selectedFileId={selectedFileId}
            setSelectedFileId={setSelectedFileId}
            elements={files}
            initialSelectedId={selectedFileId ?? undefined}
            indicator
        />
    )
}
