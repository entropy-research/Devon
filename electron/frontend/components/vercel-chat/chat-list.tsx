import { Separator } from '@/components/ui/separator'
import { UIState } from '@/lib/chat/chat.actions'
import { Session } from '@/lib/chat.types'
import Link from 'next/link'
// import { ExclamationTriangleIcon } from '@radix-ui/react-icons'
import {
    // BotCard,
    BotMessage,
} from '@/components/vercel-chat/message'
import { SpinnerMessage, UserMessage } from '@/components/vercel-chat/message'

export interface ChatList {
    messages: UIState
    session?: Session
    isShared: boolean
}

export function ChatList({ messages, session, isShared }: ChatList) {
    if (!messages.length) {
        return null
    }

    return (
        <div className="relative max-w-2xl px-8">
            {/* {!isShared && !session ? (
                <>
                    <div className="group relative mb-4 flex items-start">
                        <div className="bg-background flex size-[25px] shrink-0 select-none items-center justify-center rounded-md border shadow-sm">
                            <ExclamationTriangleIcon />
                        </div>
                        <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
                            <p className="text-muted-foreground leading-normal">
                                Please{' '}
                                <Link href="/login" className="underline">
                                    log in
                                </Link>{' '}
                                or{' '}
                                <Link href="/signup" className="underline">
                                    sign up
                                </Link>{' '}
                                to save and revisit your chat history!
                            </p>
                        </div>
                    </div>
                    <Separator className="my-4" />
                </>
            ) : null} */}

            {messages.map((message, index) => (
                <div key={message.id} className="mb-8">
                    {message.display}
                    {/* {index < messages.length - 1 && <Separator className="my-4" />} */}
                </div>
            ))}
        </div>
    )
}

export interface ChatList2 {
    messages: any[]
    session?: Session
    isShared: boolean
}

export function ChatList2({ messages, session, isShared }: ChatList2) {
    if (!messages.length) {
        return null
    }

    return (
        <div className="relative max-w-2xl px-8">
            {/* {!isShared && !session ? (
                <>
                    <div className="group relative mb-4 flex items-start">
                        <div className="bg-background flex size-[25px] shrink-0 select-none items-center justify-center rounded-md border shadow-sm">
                            <ExclamationTriangleIcon />
                        </div>
                        <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
                            <p className="text-muted-foreground leading-normal">
                                Please{' '}
                                <Link href="/login" className="underline">
                                    log in
                                </Link>{' '}
                                or{' '}
                                <Link href="/signup" className="underline">
                                    sign up
                                </Link>{' '}
                                to save and revisit your chat history!
                            </p>
                        </div>
                    </div>
                    <Separator className="my-4" />
                </>
            ) : null} */}

            {messages.map((message, index) => (
                <DisplayedChatMessage
                    key={message.id ?? index}
                    message={message}
                />
            ))}
        </div>
    )
}

const DisplayedChatMessage = ({ message }) => {
    return (
        <div className="mb-8">
            {message.type === 'Task' ? (
                <BotMessage content={message.content} />
            ) : (
                <UserMessage>{message.content}</UserMessage>
            )}
        </div>
    )
}
