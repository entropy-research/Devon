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
    const [messages, setMessages] = useState<MessageType[]>([])
    const {
        // messagesRef,
        scrollRef,
        visibilityRef,
        isAtBottom,
        scrollToBottom,
    } = useScrollAnchor()
    const { toast } = useToast()
    // const [_, setNewChatId] = useLocalStorage('newChatId', id) // TODO prob delete this later

    // Clean later
    const [userRequested, setUserRequested] = useState(false)

    const [modelLoading, setModelLoading] = useState(false)
    const [eventIdx, setEventIdx] = useState(0);

    // TODO: Actually use this to load chat from backend
    useEffect(() => {
        if (session?.user) {
            if (!path.includes('chat') && messages.length === 1) {
                window.history.replaceState({}, '', `?chat=${id}`)
            }
        }
    }, [id, path, session?.user, messages])

    useEffect(() => {
        if (!id || id === 'New') return
        let curIdx = eventIdx
        const intervalId = setInterval(async () => {
			const newEvents = await fetchSessionEvents(id);
            console.log('NEW', eventIdx, newEvents)
			if (newEvents) {
				const newMessages = handleEvents(
					newEvents,
					setUserRequested,
					setModelLoading,
                    () => {}
					// exit,
				);
				for (let i = eventIdx; i < newMessages.length; i++) {
					setMessages(messages => [...messages, newMessages[i] as MessageType]);
					curIdx += 1
				}
			}
            setEventIdx(curIdx);
		}, 2000);

        return () => {
            clearInterval(intervalId)
        }
    }, [eventIdx, id, messages])

    // useEffect(() => {
    //     setNewChatId(id)
    // })

    useEffect(() => {
        missingKeys?.map(key => {
            toast({
                title: `Missing ${key} environment variable!`,
            })
        })
    }, [toast, missingKeys])

    return (
        <div className="flex flex-col flex-2 relative h-full overflow-y-auto" ref={scrollRef}>
            <div className="flex-1">
                {/* <div
                    className={cn('pt-4 md:pt-10 bg-red-500', className)}
                    ref={messagesRef}
                > */}
                    {/* <SessionEventsDisplay
                        sessionId={id}
                        setMessages={setMessages}
                    /> */}
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
                            spinning={modelLoading}
                        />
                    ) : (
                        <></>
                    )}
                    {/* {!viewOnly && <div className="h-[150px]"></div>} */}
                    <div className="h-px w-full" ref={visibilityRef}></div>
                {/* </div> */}
            </div>
            {/* {!viewOnly && ( */}
            <div className="sticky bottom-0 w-full">
                <div className="bg-fade-bottom-to-top pt-20 overflow-hidden rounded-xl -mb-[1px]">
                    {/* <ButtonScrollToBottom
                        isAtBottom={isAtBottom}
                        scrollToBottom={scrollToBottom}
                    /> */}
                    {/* <VercelInput
                        isAtBottom={isAtBottom}
                        scrollToBottom={scrollToBottom}
                    /> */}
                    <RegularInput
                        sessionId={id}
                        isAtBottom={isAtBottom}
                        scrollToBottom={scrollToBottom}
                        setUserRequested={setUserRequested}
                        userRequested={userRequested}
                        modelLoading={modelLoading}
                        viewOnly={viewOnly}
                    />
                </div>
            </div>
            {/* )} */}
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
        | 'EnvironmentRequest'
        | 'EnvironmentResponse'
        | 'ModelRequest'
        | 'ToolRequest'
        | 'UserResponse'
    content: string
    identifier: string | null
}

type MessageType = {
    text: string
    type: 'user' | 'agent' | 'command' | 'tool' | 'task' | 'thought'
}

const handleEvents = (
    events: Event[],
    setUserRequested: (value: boolean) => void,
    setModelLoading: (value: boolean) => void,
    exit: () => void,
) => {
    const messages: MessageType[] = []
    let user_request = false
    let model_loading = false
    let tool_message = ''
    let idx = 0;
	let error = false;

    for (const event of events) {
        if (event.type == 'Stop') {
			// console.log('Devon has left the chat.');
			// exit();
		}
        if (event.type == 'ModelRequest') {
            model_loading = true
        }

        if (event.type == 'ModelResponse') {
            let content = JSON.parse(event.content)
            model_loading = false
            messages.push({ text: content.thought, type: 'thought' })
        }

        if (event.type == 'EnvironmentRequest') {
            tool_message = 'Running command: ' + event.content
        }

        if (event.type == 'EnvironmentResponse') {
            tool_message += '\n> ' + event.content
            messages.push({ text: tool_message, type: 'tool' })
            tool_message = ''
        }

        if (event.type == 'Task') {
            messages.push({ text: event.content, type: 'task' })
        }

        if (event.type == 'Interrupt') {
            // writeLogLine('interrupt: ' + event.content);
            messages.push({ text: event.content, type: 'user' })
        }

        if (event.type == 'UserResponse') {
            messages.push({ text: event.content, type: 'user' })
            user_request = false
        }

        if (event.type == 'UserRequest') {
            messages.push({ text: event.content, type: 'agent' })
            user_request = true
        }
    }
    setUserRequested(user_request)
    setModelLoading(model_loading)
    // return messages.slice(2, messages.length)
    return messages
}
