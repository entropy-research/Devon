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
    const [file, setFile] = useState(tabFiles.length > 0 ? tabFiles[0] : null)
    const [selectedFileId, setSelectedFileId] = useState(
        tabFiles.length > 0 ? tabFiles[0].id : null
    )
    const [diffEnabled, setDiffEnabled] = useState(false)

    useEffect(() => {
        if (tabFiles.length === 0) {
            setFile(null)
            setSelectedFileId(null)
            return
        }
        setFiles(tabFiles)
        if (!file) {
            setFile(tabFiles[0])
        }
        if (!selectedFileId && tabFiles.length > 0) {
            setSelectedFileId(tabFiles[0].id)
        }
    }, [file, selectedFileId, tabFiles])

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
