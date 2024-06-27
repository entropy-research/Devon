import React, { useMemo, useRef, forwardRef, useEffect, useState } from 'react'
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
        const [textareaHeight, setTextareaHeight] = useState('auto')
        const sharedStyles = `
        w-full
        rounded-xl
        pr-9
        pl-5
        py-3
        leading-8
        text-md
        max-h-[500px]
`
        const overlayRef = useRef<HTMLDivElement>(null)
        const combinedRef = useRef<HTMLTextAreaElement | null>(null)
        const setRefs = (element: HTMLTextAreaElement | null) => {
            combinedRef.current = element
            if (typeof ref === 'function') {
                ref(element)
            } else if (ref) {
                ;(
                    ref as React.MutableRefObject<HTMLTextAreaElement | null>
                ).current = element
            }
            if (innerRef) {
                innerRef.current = element
            }
        }

        const highlightedValue = useMemo(() => {
            if (!props.value) return null

            const parts = String(props.value).split(REGEX)
            return parts.map((part, index) => {
                if (part.match(REGEX) !== null) {
                    const snippetId = part.slice(1)
                    const exists = codeSnippets.some(
                        snippet => snippet.id === snippetId
                    )
                    return (
                        <span
                            key={index}
                            className={exists ? 'text-blue-500' : ''}
                        >
                            {part}
                        </span>
                    )
                }
                return part.split('\n').map((line, lineIndex, array) => (
                    <React.Fragment key={`${index}-${lineIndex}`}>
                        {line}
                        {lineIndex < array.length - 1 && <br />}
                    </React.Fragment>
                ))
            })
        }, [props.value, codeSnippets])

        const syncScroll = () => {
            if (combinedRef.current && overlayRef.current) {
                overlayRef.current.scrollTop = combinedRef.current.scrollTop
            }
        }

        useEffect(() => {
            const updateHeight = () => {
                if (combinedRef.current) {
                    const newHeight = `${combinedRef.current.scrollHeight}px`
                    setTextareaHeight(newHeight)
                }
            }

            updateHeight()
            window.addEventListener('resize', updateHeight)

            return () => window.removeEventListener('resize', updateHeight)
        }, [props.value])

        return (
            <div className="relative w-full flex">
                <TextareaAutosize
                    ref={setRefs}
                    value={props.value}
                    onChange={e => {
                        props.onChange?.(e)
                        if (combinedRef.current) {
                            setTextareaHeight(
                                `${combinedRef.current.scrollHeight}px`
                            )
                        }
                    }}
                    onScroll={syncScroll}
                    placeholder={placeholder}
                    style={{ height: textareaHeight }}
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
                    overflow-y-auto
                `
                    )}
                    {...props}
                />
                <div
                    ref={overlayRef}
                    style={{
                        height: textareaHeight,
                        paddingBottom: '3rem', // Add extra padding at the bottom
                    }}
                    className={cn(
                        sharedStyles,
                        `
                    absolute
                    top-0
                    left-0
                    right-0
                    pointer-events-none
                    overflow-hidden
                    whitespace-pre-wrap
                    break-words
                    text-white
                    overflow-y-auto
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
