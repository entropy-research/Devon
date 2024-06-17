import Editor, { Monaco } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import FileTabs from '@/components/file-tabs/file-tabs'
import { useSearchParams } from 'next/navigation'
import { useState } from 'react'
import { SessionMachineContext } from '@/app/home'
import { Skeleton } from '@/components/ui/skeleton'

// Source: https://github.com/OpenDevin/OpenDevin/blob/main/frontend/src/components/CodeEditor.tsx
export default function CodeEditor({
    isExpandedVariant = false,
    showEditorBorders,
    path,
}: {
    isExpandedVariant?: boolean
    showEditorBorders: boolean
    path: string
}): JSX.Element {
    const searchParams = useSearchParams()
    // const chatId = searchParams.get('chat')

    const [selectedFileId, setSelectedFileId] = useState<string | null>(null)

    let files = SessionMachineContext.useSelector(
        state => {
            if (state.context.sessionState?.editor && state.context.sessionState.editor.files) {
                return Object.keys(state.context.sessionState.editor.files).map(filename => ({
                    id: filename,
                    name: filename.split('/').pop() ?? 'unnamed_file',
                    path: filename,
                    language: 'python',
                    value: state.context.sessionState.editor.files[filename],
                }))
            } else {
                return []
            }
        }
    )

    const handleEditorDidMount = (
        editor: editor.IStandaloneCodeEditor,
        monaco: Monaco
    ) => {
        monaco.editor.defineTheme('theme', {
            base: 'vs-dark',
            inherit: true,
            rules: [],
            colors: {
                // 'editor.background': bgColor,
            },
        })

        monaco.editor.setTheme('theme')
    }

    const bgColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--bg-workspace')
        .trim()

    // if (isExpandedVariant) {
    //     return (
    //         <div className="w-full bg-workspace rounded-b-lg overflow-hidden">
    //             <BothEditorTypes
    //                 file={files?.find(f => f.id === selectedFileId)}
    //                 handleEditorDidMount={handleEditorDidMount}
    //             />
    //         </div>
    //     )
    // }

    return (
        <div className="flex flex-col w-full h-full">
            <FileTabs
                files={files}
                selectedFileId={selectedFileId ?? files[0]?.id}
                setSelectedFileId={setSelectedFileId}
                // chatId={chatId}
                className={showEditorBorders ? '' : ''}
                isExpandedVariant={isExpandedVariant}
                loading={files.length === 0}
            />
            {<PathDisplay path={path} loading={files.length === 0} />}
            <div className="flex w-full h-full bg-night rounded-b-lg mt-[-2px]">
                {selectedFileId && (
                    <BothEditorTypes
                        file={files?.find(f => f.id === selectedFileId)}
                        handleEditorDidMount={handleEditorDidMount}
                    />
                )}
            </div>
        </div>
    )
}

const BothEditorTypes = ({ file, handleEditorDidMount }) =>
(
    <Editor
        className="h-full"
        theme="vs-dark"
        defaultLanguage={'python'}
        language={file?.language ?? 'python'}
        defaultValue={''}
        value={file?.value?.lines ?? ''}
        onMount={handleEditorDidMount}
        path={file.path}
        options={{ readOnly: true, fontSize: 10 }}
    />
)


const PathDisplay = ({
    path,
    loading = false,
}: {
    path: string
    loading?: boolean
}) => (
    <div className="-mt-[1px] px-3 py-1 bg-night border-t border-outlinecolor">
        {loading ? (
            // <Skeleton className="w-[150px] h-[8px] mt-1 bg-neutral-800 rounded-[3px]" />
            <></>
        ) : (
            <p className="text-xs text-neutral-500">
                {path ? convertPath(path) : ''}
            </p>
        )}
    </div>
)

function convertPath(path) {
    // Split the path based on the separator, either "/" or "\"
    const parts = path.split(/[/\\]/)

    // Remove unwanted parts (e.g., initial "Users" or "C:" for Windows paths)
    const filteredParts = parts.filter(
        part => part && part !== 'Users' && !part.includes(':')
    )

    // Join the remaining parts with the custom separator
    const customPath = filteredParts.join(' > ')

    return customPath
}
