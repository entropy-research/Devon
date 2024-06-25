import { Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { spinner } from './chat.spinner'
import { CodeBlock } from '@/components/ui/codeblock'
import { MemoizedReactMarkdown } from './chat.memoized-react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
// import { remarkCustomCode } from './remarkCustomCode' // import the custom plugin
// import { TfiThought } from 'react-icons/tfi'
import { Icon } from '@iconify/react'
import { parseDiff, Diff, Hunk } from 'react-diff-view'
import 'react-diff-view/style/index.css'
import './diff-view.css'
import { parseFileDiff } from '../../lib/utils'
import * as unidiff from 'unidiff'

// Different types of message bubbles.

export function UserMessage({ children }: { children: React.ReactNode }) {
    return (
        <div className="group relative flex items-start">
            <div className="flex size-[33px] shrink-0 select-none items-center justify-center rounded-md border bg-background shadow-sm">
                <User />
            </div>
            <div className="ml-4 flex-1 space-y-2 overflow-hidden pl-2">
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

export function SpinnerMessage() {
    return (
        <div className="group relative flex items-start">
            <div className="flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm">
                <Bot />
            </div>
            <div className="ml-4 h-[32px] flex flex-row items-center flex-1 space-y-2 overflow-hidden px-1">
                {spinner}
            </div>
        </div>
    )
}

export const BotMessage = ({
    content,
    className,
}: {
    content: string
    className?: string
}) => {
    const icon = (
        <div className="flex size-[32px] shrink-0 select-none items-center justify-center rounded-md border bg-primary text-primary-foreground shadow-sm">
            <Bot />
        </div>
    )
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
}: {
    content: string
    className?: string
}) => {
    const icon = <div className="w-[32px]"></div>
    let [command, response] = content.toString().split('|START_RESPONSE|')

    if (command.includes('Running command: edit')) {
        const indexOfFirstNewline = command.indexOf('\n')
        if (indexOfFirstNewline !== -1) {
            command = command.substring(indexOfFirstNewline + 1)
        }
        const { filename, language, searchContent, replaceContent } =
            parseFileDiff(command)

        const resultingDiffLines = unidiff.diffLines(searchContent, replaceContent)
        const unifiedDiff = unidiff.formatLines(resultingDiffLines, {
            aname: 'before',
            bname: 'after',
            context: 3,
        })

        const files = parseDiff(unifiedDiff)

        return (
            <div className="flex ml-[50px]">
                {files.map(file => {
                    return (
                        <Diff
                            key={file.oldRevision + '-' + file.newRevision}
                            viewType="unified"
                            diffType={file.type}
                            hunks={file.hunks}
                            gutterType="none"
                        >
                            {hunks =>
                                hunks.map(hunk => (
                                    <Hunk key={hunk.content} hunk={hunk} />
                                ))
                            }
                        </Diff>
                    )
                })}
            </div>
        )
    }
    return <StyledMessage content={command} className={className} icon={icon} />
}

const StyledMessage = ({
    content,
    className,
    icon,
}: {
    content: string
    className?: string
    icon: React.ReactNode
}) => {
    const path = extractPath(content)
    // const textWithoutPath = path
    //     ? content.replace(`# ${path}`, '').trim()
    //     : content
    const textWithoutPath = content

    return (
        <div className={cn('group relative flex items-start', className)}>
            {icon}
            <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
                {path && (
                    <div className="text-sm text-gray-500 mb-2">
                        <strong>Path:</strong> {path}
                    </div>
                )}
                <MemoizedReactMarkdown
                    className="prose break-words dark:prose-invert prose-p:leading-relaxed prose-pre:p-0"
                    remarkPlugins={[remarkGfm, remarkMath]}
                    components={{
                        p({ children }) {
                            return <p className="mb-2 last:mb-0">{children}</p>
                        },
                        code({ node, inline, className, children, ...props }) {
                            // Extract the path from the code block
                            const codeContent = String(children).replace(
                                /\n$/,
                                ''
                            )
                            const path = extractPath(codeContent)
                            // const textWithoutPath = path
                            //     ? codeContent.replace(`# ${path}`, '').trim()
                            //     : codeContent
                            const textWithoutPath = codeContent

                            if (inline || !className) {
                                return (
                                    <code
                                        className={cn(
                                            className,
                                            'bg-black px-[4px] py-[3px] rounded-md text-white text-[0.9rem]'
                                        )}
                                        {...props}
                                    >
                                        {children}
                                    </code>
                                )
                            }

                            const match = /language-(\w+)/.exec(className || '')

                            return (
                                <>
                                    <CodeBlock
                                        key={Math.random()}
                                        language={(match && match[1]) || ''}
                                        value={textWithoutPath}
                                        path={path}
                                        {...props}
                                    />
                                </>
                            )
                        },
                    }}
                >
                    {textWithoutPath}
                </MemoizedReactMarkdown>
            </div>
        </div>
    )
}

const extractPath = (content: string) => {
    const pathMatch = content.match(/^# (\/[^\s]+)/)
    if (pathMatch) {
        return pathMatch[1]
    }
    return null
}
