import { useEffect, useState } from 'react';
import { fetchSessionState } from '@/lib/services/sessionService/sessionService';
import { File } from '@/lib/types';

const boilerplateFile = {
    id: 'main.py',
    name: 'main.py',
    path: 'main.py',
    language: 'python',
    value: {
        lines: `# Welcome to Devon!\n`,
    },
};

const boilerplateFile2 = {
    id: 'hello.py',
    name: 'hello.py',
    path: 'hello.py',
    language: 'python',
    value: {
        lines: `# Hello world!\n`,
    },
};

const useSessionFiles = (chatId) => {
    const [files, setFiles] = useState<File[]>([]);
    const [selectedFileId, setSelectedFileId] = useState<string>('');

    useEffect(() => {
        let intervalId;

        async function getSessionState() {
            try {
                const res = await fetchSessionState(chatId);
                if (!res || !res.editor || !res.editor.files) return;
                const editor = res.editor;
                const f = editor.files;
                const _files: File[] = [];

                for (let key in f) {
                    if (f.hasOwnProperty(key)) {
                        _files.push({
                            id: key,
                            name: key.split('/').pop() ?? 'unnamed_file',
                            path: key,
                            language: 'python',
                            value: f[key],
                        });
                    }
                }
                if (_files.length === 0) {
                    _files.push(boilerplateFile);
                    _files.push(boilerplateFile2);
                }
                setFiles(_files);
                if (!selectedFileId || !_files.find(f => f.id === selectedFileId)) {
                    setSelectedFileId(_files[0].id);
                }
            } catch (error) {
                console.error('Error fetching session state:', error);
            }
        }

        getSessionState();
        intervalId = setInterval(getSessionState, 2000);
        return () => clearInterval(intervalId);
    }, [chatId, selectedFileId]);

    return { files, selectedFileId, setSelectedFileId };
};

export default useSessionFiles;
