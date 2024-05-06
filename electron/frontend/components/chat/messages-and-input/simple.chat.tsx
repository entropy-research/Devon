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
import useCreateSession from '@/lib/services/sessionService/use-create-session'
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
    const router = useRouter()
    const path = usePathname()
    const [messages, setMessages] = useState<Message[]>([])
    // const [messages] = useUIState()
    // const [aiState, setAIState] = useAIState()
    const {
        messagesRef,
        scrollRef,
        visibilityRef,
        isAtBottom,
        scrollToBottom,
    } = useScrollAnchor()
    const { toast } = useToast()

    const [_, setNewChatId] = useLocalStorage('newChatId', id)

    // const { createSession, sessionId, loading, error } = useCreateSession()
    // const [_path, setPath] = useState('')

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
            console.log('Fetching session events...')
            fetchSessionEvents(id)
                .then(data => {
                    setMessages(data)
                })
                .catch(error => {
                    console.error('Error fetching session events:', error)
                })
        }

        const intervalId = setInterval(fetchAndUpdateMessages, 5000)

        return () => {
            clearInterval(intervalId)
        }
    }, [id, messages])

    // useEffect(() => {
    //     const messagesLength = aiState.messages?.length
    //     if (messagesLength === 2) {
    //         router.refresh()
    //     }
    // }, [aiState.messages, router])

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

    // const handleSubmit = e => {
    //     e.preventDefault()
    //     const projectPath = '/Users/josh/Documents/cs/entropy/Devon/examples'
    //     setPath(projectPath)
    //     createSession(projectPath)
    // }

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
