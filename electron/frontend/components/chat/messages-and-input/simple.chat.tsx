'use client'

import { cn } from '@/lib/utils'
import { ChatList, ChatList2 } from '@/components/vercel-chat/chat-list'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import { useEffect, useState } from 'react'
// import { useUIState, useAIState } from 'ai/rsc'
import { Session } from '@/lib/chat.types'
import { usePathname, useRouter } from 'next/navigation'
import { Message } from '@/lib/chat/chat.actions'
import { useScrollAnchor } from '@/lib/hooks/chat.use-scroll-anchor'
import SuggestionContainer from './suggestion-container'
import { VercelInput, RegularInput } from './input'
import { useToast } from '@/components/ui/use-toast'
import { ButtonScrollToBottom } from './button-scroll-to-bottom'
import { getChatById, getChats, createChat } from '@/lib/services/chatService'
import { Chat } from '@/lib/chat.types'
import { AI } from '@/lib/chat/chat.actions'
import EventStream from '@/components/event-stream'
// import useCreateSession from '@/lib/services/sessionService/use-create-session'
import useFetchSessionEvents, {
    fetchSessionEvents,
} from '@/lib/services/sessionService/use-fetch-session-events'
import SessionEventsDisplay from '@/components/events'

export interface ChatProps extends React.ComponentProps<'div'> {
    initialMessages?: Message[]
    id?: string
    session?: Session
    missingKeys?: string[]
}

export function SimpleChat({
    viewOnly,
    id,
    className,
    session,
    missingKeys,
}: { viewOnly: boolean } & ChatProps) {
    const path = usePathname()
    const [messages, setMessages] = useState<Message[]>([])
    const {
        messagesRef,
        scrollRef,
        visibilityRef,
        isAtBottom,
        scrollToBottom,
    } = useScrollAnchor()
    const { toast } = useToast()
    const [_, setNewChatId] = useLocalStorage('newChatId', id)

    // Clean later
    const [userRequested, setUserRequested] = useState(false)

    // TODO: Actually use this to load chat from backend
    useEffect(() => {
        if (session?.user) {
            if (!path.includes('chat') && messages.length === 1) {
                window.history.replaceState({}, '', `?chat=${id}`)
            }
        }
    }, [id, path, session?.user, messages])

    useEffect(() => {
        if (!id) return
        const fetchAndUpdateMessages = () => {
            fetchSessionEvents(id)
                .then(data => {
                    const parsedMessages = handleEvents(data, setUserRequested)
                    setMessages(parsedMessages)
                })
                .catch(error => {
                    console.error('Error fetching session events:', error)
                })
        }

        const intervalId = setInterval(fetchAndUpdateMessages, 2000)

        return () => {
            clearInterval(intervalId)
        }
    }, [id, messages])

    useEffect(() => {
        setNewChatId(id)
    })

    useEffect(() => {
        missingKeys?.map(key => {
            toast({
                title: `Missing ${key} environment variable!`,
            })
        })
    }, [toast, missingKeys])

    return (
        <div className="flex flex-col flex-2 relative h-full" ref={scrollRef}>
            <div className="flex-1">
                <div
                    className={cn('pt-4 md:pt-10', className)}
                    ref={messagesRef}
                >
                    <SessionEventsDisplay
                        sessionId={id}
                        setMessages={setMessages}
                    />
                    {messages?.length ? (
                        // <ChatList
                        //     messages={messages}
                        //     isShared={false}
                        //     session={session}
                        // />
                        <ChatList2
                            messages={messages}
                            isShared={false}
                            session={session}
                        />
                    ) : (
                        <></>
                    )}
                    {!viewOnly && <div className="h-[150px]"></div>}
                    <div className="h-px w-full" ref={visibilityRef} />
                </div>
            </div>
            {!viewOnly && (
                <div className="sticky bottom-0 w-full">
                    <div className="bg-fade-bottom-to-top pt-20 overflow-hidden rounded-xl -mb-[1px]">
                        {!(messages?.length > 0) && <SuggestionContainer />}
                        <ButtonScrollToBottom
                            isAtBottom={isAtBottom}
                            scrollToBottom={scrollToBottom}
                        />
                        {/* <VercelInput
                        isAtBottom={isAtBottom}
                        scrollToBottom={scrollToBottom}
                    /> */}
                        <RegularInput
                            sessionId={id}
                            isAtBottom={isAtBottom}
                            scrollToBottom={scrollToBottom}
                        />
                    </div>
                </div>
            )}
            {/* <EventStream sessionId={'1'} /> */}
        </div>
    )
}

type Event = {
    type:
        | 'ModelResponse'
        | 'ToolResponse'
        | 'Task'
        | 'Interrupt'
        | 'UserRequest'
        | 'Stop'
    content: string
    identifier: string | null
}

type Message = {
    text: string
    type: 'user' | 'agent' | 'command' | 'tool' | 'task'
}

const handleEvents = (
    events: Event[],
    setUserRequested: (value: boolean) => void
) => {
    const messages: Message[] = []
    for (const event of events) {
        const type = event.type
        // console.log("EVENT", event["content"]);
        if (type == 'ModelResponse') {
            // Model response content is in format <THOUGHT>{thought}</THOUGHT><COMMAND>{command}</COMMAND>
            if (event.content) {
                const thoughtMatch = event.content
                    .split('<THOUGHT>')
                    ?.pop()
                    ?.split('</THOUGHT>')[0]
                const commandMatch = event.content
                    .split('<COMMAND>')
                    .pop()
                    ?.split('</COMMAND>')[0]
                const thought = thoughtMatch ? thoughtMatch : ''
                const command = commandMatch ? commandMatch : ''

                // split command by space

                let command_split = command?.split(' ') ?? ['', '']
                let command_name = command_split[0].trim()
                let command_args = command_split.slice(1).join(' ')
                let trimmedStr = command_args.trim().replace(/^['"]+|['"]+$/g, '')

                if (command_name == 'ask_user') {
                    messages.push({ text: trimmedStr, type: 'agent' })
                } else {
                    messages.push({ text: thought ?? '', type: 'agent' })
                    messages.push({ text: command ?? '', type: 'command' })
                }
            }
        }

        if (type == 'ToolResponse') {
            messages.push({ text: event.content, type: 'tool' })
        }

        if (type == 'Task') {
            messages.push({ text: event.content, type: 'task' })
        }

        if (type == 'Interrupt') {
            messages.push({ text: event.content, type: 'user' })
        }

        if (type == 'UserRequest') {
            setUserRequested(true)
        }
    }
    return messages
}
