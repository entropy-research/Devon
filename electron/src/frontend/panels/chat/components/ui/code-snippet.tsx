import { memo } from 'react'
import { SimpleCodeBlock } from '@/components/ui/codeblock'
import { X } from 'lucide-react'
import { atom } from 'jotai'

export type ICodeSnippet = {
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

export const codeSnippetsAtom = atom<ICodeSnippet[]>([])

const CodeSnippet = ({
    snippets,
    onClose,
    onClickHeader,
}: {
    snippets: ICodeSnippet[]
    onClose: (id: string) => void
    onClickHeader: (snippet: ICodeSnippet) => void
}) => {
    return (
        <div className="flex flex-wrap gap-2 mt-0 pb-3 bg-night">
            {snippets.map(snippet => (
                <div
                    key={snippet.id}
                    className="bg-batman rounded-md text-white relative max-w-xs"
                >
                    <pre className="text-sm flex h-full">
                        <SimpleCodeBlock
                            key={snippet.id}
                            language={snippet.language}
                            value={snippet.selection}
                            fileName={snippet.fileName}
                            subtext={snippet.startLineNumber === snippet.endLineNumber ? `(Line ${snippet.startLineNumber})` : `(Lines ${snippet.startLineNumber} to ${snippet.endLineNumber})`}
                            onClickHeader={() => onClickHeader(snippet)}
                        />
                    </pre>
                    <button className="z-10 absolute top-1 right-1 text-neutral-500 hover:text-white cursor-pointer p-1 transition-colors duration-300 ease-in-out bg-zinc-800">
                        <X
                            onClick={() => onClose(snippet.id)}
                            size={14}
                        />
                    </button>
                </div>
            ))}
        </div>
    )
}

const areEqual = (prevProps: any, nextProps: any) => {
    // Compare the snippets array and the onClose function
    return (
        prevProps.snippets === nextProps.snippets &&
        prevProps.onClose === nextProps.onClose
    )
}

export default memo(CodeSnippet, areEqual)
