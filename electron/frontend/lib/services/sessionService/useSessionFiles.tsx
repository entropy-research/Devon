import { useEffect, useState } from 'react'
import { useBackendUrl } from '@/contexts/BackendUrlContext'
import { File } from '@/lib/types'

import axios from 'axios'
import { SessionMachineContext } from '@/app/home'


export const fetchSessionState = async (backendUrl, sessionId) => {
    if (!backendUrl || !sessionId) {
        return null
    }
    const { data } = await axios.get(
        `${backendUrl}/sessions/${encodeURIComponent(sessionId)}/state`
    )
    return data
}

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

    const res = SessionMachineContext.useSelector(state => state.context.sessionState)

    const [files, setFiles] = useState<File[]>([])
    const [selectedFileId, setSelectedFileId] = useState<string>('')

    // if (!res || !res.editor || !res.editor.files) return
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

export default useSessionFiles
