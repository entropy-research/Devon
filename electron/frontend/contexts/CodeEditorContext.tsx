import { createContext, useContext, useState, useEffect } from 'react'
import useSessionFiles from '@/lib/services/sessionService/useSessionFiles'
import { File } from '@/lib/types'

const context: {
    files: File[]
    selectedFileId: string
    setSelectedFileId: (value: string) => void
} = {
    files: [],
    selectedFileId: '',
    setSelectedFileId: value => {},
}

const CodeEditorContext = createContext(context)

export const CodeEditorContextProvider = ({ children, chatId }) => {
    const { files, selectedFileId, setSelectedFileId } = useSessionFiles(chatId)

    useEffect(() => {
        if (files.length === 0) {
            setSelectedFileId('')
            return
        }
        if (!selectedFileId && files.length > 0) {
            setSelectedFileId(files[0].id)
        }
    }, [selectedFileId, files])

    return (
        <CodeEditorContext.Provider
            value={{
                files,
                selectedFileId,
                setSelectedFileId,
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
