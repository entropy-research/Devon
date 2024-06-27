import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps
    extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, ...props }, ref) => {
        return <textarea className={cn('', className)} ref={ref} {...props} />
    }
)
Textarea.displayName = 'Textarea'

const PlannerTextarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
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

export { Textarea, PlannerTextarea }
