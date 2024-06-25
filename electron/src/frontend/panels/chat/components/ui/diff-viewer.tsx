import React from 'react'
import { Diff, Hunk } from 'react-diff-view'
import 'react-diff-view/style/index.css'

interface DiffViewerProps {
    files: any[] // We'll need to define a more specific type later
}

const DiffViewer: React.FC<DiffViewerProps> = ({ files }) => {
    return (
        <>
            {files.map(file => (
                <Diff
                    key={file.oldRevision + '-' + file.newRevision}
                    viewType="unified"
                    diffType={file.type}
                    hunks={file.hunks}
                    gutterType="none"
                >
                    {hunks =>
                        hunks.map(hunk => (
                            <Hunk key={hunk.content} hunk={hunk} />
                        ))
                    }
                </Diff>
            ))}
        </>
    )
}

export default DiffViewer
