'use client'

import { cn } from '@/lib/utils'
import { ChatList } from '@/components/vercel-chat/chat-list'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import { useEffect, useState } from 'react'
import { useUIState, useAIState } from 'ai/rsc'
import { Session } from '@/lib/chat.types'
import { usePathname, useRouter } from 'next/navigation'
import { Message } from '@/lib/chat/chat.actions'
import { useScrollAnchor } from '@/lib/hooks/chat.use-scroll-anchor'
import SuggestionContainer from './suggestion-container'
import Input from './input'
import { useToast } from '@/components/ui/use-toast'
import { ButtonScrollToBottom } from './button-scroll-to-bottom'
import { getChatById, getChats, createChat } from '@/lib/services/chatService'
import {
    createAI,
    createStreamableUI,
    getMutableAIState,
    getAIState,
    render,
    createStreamableValue,
} from 'ai/rsc'
import { Chat } from '@/lib/chat.types'
import { AI } from '@/lib/chat/chat.actions'
import EventStream from '@/components/event-stream'
import useCreateSession from '@/lib/services/sessionService/use-create-session'

export interface ChatProps extends React.ComponentProps<'div'> {
    initialMessages?: Message[]
    id?: string
    session?: Session
    missingKeys?: string[]
}

export function VercelChat({
    viewOnly,
    id,
    className,
    session,
    missingKeys,
}: { viewOnly: boolean } & ChatProps) {
    const router = useRouter()
    const path = usePathname()
    const [messages] = useUIState()
    const [aiState, setAIState] = useAIState()
    const { toast } = useToast()

    const [_, setNewChatId] = useLocalStorage('newChatId', id)

    const { createSession, sessionId, loading, error } = useCreateSession()
    const [_path, setPath] = useState('')

    useEffect(() => {
        // getChats().then((res) => {
        //     console.log('chats', res)
        // }
        // )
        const chat = getChatById('1').then(res => {
            console.log('chat', res)
            const userId = '1'
            const chatId = '1'
            if (res === null) {
                // If chat does not exist, create it
                const chat: Chat = {
                    id: chatId,
                    title: 'title',
                    createdAt: new Date(),
                    userId: userId,
                    path: './',
                    messages: [],
                    // sharePath: 'sharePath',
                }
                createChat(chat)
                // const aiState = getMutableAIState<typeof AI>()

                // aiState.update({
                //     ...aiState.get(),
                //     messages: [
                //         ...aiState.get().messages
                //     ],
                // })
            } else {
                setAIState({
                    ...aiState,
                    chatId: res.id,
                    messages: res.messages,
                })
            }
        })
    }, [])

    useEffect(() => {
        if (session?.user) {
            if (!path.includes('chat') && messages.length === 1) {
                window.history.replaceState({}, '', `?chat=${id}`)
            }
        }
    }, [id, path, session?.user, messages])

    useEffect(() => {
        const messagesLength = aiState.messages?.length
        if (messagesLength === 2) {
            router.refresh()
        }
    }, [aiState.messages, router])

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

    const {
        messagesRef,
        scrollRef,
        visibilityRef,
        isAtBottom,
        scrollToBottom,
    } = useScrollAnchor()

    const handleSubmit = e => {
        e.preventDefault()
        const projectPath = '/my-path'
        setPath('/my-path')
        createSession(projectPath)
    }

    return (
        <div className="flex flex-col flex-2 relative h-full" ref={scrollRef}>
            <div className="flex-1">
                <div
                    className={cn('pt-4 md:pt-10', className)}
                    ref={messagesRef}
                >
                    {messages.length ? (
                        <ChatList
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
                    {!(messages?.length > 0) && <SuggestionContainer />}
                    <ButtonScrollToBottom
                        isAtBottom={isAtBottom}
                        scrollToBottom={scrollToBottom}
                    />
                    <Input
                        isAtBottom={isAtBottom}
                        scrollToBottom={scrollToBottom}
                    />
                </div>
            )}
            <EventStream sessionId={'1'} />
            <button onClick={handleSubmit} disabled={loading}>
                Create
            </button>
            {_path}
        </div>
    )
}
