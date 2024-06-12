import { Bot, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { spinner } from './chat.spinner'
import { CodeBlock } from '@/components/ui/codeblock'
import { MemoizedReactMarkdown } from './chat.memoized-react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import { remarkCustomCode } from './remarkCustomCode' // import the custom plugin
import { TfiThought } from 'react-icons/tfi'

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
            <TfiThought size={28} />
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
    return <StyledMessage content={command} className={className} icon={icon} />
}

function StyledMessage({ content, className, icon }: { content: string, className: string, icon: JSX.Element }) {
    const text = content

    return (
        <div className={cn('group relative flex items-start', className)}>
            {icon}
            <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
                <MemoizedReactMarkdown
                    className="prose break-words dark:prose-invert prose-p:leading-relaxed prose-pre:p-0"
                    // remarkPlugins={[remarkGfm, remarkMath, remarkCustomCode]}
                    // remarkPlugins={[remarkCustomCode]}
                    components={{
                        p({ children }) {
                            return <p className="mb-2 last:mb-0">{children}</p>
                        },
                        code({ node, inline, className, children, ...props }) {
                            if (children.length) {
                                if (children[0] == '▍') {
                                    return (
                                        <span className="mt-1 animate-pulse cursor-default">
                                            ▍
                                        </span>
                                    )
                                }

                                children = (children as string).replace(
                                    '`▍`',
                                    '▍'
                                )
                            }

                            const match = /language-(\w+)/.exec(className || '')

                            if (inline) {
                                return (
                                    <code className={className} {...props}>
                                        {children}
                                    </code>
                                )
                            }

                            return (
                                <CodeBlock
                                    key={Math.random()}
                                    language={(match && match[1]) || ''}
                                    value={String(children).replace(/\n$/, '')}
                                    {...props}
                                />
                            )
                        },
                    }}
                >
                    {text}
                </MemoizedReactMarkdown>
            </div>
        </div>
    )
}
