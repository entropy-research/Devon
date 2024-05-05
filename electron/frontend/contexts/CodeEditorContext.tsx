import React, { createContext, useContext, useState } from 'react'

const CodeEditorContext = createContext({
    files: [],
    file: null,
    setFile: value => {},
    selectedFileId: null,
    setSelectedFileId: value => {},
    diffEnabled: false,
    setDiffEnabled: value => {},
})

export const CodeEditorContextProvider = ({ children, tabFiles }) => {
    const [files, setFiles] = useState(tabFiles)
    const [file, setFile] = useState(files[0])
    const [selectedFileId, setSelectedFileId] = useState(file.id)
    const [diffEnabled, setDiffEnabled] = useState(false)

    return (
        <CodeEditorContext.Provider
            value={{
                files,
                file,
                setFile,
                selectedFileId,
                setSelectedFileId,
                diffEnabled,
                setDiffEnabled,
            }}
        >
            {children}
        </CodeEditorContext.Provider>
    )
}

export const useCodeEditorState = () => {
    const context = useContext(CodeEditorContext)
    if (context === undefined) {
        throw new Error(
            'useCodeEditorState must be used within a CodeEditorContextProvider'
        )
    }
    return context
}
