// Inspired by Chatbot-UI and modified to fit the needs of this project
// @see https://github.com/mckaywrigley/chatbot-ui/blob/main/components/Markdown/CodeBlock.tsx
import { FC, memo } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { coldarkDark } from 'react-syntax-highlighter/dist/cjs/styles/prism'

import { useCopyToClipboard } from '@/lib/hooks/use-copy-to-clipboard'
import { Copy, CopyCheck, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { convertPath } from '@/panels/editor/components/code-editor'
import { Icon } from '@iconify/react'
import {
    getIconFromLanguage,
    getIconFromFilename,
} from '@/lib/programming-language-utils'

interface CodeBlockProps {
    fileName: string
    language: string
    value: string
    path?: string
}

interface SimpleCodeBlockProps {
    language: string
    value: string
    fileName: string
    subtext: string
    onClickHeader: () => void
}

interface languageMap {
    [key: string]: string | undefined
}

export const programmingLanguages: languageMap = {
    javascript: '.js',
    python: '.py',
    java: '.java',
    c: '.c',
    cpp: '.cpp',
    'c++': '.cpp',
    'c#': '.cs',
    ruby: '.rb',
    php: '.php',
    swift: '.swift',
    'objective-c': '.m',
    kotlin: '.kt',
    typescript: '.ts',
    go: '.go',
    perl: '.pl',
    rust: '.rs',
    scala: '.scala',
    haskell: '.hs',
    lua: '.lua',
    shell: '.sh',
    sql: '.sql',
    html: '.html',
    css: '.css',
    // add more file extensions here, make sure the key is same as language prop in CodeBlock.tsx component
}

export const generateRandomString = (length: number, lowercase = false) => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXY3456789' // excluding similar looking characters like Z, 2, I, 1, O, 0
    let result = ''
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return lowercase ? result.toLowerCase() : result
}

const CodeBlock: FC<CodeBlockProps> = memo(
    ({ fileName, language, value, path }) => {
        const { isCopied, copyToClipboard } = useCopyToClipboard({
            timeout: 2000,
        })
        const { toast } = useToast()

        const downloadAsFile = () => {
            if (typeof window === 'undefined') {
                return
            }
            const fileExtension = programmingLanguages[language] || '.file'
            const suggestedFileName = `file-${generateRandomString(
                3,
                true
            )}${fileExtension}`
            const fileName = window.prompt(
                'Enter file name' || '',
                suggestedFileName
            )

            if (!fileName) {
                // User pressed cancel on prompt.
                return
            }

            const blob = new Blob([value], { type: 'text/plain' })
            const url = URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.download = fileName
            link.href = url
            link.style.display = 'none'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(url)
        }

        const onCopy = () => {
            if (isCopied) return
            copyToClipboard(value)
            toast({
                title: 'Copied to clipboard!',
            })
        }

        return (
            <div className="relative w-full font-sans codeblock bg-zinc-950 rounded-md overflow-auto">
                <div className="flex items-center justify-between w-full pl-3 py-0 pr-1 bg-zinc-800 text-zinc-100 rounded-t-md">
                    <div className="flex items-center">
                        {fileName ? (
                            <Icon
                                icon={getIconFromFilename(fileName)}
                                className="h-4 w-4 mr-2"
                            />
                        ) : (
                            <Icon
                                icon={getIconFromLanguage(language)}
                                className="h-4 w-4 mr-2"
                            />
                        )}
                        {fileName ? (
                            <span className="text-sm">{fileName}</span>
                        ) : (
                            <span className="text-xs lowercase">
                                {language}
                            </span>
                        )}
                    </div>

                    <div className="flex items-center space-x-1">
                        {/* <Button
                        variant="ghost"
                        className="hover:bg-zinc-800 focus-visible:ring-1 focus-visible:ring-slate-700 focus-visible:ring-offset-0"
                        onClick={downloadAsFile}
                        size="icon"
                    >
                        <Download size={16}/>
                        <span className="sr-only">Download</span>
                    </Button> */}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="smooth-hover text-xs hover:bg-zinc-800 focus-visible:ring-1 focus-visible:ring-slate-700 focus-visible:ring-offset-0"
                            onClick={onCopy}
                        >
                            {isCopied ? (
                                <CopyCheck size={16} />
                            ) : (
                                <Copy
                                    size={16}
                                    className="text-neutral-500 hover:text-white"
                                />
                            )}
                            <span className="sr-only">Copy code</span>
                        </Button>
                    </div>
                </div>
                {path && (
                    <span className="text-xs lowercase px-4 truncate flex-1 mr-5 overflow-hidden flex">
                        {convertPath(path)}
                    </span>
                )}
                <SyntaxHighlighter
                    language={language}
                    style={coldarkDark}
                    PreTag="div"
                    showLineNumbers
                    customStyle={{
                        margin: 0,
                        width: '100%',
                        background: 'transparent',
                        padding: '1.5rem 1rem',
                    }}
                    lineNumberStyle={{
                        userSelect: 'none',
                    }}
                    codeTagProps={{
                        style: {
                            fontSize: '0.9rem',
                            fontFamily: 'var(--font-mono)',
                        },
                    }}
                >
                    {value}
                </SyntaxHighlighter>
            </div>
        )
    }
)
CodeBlock.displayName = 'CodeBlock'

const SimpleCodeBlock: FC<SimpleCodeBlockProps> = memo(
    ({ language, value, fileName, subtext, onClickHeader }) => {
        const { isCopied, copyToClipboard } = useCopyToClipboard({
            timeout: 2000,
        })
        const { toast } = useToast()

        const onCopy = () => {
            if (isCopied) return
            copyToClipboard(value)
            toast({
                title: 'Copied to clipboard!',
            })
        }

        return (
            <div className="relative w-full font-sans codeblock bg-zinc-950 rounded-md overflow-hidden border-[1px] border-outlinecolor">
                <div
                    className="flex items-center justify-between w-full pl-3 py-0 pr-1 bg-zinc-800 text-zinc-100 rounded-t-md sticky top-0 z-10 hover:cursor-pointer"
                    onClick={onClickHeader}
                >
                    <div className="flex py-2">
                        {language && (
                            <Icon
                                icon={getIconFromLanguage(language)}
                                className="h-4 w-4 mr-2"
                            />
                        )}
                        <span className="text-xs lowercase flex">
                            {fileName}
                            <p className="ml-2 normal-case text-[0.7rem] text-neutral-500">
                                {subtext}
                            </p>
                        </span>
                    </div>
                </div>
                <div className="overflow-y-auto whitespace-pre-wrap break-words max-h-32">
                    <SyntaxHighlighter
                        language={language}
                        style={coldarkDark}
                        PreTag="div"
                        customStyle={{
                            margin: 0,
                            width: '100%',
                            background: 'transparent',
                            padding: '0rem 1rem',
                        }}
                        lineNumberStyle={{
                            userSelect: 'none',
                        }}
                        codeTagProps={{
                            style: {
                                fontSize: '0.7rem',
                                fontFamily: 'var(--font-mono)',
                            },
                        }}
                    >
                        {value}
                    </SyntaxHighlighter>
                </div>
            </div>
        )
    }
)
SimpleCodeBlock.displayName = 'SimpleCodeBlock'

export { CodeBlock, SimpleCodeBlock }
