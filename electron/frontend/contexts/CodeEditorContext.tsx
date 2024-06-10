import { createContext, useContext, useState, useEffect } from 'react'
// import useSessionFiles from '@/lib/services/sessionService/useSessionFiles'
import { File } from '@/lib/types'
import { SessionMachineContext } from '@/app/home'


const boilerplateFile = {
    id: 'main.py',
    name: 'main.py',
    path: 'main.py',
    language: 'python',
    value: {
        lines: `# Welcome to Devon!\n`,
    },
}

const boilerplateFile2 = {
    id: 'hello.py',
    name: 'hello.py',
    path: 'hello.py',
    language: 'python',
    value: {
        lines: `# Hello world!\n`,
    },
}

const useSessionFiles = chatId => {

    // const res = SessionMachineContext.useSelector(state => state.context.sessionState)
    // const res = {
    //     editor: {
    //         files: {}
    //     }
    // }
    let res = {
        editor: {
            files: {}
        }
    }

    const [files, setFiles] = useState<File[]>([])
    const [selectedFileId, setSelectedFileId] = useState<string>('')

    if (!res || !res.editor || !res.editor.files) return {
        files: [],
        selectedFileId: '',
        setSelectedFileId: () => { },
    }
    const editor = res.editor
    const f = editor.files
    const _files: File[] = []

    for (let key in f) {
        if (f.hasOwnProperty(key)) {
            _files.push({
                id: key,
                name: key.split('/').pop() ?? 'unnamed_file',
                path: key,
                language: 'python',
                value: f[key],
            })
        }
    }
    if (_files.length === 0) {
        _files.push(boilerplateFile)
        _files.push(boilerplateFile2)
    }
    setFiles(_files)
    if (
        !selectedFileId ||
        !_files.find(f => f.id === selectedFileId)
    ) {
        setSelectedFileId(_files[0].id)
    }


    return { files, selectedFileId, setSelectedFileId }
}



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
    // const { files, selectedFileId, setSelectedFileId } = useSessionFiles(chatId)
    const res = SessionMachineContext.useSelector(state => state.context.sessionState)

    const [files, setFiles] = useState<File[]>([])
    const [selectedFileId, setSelectedFileId] = useState<string>('')




    if (!res || !res.editor || !res.editor.files) {
        setFiles([])
        setSelectedFileId('')
    } else {
        const editor = res.editor
        const f = editor.files
    const _files: File[] = []

    for (let key in f) {
        if (f.hasOwnProperty(key)) {
            _files.push({
                id: key,
                name: key.split('/').pop() ?? 'unnamed_file',
                path: key,
                language: 'python',
                value: f[key],
            })
        }
    }
    if (_files.length === 0) {
        _files.push(boilerplateFile)
        _files.push(boilerplateFile2)
    }
    setFiles(_files)
    if (
        !selectedFileId ||
        !_files.find(f => f.id === selectedFileId)
    ) {
        setSelectedFileId(_files[0].id)
    }
}



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

// export const useCodeEditorState = () => {
//     const context = useContext(CodeEditorContext)
//     if (context === undefined) {
//         throw new Error(
//             'useCodeEditorState must be used within a CodeEditorContextProvider'
//         )
//     }
//     return context
// }
