import React, { createContext, useContext, useState, useEffect } from 'react'

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
    const [file, setFile] = useState(files.length > 0 ? files[0] : null)
    const [selectedFileId, setSelectedFileId] = useState(file?.id)
    const [diffEnabled, setDiffEnabled] = useState(false)

    useEffect(() => {
        setFiles(tabFiles)
        setFile(tabFiles.length > 0 ? tabFiles[0] : null)
        setSelectedFileId(file?.id) 
    }, [file?.id, tabFiles])
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
