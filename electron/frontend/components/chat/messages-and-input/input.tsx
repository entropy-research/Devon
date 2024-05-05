import { useState, useRef, useEffect } from 'react'
import { Paperclip, ArrowRight } from 'lucide-react'
import { useActions, useUIState } from 'ai/rsc'
import { type AI } from '@/lib/chat/chat.actions'
import { AutoresizeTextarea } from '@/components/ui/textarea'
import { useComingSoonToast } from '@/components/ui/use-toast'
import { useEnterSubmit } from '@/lib/hooks/chat.use-enter-submit'
import { nanoid } from 'nanoid'
import { UserMessage } from '@/components/vercel-chat/message'

export default function Input({
    isAtBottom,
    scrollToBottom,
}: {
    isAtBottom: boolean
    scrollToBottom: () => void
}) {
    const [focused, setFocused] = useState(false)
    const toast = useComingSoonToast()
    const { formRef, onKeyDown } = useEnterSubmit()
    const inputRef = useRef<HTMLTextAreaElement>(null)
    const [input, setInput] = useState('')
    const [_, setMessages] = useUIState<typeof AI>()
    const { submitUserMessage } = useActions()

    return (
        <div className="relative grid align-middle px-5 pb-7 mt-8">
            <form
                ref={formRef}
                onSubmit={async (e: any) => {
                    e.preventDefault()

                    // Blur focus on mobile
                    if (window.innerWidth < 600) {
                        e.target['message']?.blur()
                    }

                    const value = input.trim()
                    setInput('')
                    if (!value) return

                    // Optimistically add user message UI
                    setMessages(currentMessages => [
                        ...currentMessages,
                        {
                            id: nanoid(),
                            display: <UserMessage>{value}</UserMessage>,
                        },
                    ])

                    // Submit and get response message
                    const responseMessage = await submitUserMessage(value)
                    setMessages(currentMessages => [
                        ...currentMessages,
                        responseMessage,
                    ])

                    scrollToBottom()
                }}
            >
                <div className="relative">
                    <AutoresizeTextarea
                        ref={inputRef}
                        placeholder="Give Devon a task to work on ..."
                        onFocus={() => setFocused(true)}
                        onBlur={() => setFocused(false)}
                        rows={1}
                        onKeyDown={onKeyDown}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                    />
                    <button
                        onClick={toast}
                        className="absolute left-[0.5rem] top-1/2 -translate-y-1/2 xl:left-[0.75rem] flex h-8 w-8 items-center justify-center rounded-md transition duration-200 hover:bg-gray-100 dark:hover:bg-night"
                    >
                        <Paperclip
                            className={`h-4 w-4 ${focused ? 'text-primary' : ''}`}
                        />
                    </button>
                    <button
                        className="absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 xl:right-4"
                        type="submit"
                    >
                        <ArrowRight
                            className={`h-4 w-4 ${focused ? 'text-primary' : ''}`}
                        />
                    </button>
                </div>
            </form>
        </div>
    )
}
