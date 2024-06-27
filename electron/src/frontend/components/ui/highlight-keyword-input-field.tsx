import { useMemo, useRef, forwardRef } from 'react'
import TextareaAutosize, {
    TextareaAutosizeProps,
} from 'react-textarea-autosize'
import { ICodeSnippet } from '@/panels/chat/components/ui/code-snippet'
import { cn } from '@/lib/utils'

interface AutoresizeTextareaProps extends TextareaAutosizeProps {
    highlightCodeSnippets?: boolean
    codeSnippets?: ICodeSnippet[]
    innerRef?: React.RefObject<HTMLTextAreaElement>
}

const REGEX = /(@\S+)/g

const HighlightKeywordInputField = forwardRef<
    HTMLTextAreaElement,
    AutoresizeTextareaProps
>(
    (
        {
            highlightCodeSnippets = false,
            codeSnippets = [],
            placeholder,
            innerRef,
            ...props
        },
        ref
    ) => {
        const sharedStyles = `
        w-full
        rounded-xl
        pr-9
        pl-5
        py-3
        leading-8
        text-md
    `

        const highlightedValue = useMemo(() => {
            if (!props.value) return null

            const parts = String(props.value).split(REGEX)
            return parts.map((part, index) => {
                if (part.match(REGEX) !== null) {
                    const snippetId = part.slice(1)
                    const exists = codeSnippets.some(
                        snippet => snippet.id === snippetId
                    )
                    return exists ? (
                        <span key={index} className="text-blue-500">
                            {part}
                        </span>
                    ) : (
                        <span key={index}>{part}</span>
                    )
                }
                return <span key={index}>{part}</span>
            })
        }, [props.value, codeSnippets])

        return (
            <div className="relative w-full flex">
                <TextareaAutosize
                    ref={innerRef || ref}
                    value={props.value}
                    onChange={props.onChange}
                    placeholder={placeholder}
                    className={cn(
                        sharedStyles,
                        `
                    resize-none
                    border
                    border-input
                    placeholder:text-muted-foreground
                    bg-midnight
                    text-transparent
                    caret-white
                    placeholder:text-gray-400
                    transition
                    duration-100
                    focus:outline-none
                    focus-visible:outline-none
                    focus-visible:ring-ring
                    focus-visible:ring-offset-2
                    ring-offset-background
                    disabled:cursor-not-allowed
                    disabled:opacity-50
                `
                    )}
                    {...props}
                />
                <div
                    className={cn(
                        sharedStyles,
                        `
                    absolute
                    top-0
                    left-0
                    h-full
                    pointer-events-none
                    overflow-hidden
                    whitespace-pre-wrap
                    break-words
                    text-white
                `
                    )}
                >
                    {highlightedValue}
                </div>
            </div>
        )
    }
)

HighlightKeywordInputField.displayName = 'HighlightKeywordInputField'

export default HighlightKeywordInputField
