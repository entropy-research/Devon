import React, { useEffect } from 'react';
import { TreeView } from './tree-view';
import { useCodeEditorState } from '@/contexts/CodeEditorContext';

export default function FileTree() {
    const {
        files,
        selectedFileId,
        setSelectedFileId,
        setFile,
    } = useCodeEditorState();

    const elements = files.map((file: any) => ({
        id: file.id,
        name: file.name,
        children: file.children || [],
    }));

    const handleSelect = (id: string) => {
        setSelectedFileId(id);
        const file = findFileById(files, id);
        if (file) {
            setFile(file);
        }
    };

    const findFileById = (files: any[], id: string): any | undefined => {
        for (const file of files) {
            if (file.id === id) {
                return file;
            }
            if (file.children) {
                const found = findFileById(file.children, id);
                if (found) {
                    return found;
                }
            }
        }
        return undefined;
    };

    useEffect(() => {
        if (selectedFileId) {
            handleSelect(selectedFileId);
        }
    }, [selectedFileId]);

    return (
        <TreeView
            elements={elements}
            initialSelectedId={selectedFileId}
            initialExpendedItems={['1', '2']}
            onSelect={handleSelect}
        />
    );
}
