import React, { useState, useRef, useEffect } from 'react'
import TextareaAutosize, {
    TextareaAutosizeProps,
} from 'react-textarea-autosize'

import { cn } from '@/lib/utils'
import { ICodeSnippet } from '@/panels/chat/components/ui/code-snippet'

export interface TextareaProps
    extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

interface AutoresizeTextareaProps extends TextareaAutosizeProps {
    highlightCodeSnippets?: boolean
    codeSnippets?: ICodeSnippet[]
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, ...props }, ref) => {
        return <textarea className={cn('', className)} ref={ref} {...props} />
    }
)
Textarea.displayName = 'Textarea'
const REGEX = /(@\S+)/g

const AutoresizeTextarea = React.forwardRef(
    (
        {
            className,
            highlightCodeSnippets = false,
            codeSnippets = [],
            ...props
        },
        ref
    ) => {
        const [value, setValue] = useState(props.value || '')

        useEffect(() => {
            if (props.value !== undefined) {
                setValue(props.value)
            }
        }, [props.value])

        const handleChange = e => {
            const newValue = e.target.value
            setValue(newValue)
            if (props.onChange) {
                props.onChange(e)
            }
        }

        const sharedStyles = `
            resize-none
            h-full
            overflow-y-hidden
            overflow-x-auto
            rounded-xl
            border
            border-input
            pr-9
            pl-5
            py-3
            leading-8
            text-md
        `

        return (
            <div className="relative w-full">
                <TextareaAutosize
                    ref={ref}
                    className={cn(
                        sharedStyles,
                        `
                        bg-white
                        dark:bg-midnight
                        placeholder:text-muted-foreground
                        placeholder:text-gray-400
                        transition
                        duration-100
                        focus-visible:outline-none
                        focus-visible:ring-ring
                        focus-visible:ring-offset-2
                        ring-offset-background
                        flex
                        w-full
                        disabled:cursor-not-allowed
                        disabled:opacity-50
                        ${
                            highlightCodeSnippets
                                ? 'caret-current text-transparent'
                                : ''
                        }
                        `,
                        className
                    )}
                    value={value}
                    onChange={handleChange}
                    maxRows={20}
                    {...props}
                />
                {/* {highlightCodeSnippets && (
                    <div
                        className={cn(
                            sharedStyles,
                            `
                            absolute
                            inset-0
                            pointer-events-none
                            whitespace-pre-wrap
                            break-words
                            bg-transparent
                            `,
                            className
                        )}
                    >
                        {value.split(REGEX).map((word, i) => {
                            if (word.match(REGEX) !== null) {
                                const exists = codeSnippets.some(
                                    snippet => snippet.id === word.slice(1)
                                )
                                return (
                                    <span
                                        key={i}
                                        className={
                                            exists ? 'text-blue-500' : ''
                                        }
                                    >
                                        {word}
                                    </span>
                                )
                            } else {
                                return <span key={i}>{word}</span>
                            }
                        })}
                    </div>
                )} */}
            </div>
        )
    }
)

AutoresizeTextarea.displayName = 'AutoresizeTextarea'

const PlannerTextarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, ...props }, ref) => {
        return (
            <textarea
                className={cn(
                    `resize-none
                    h-full
                    w-full
                    flex
                    flex-1
                    rounded-lg
                    border
                    border-input
                    p-3
                    leading-8
                    text-md
                    placeholder:text-muted-foreground
                    bg-batman
                    text-white
                    placeholder:text-gray-400
                    transition
                    duration-100
                    focus:border-neutral-400
                    focus:outline-none
                    focus-visible:outline-none
                    focus-visible:ring-ring
                    focus-visible:ring-offset-2
                    ring-offset-background
                    disabled:cursor-not-allowed
                    disabled:opacity-50`,
                    className
                )}
                ref={ref}
                {...props}
            />
        )
    }
)

PlannerTextarea.displayName = 'PlannerTextarea'

export { Textarea, AutoresizeTextarea, PlannerTextarea }
