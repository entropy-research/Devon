import { useState, useRef, useEffect } from 'react'
import { Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import * as AccordionPrimitive from '@radix-ui/react-accordion'
import Spinner from '../ui/loading-spinner'
import { Icon } from '@iconify/react'
import { parseDiff } from 'react-diff-view'
import 'react-diff-view/style/index.css'
import './diff-view.css'
import { parseFileDiff } from '../../lib/utils'
import * as unidiff from 'unidiff'
import StyledMessage from './styled-message'
import DiffViewer from '../ui/diff-viewer'
import { ChevronDown, CircleAlert, Ban, Info } from 'lucide-react'
import { getFileName, parseCommand } from '@/lib/utils'
import AtomLoader from '@/components/ui/atom-loader/atom-loader'
import DotsSpinner from '@/components/ui/dots-spinner/dots-spinner'
// Different types of message bubbles.

export function UserMessage({ children }: { children: React.ReactNode }) {
    return (
        <div className="group relative flex items-start">
            <div className="flex size-[33px] shrink-0 select-none items-center justify-center rounded-md border bg-background shadow-sm">
                <User />
            </div>
            <div className="ml-4 flex-1 space-y-2 overflow-hidden pl-2 chat-text-relaxed">
                {children}
            </div>
        </div>
    )
}

export function BotCard({
    children,
    showAvatar = true,
}: {
    children: React.ReactNode
    showAvatar?: boolean
}) {
    return (
        <div className="group relative flex items-start">
            <div
                className={cn(
                    'flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm',
                    !showAvatar && 'invisible'
                )}
            >
                <Bot />
            </div>
            <div className="ml-4 flex-1 pl-2">{children}</div>
        </div>
    )
}

export function SystemMessage({ children }: { children: React.ReactNode }) {
    return (
        <div
            className={
                'mt-2 flex items-center justify-center gap-2 text-xs text-gray-500'
            }
        >
            <div className={'max-w-[600px] flex-initial p-2'}>{children}</div>
        </div>
    )
}

export function SpinnerMessage({ paused = false }: { paused?: boolean }) {
    return (
        <div className="group relative flex items-start">
            <div className="flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm">
                <Bot />
            </div>
            <div className="ml-5 h-[32px] flex flex-row items-center flex-1 space-y-2 overflow-hidden px-1">
                {/* <Spinner paused={paused} /> */}
                {/* <AtomLoader speed="fast" size="xs" /> */}
                {!paused && <DotsSpinner size={8} paused={paused} />}
            </div>
        </div>
    )
}

export const BotMessage = ({
    content,
    className,
    pretext,
}: {
    content: string
    className?: string
    pretext?: JSX.Element
}) => {
    const icon = (
        <div className="flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm">
            <Bot />
        </div>
    )
    if (pretext) {
        return (
            <div className={cn('group relative flex items-start', className)}>
                {icon}
                <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1 flex">
                    {pretext}
                    {content}
                </div>
            </div>
        )
    }

    return <StyledMessage content={content} className={className} icon={icon} />
}

export const ThoughtMessage = ({
    content,
    className,
}: {
    content: string
    className?: string
}) => {
    const icon = (
        <div className="scale-x-[-1] translate-x-1 flex size-[32px] shrink-0 select-none items-center justify-center rounded-md text-primary-foreground shadow-sm">
            {/* <TfiThought size={28} /> */}
            <Icon
                icon="mdi:thinking"
                className="w-[30px] h-[30px] transform -scale-x-100"
            />
        </div>
    )
    return <StyledMessage content={content} className={className} icon={icon} />
}

export const ToolResponseMessage = ({
    content,
    className,
    index,
}: {
    content: string
    className?: string
    index: number
}) => {
    const icon = <div className="w-[32px]"></div>
    let [command, response] = content.toString().split('|START_RESPONSE|')
    const parsedRes = parseCommand(command)
    if (parsedRes?.command === 'ask_user') {
        return null
    } else if (parsedRes?.command === 'no_op') {
        if (index === 0) {
            return null
        }
        return <ThoughtMessage content={'Let me cook...'} />
    }

    if (command.includes('Running command: edit')) {
        const indexOfFirstNewline = command.indexOf('\n')
        if (indexOfFirstNewline !== -1) {
            command = command.substring(indexOfFirstNewline + 1)
        }
        const { path, language, searchContent, replaceContent } =
            parseFileDiff(command)

        const resultingDiffLines = unidiff.diffLines(
            searchContent,
            replaceContent
        )
        const unifiedDiff = unidiff.formatLines(resultingDiffLines, {
            aname: 'before',
            bname: 'after',
            context: 3,
        })

        const files = parseDiff(unifiedDiff)

        return (
            <div className="flex ml-[50px] flex-col">
                {parsedRes &&
                    parsedRes.command != 'create_file' &&
                    parsedRes.command && (
                        <div className="mt-2 w-full mb-1">
                            <pre className="text-md mb-2 text-gray-400 whitespace-pre-wrap break-words">
                                <strong>Command:</strong> {parsedRes.command}{' '}
                                {getFileName(path)}
                            </pre>
                        </div>
                    )}
                <div className="relative w-full font-sans codeblock bg-zinc-950 rounded-md overflow-hidden">
                    <div className="flex items-center justify-between w-full pl-3 py-0 pr-1 bg-code-header text-zinc-100 rounded-t-md sticky top-0 hover:cursor-pointer">
                        <div className="flex py-2 items-center text-gray-300 px-1">
                            <pre className="text-sm flex">diff</pre>
                        </div>
                    </div>
                    <div className="bg-midnight text-zinc-100 overflow-hidden w-full">
                        <DiffViewer files={files} />
                    </div>
                </div>
            </div>
        )
    }
    return (
        <>
            {parsedRes &&
            parsedRes.command != 'create_file' &&
            parsedRes.command ? (
                <div className="pl-[49px] mt-2 w-full">
                    <pre className="text-md mb-2 text-gray-400 whitespace-pre-wrap break-words">
                        <strong>Command:</strong> {parsedRes.command}{' '}
                        {parsedRes.remainingText}
                    </pre>
                </div>
            ) : (
                <StyledMessage
                    content={command}
                    className={className}
                    icon={icon}
                />
            )}

            {response && <ResponseBlock response={response} />}
        </>
    )
}

export const RateLimitWarning = ({ className }: { className?: string }) => {
    // return (
    //     <div className="ml-[49px] mt-3 overflow-auto text-gray-400">
    //         <pre className="text-sm mb-2 whitespace-pre-wrap break-words">
    //             <strong>Rate limit reached:</strong> Automatically retrying in 1
    //             minute...
    //         </pre>
    //     </div>
    // )
    return (
        <div className="ml-[49px] mt-3 overflow-auto !text-gray-400 flex items-center gap-[6px] chat-text-relaxed">
            <Info size={18} />
            <p className="text-md">
                <span>Rate limit reached:</span> Automatically retrying in 1
                minute...
            </p>
        </div>
    )
}

export const ErrorMessage = ({
    content,
    className,
}: {
    content: string
    className?: string
}) => {
    const [expanded, setExpanded] = useState(true)
    const [height, setHeight] = useState(0)
    const contentRef = useRef<HTMLPreElement>(null)

    const toggleExpanded = () => setExpanded(prev => !prev)

    useEffect(() => {
        if (contentRef.current) {
            setHeight(expanded ? contentRef.current.scrollHeight : 0)
        }
    }, [expanded, content])

    return (
        <div className={cn('mt-3 overflow-auto', className)}>
            <div className="relative w-full font-sans codeblock bg-zinc-950 rounded-md overflow-hidden">
                <div
                    className="flex items-center justify-between w-full pl-3 py-0 pr-1 bg-code-header text-zinc-100 rounded-t-md sticky top-0 hover:cursor-pointer"
                    onClick={toggleExpanded}
                >
                    <div className="flex py-2 items-center text-red-400 px-[1px] gap-[3px]">
                        {/* <CircleAlert
                            className={cn(
                                'h-[13px] w-[13px] transition-transform duration-200 ease-in-out mr-[3px]'
                            )}
                        /> */}
                        <Ban
                            className={cn(
                                'h-[12px] w-[12px] transition-transform duration-200 ease-in-out mr-[3px] ml-[2px]'
                            )}
                        />
                        <pre className="text-sm flex">Error</pre>
                    </div>
                </div>
                <div
                    style={{ height: `${height}px` }}
                    className="transition-[height] duration-300 ease-in-out overflow-auto bg-midnight"
                >
                    <div className="duration-300 ease-in-out overflow-y-auto bg-midnight w-full max-h-[300px]">
                        <pre
                            ref={contentRef}
                            className="text-zinc-100 p-5 text-sm w-full rounded-b-md whitespace-pre-wrap break-words"
                        >
                            {content}
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    )
}

const ResponseBlock = ({ response }: { response: string }) => {
    const [expanded, setExpanded] = useState(false)
    const [height, setHeight] = useState(0)
    const contentRef = useRef<HTMLPreElement>(null)

    const toggleExpanded = () => setExpanded(prev => !prev)

    useEffect(() => {
        if (contentRef.current) {
            setHeight(expanded ? contentRef.current.scrollHeight : 0)
        }
    }, [expanded, response])

    return (
        <div className="ml-[49px] mt-3">
            <div className="relative w-full font-sans codeblock bg-zinc-950 rounded-md overflow-hidden">
                <div
                    className="flex items-center justify-between w-full pl-3 py-0 pr-1 bg-code-header text-zinc-100 rounded-t-md sticky top-0 hover:cursor-pointer"
                    onClick={toggleExpanded}
                >
                    <div className="flex py-2 items-center text-gray-300">
                        <ChevronDown
                            className={cn(
                                'h-[15px] w-[15px] transition-transform duration-200 ease-in-out mr-[3px]',
                                expanded ? '' : '-rotate-90'
                            )}
                        />
                        <pre className="text-sm flex">Response</pre>
                    </div>
                </div>
                <div
                    style={{ height: `${height}px` }}
                    className="transition-[height] duration-300 ease-in-out overflow-auto bg-midnight"
                >
                    <pre
                        ref={contentRef}
                        className="text-zinc-100 p-5 text-sm w-full rounded-b-md"
                    >
                        {response}
                    </pre>
                </div>
            </div>
        </div>
    )
}
