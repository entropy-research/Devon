import { atom } from 'jotai'

export type CodeSnippet = {
    id: string
    fileName: string
    fullPath: string
    relativePath: string
    selection: string
    startLineNumber: number
    endLineNumber: number
    startColumn: number
    endColumn: number
    language: string
}

export const codeSnippetsAtom = atom<CodeSnippet[]>([])
