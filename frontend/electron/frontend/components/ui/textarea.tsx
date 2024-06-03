import * as React from 'react'
import TextareaAutosize, {
    TextareaAutosizeProps,
} from 'react-textarea-autosize'

import { cn } from '@/lib/utils'

export interface TextareaProps
    extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, ...props }, ref) => {
        return <textarea className={cn('', className)} ref={ref} {...props} />
    }
)
Textarea.displayName = 'Textarea'

const AutoresizeTextarea = React.forwardRef<
    HTMLTextAreaElement,
    TextareaAutosizeProps
>(({ className, ...props }, ref) => {
    return (
        <TextareaAutosize
            className={cn(
                `resize-none
                 scroll-p-5
                 h-full
                 overflow-y-hidden
                 overflow-x-auto
                 rounded-xl
                 border
                 border-input
                 bg-white
                 bg-midnight
                 pr-9
                 pl-5
                 py-3
                 leading-8
                 text-md
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
                `,
                className
            )}
            ref={ref}
            // ref={(tag) => (this.textarea = tag)}
            maxRows={20}
            {...props}
        />
    )
})
AutoresizeTextarea.displayName = 'TextareaResize'

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
