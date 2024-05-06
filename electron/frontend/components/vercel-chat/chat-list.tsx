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
import Chat from '../chat/chat'

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

/**
ModelResponse
- Content: Response by the model (currently in the format <THOUGHT></THOUGHT><ACTION></ACTION>)
- Next: The action is parsed and the right tool is chosen or user response is requested

ToolResponse
- Content: Response from the tool
- Next: The model is called with the reponse as the observation

UserRequest
- Content: User input
- Next: The output is sent as ToolRequest

Interrupt
- Content: The interrupt message
- Next: ModelResponse, the model is interrupted

Stop
- Content: None
- Next: None

Task
- Content: The next task/object the agent has to complete
- Next: ModelResponse

 */
const DisplayedChatMessage = ({ message }) => {
    return (
        <div className="mb-8">
            {message.type === 'ModelResponse' ? (
                <BotMessage content={`Model: ${message.content}`} />
            ) : message.type === 'ToolResponse' ? (
                <ChatTypeWrapper type="Tool Response">{message.content}</ChatTypeWrapper>
            ) : message.type === 'UserRequest' ? (
                <UserMessage>{message.content}</UserMessage>
            ) : message.type === 'Interrupt' ? (
                <ChatTypeWrapper type="Interrupt">{message.content}</ChatTypeWrapper>
            ) : message.type === 'Stop' ? (
                <ChatTypeWrapper type="Stop">{message.content}</ChatTypeWrapper>
            ) : message.type === 'Task' ? (
                <ChatTypeWrapper type="Task">{message.content}</ChatTypeWrapper>
            ) : (
                <ChatTypeWrapper type="(Type not found)">{message.content}</ChatTypeWrapper>
            )}
        </div>
    )
}

const ChatTypeWrapper = ({ type, children }) => {
    return (
        <span className="flex">
            <p className="font-bold mr-2">{type}:</p>
            {children}
        </span>
    )
}
