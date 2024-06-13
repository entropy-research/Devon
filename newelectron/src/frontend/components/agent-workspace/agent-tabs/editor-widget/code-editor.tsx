import Editor, { Monaco } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import FileTabs from '@/components/file-tabs/file-tabs'
import { useState } from 'react'
import { SessionMachineContext } from '@/home'
import { File } from '@/lib/types'
import { mapLanguage, mapIcon } from '@/lib/services/fileService'

export default function CodeEditor({
    isExpandedVariant = false,
    showEditorBorders,
    path,
}: {
    isExpandedVariant?: boolean
    showEditorBorders: boolean
    path: string
}): JSX.Element {
    // const searchParams = useSearchParams()
    // const chatId = searchParams.get('chat')

    const [selectedFileId, setSelectedFileId] = useState<string | null>(null)

    const files: File[] = SessionMachineContext.useSelector(
        state => {
            if (state.context.sessionState?.editor && state.context.sessionState.editor.files) {
                return Object.keys(state.context.sessionState.editor.files).map(filename => ({
                    id: filename,
                    name: filename.split('/').pop() ?? 'unnamed_file',
                    path: filename,
                    language: mapLanguage(filename.split('/').pop()),
                    value: state.context.sessionState.editor.files[filename],
                    icon: mapIcon(filename.split('/').pop()),
                }))
            } else {
                return []
            }
        }
    )

    if (files && files.length > 0 && !selectedFileId) {
        setSelectedFileId(files[0].id)
    } else if ((!files || files.length === 0) && selectedFileId) {
        setSelectedFileId(null)
    }

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

    // if (!selectedFileId) {
    //     return (
    //         <>
    //             <FileTabs
    //                 files={files}
    //                 selectedFileId={selectedFileId ?? files[0]?.id}
    //                 setSelectedFileId={setSelectedFileId}
    //                 // chatId={chatId}
    //                 className={showEditorBorders ? '' : 'mr-[13px]'}
    //                 isExpandedVariant={isExpandedVariant}
    //             />
    //             {files.length > 0 && (
    //                 <PathDisplay path={'/Users/devon/projects/hello_world'} />
    //             )}
    //             <div className="w-full bg-workspace rounded-b-lg mt-[-2px]">
    //                 {selectedFileId && (
    //                     <BothEditorTypes
    //                         file={files?.find(f => f.id === selectedFileId)}
    //                         handleEditorDidMount={handleEditorDidMount}
    //                     />
    //                 )}
    //             </div>
    //         </>
    //     )
    // }



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
                selectedFileId={selectedFileId ?? null}
                setSelectedFileId={setSelectedFileId}
                // chatId={chatId}
                className={showEditorBorders ? '' : ''}
                isExpandedVariant={isExpandedVariant}
                loading={files.length === 0}
            />
            {files && <PathDisplay path={path} />}
            <div className="flex w-full h-full bg-bg-workspace rounded-b-lg mt-[-2px]">
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
        path={file?.path}
        options={{ readOnly: true, fontSize: 10 }}
    />
)


const PathDisplay = ({ path }: { path: string }) => (
    <div className="-mt-[1px] px-3 py-1 bg-night border-t border-outlinecolor">
        <p className="text-xs text-neutral-500">
            {path ? convertPath(path) : ''}
        </p>
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
