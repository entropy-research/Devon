import { cn } from '@/lib/utils'
import { CodeBlock } from '@/components/ui/codeblock'
import { MemoizedReactMarkdown } from '../ui/memoized-react-markdown'
import { getLanguageFromFilename } from '@/lib/programming-language-utils'
import { getFileName } from '@/lib/utils'
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
    const { textWithoutPath, codeBlocks } = extractCodeBlocks(content)

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
                    className="prose break-words dark:prose-invert prose-p:leading-relaxed prose-pre:p-0 chat-text-relaxed"
                    components={{
                        p({ children }) {
                            return <p className="mb-2 last:mb-0">{children}</p>
                        },
                        code({ node, className, children, ...props }) {
                            const value = String(children).replace(/\n$/, '')

                            // Check if it's an inline code (single backticks)
                            if (value.split('\n').length === 1 && !props.meta) {
                                return (
                                    <code
                                        className={cn(
                                            'bg-black px-[6px] py-[3px] rounded-md text-primary text-opacity-90 text-[0.9rem]',
                                            className
                                        )}
                                        {...props}
                                    >
                                        {value}
                                    </code>
                                )
                            }

                            const match = /language-(\w+)/.exec(className || '')
                            const meta = props.meta || ''
                            return (
                                <div className="relative py-5">
                                    {meta && (
                                        <div className="text-sm text-gray-500 mb-2">
                                            <strong>Command:</strong> {meta}
                                        </div>
                                    )}
                                    <CodeBlock
                                        key={Math.random()}
                                        // language={(match && match[1]) || ''}
                                        value={value}
                                        // fileName={path ?? ''}
                                        // path={path}
                                        // {...props}
                                    />
                                </div>
                            )
                        },
                    }}
                >
                    {textWithoutPath}
                </MemoizedReactMarkdown>
                {codeBlocks.map((block, index) => (
                    <div key={index} className="relative py-5">
                        <pre className="text-md mb-2">
                            <strong>Command:</strong> {block.command}{' '}
                            {block.relativePath}
                        </pre>
                        <CodeBlock
                            value={block.code}
                            fileName={block.fileName}
                            language={getLanguageFromFilename(block.fileName)}
                        />
                    </div>
                ))}
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

const extractCodeBlocks = (content: string) => {
    const regex = /Running command: (\S+)\s+(\S+)\s+<<<\n([\s\S]*?)\n>>>/g
    let match
    const codeBlocks = []
    let textWithoutPath = content

    while ((match = regex.exec(content)) !== null) {
        codeBlocks.push({
            command: match[1],
            relativePath: match[2],
            fileName: getFileName(match[2]),
            code: match[3],
        })
        textWithoutPath = textWithoutPath.replace(match[0], '')
    }

    return { textWithoutPath, codeBlocks }
}

export default StyledMessage
