import * as React from 'react'
import TextareaAutosize, {
    TextareaAutosizeProps,
} from 'react-textarea-autosize'

import { cn } from '@/lib/utils'

export interface TextareaProps
    extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, ...props }, ref) => {
        return (
            <textarea
                className={cn(
                    'resize-none scroll-p-5 h-full overflow-y-hidden overflow-x-auto rounded-2xl border border-day bg-white px-[2rem] leading-8 transition duration-100 focus:border-primary focus:outline-none dark:border-input dark:bg-input dark:text-white dark:placeholder:text-neutral-300 dark:focus:border-primary xl:px-[3rem] flex w-full border border-input bg-background py-3 text-lg ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
                    className
                )}
                ref={ref}
                {...props}
            />
        )
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
                'resize-none scroll-p-5 h-full overflow-y-hidden overflow-x-auto rounded-2xl border border-day bg-white px-[3rem] leading-8 transition duration-100 focus:border-primary focus:outline-none dark:border-input dark:bg-input dark:text-white dark:placeholder:text-neutral-300 dark:focus:border-primary xl:px-[3rem] flex w-full border border-input bg-background py-3 text-lg ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
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

export { Textarea, AutoresizeTextarea }
