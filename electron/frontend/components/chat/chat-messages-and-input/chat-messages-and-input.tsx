'use client'
import { useEffect } from 'react'
import { Session } from '@/lib/chat.types'
import { useScrollAnchor } from '@/lib/hooks/chat.use-scroll-anchor'
import { useToast } from '@/components/ui/use-toast'
import ChatMessages from './messages/chat.messages'
import Input from './input/input'
import { useActor, useMachine } from '@xstate/react'
import {
    sessionMachine,
} from '@/lib/services/stateMachineService/stateMachine'
import { useSearchParams } from 'next/navigation'
import { SessionMachineContext } from '@/app/home'

type Message = {
    role: 'user' | 'assistant' | 'system' | 'function' | 'data' | 'tool'
    content: string
    id: string
    name?: string
}

// TODO: Get rid of / correct this type later. Was from old chat component
export interface ChatProps extends React.ComponentProps<'div'> {
    initialMessages?: Message[]
    id?: string
    session?: Session
    missingKeys?: string[]
}

export default function ChatMessagesAndInput({
    viewOnly,
    // sessionMachineProps,
}: {
    viewOnly: boolean
    // sessionMachineProps: {
    //     port: number
    //     name: string
    //     path: string
    // }
}) {
    const {
        // messagesRef,
        scrollRef,
        visibilityRef,
        isAtBottom,
        scrollToBottom,
    } = useScrollAnchor()

    const searchParams = useSearchParams()
    // const [eventState, sendEvent] = useActor(eventHandlingLogic)
    // let messages = eventState.context.messages
    // This inits the state machine and starts the session

    let status = ''

//     const [state] = useMachine(sessionMachine, { input: {
//         host: 'http://localhost:' + sessionMachineProps.port,
//         name: sessionMachineProps.name,
//         path: sessionMachineProps.path,
//         reset: false,
//         },
//     },
// )

    const state = SessionMachineContext.useSelector((state) => state);

    const eventState = SessionMachineContext.useSelector((state) => state.context.serverEventContext);

    // const eventState = state.context.serverEventContext;
    let messages = eventState.messages;

	if (!state.matches('running')) {
		status = 'Initializing...';
	} else if (eventState.modelLoading) {
		status = 'Waiting for Devon...';
	} else if (eventState.userRequest) {
		status = 'Type your message:';
	} else {
		status = 'Interrupt:';
	}

    console.log(state.value,state.context.retryCount)
    console.log(state.context)

    // useEffect(() => {
    //     missingKeys?.map(key => {
    //         toast({
    //             title: `Missing ${key} environment variable!`,
    //         })
    //     })
    // }, [toast, missingKeys])
    console.log(messages)

    return (
        <div
            className="flex flex-col flex-2 relative h-full overflow-y-auto"
            ref={scrollRef}
        >
            <div className="flex-1">
                {/* <div
                    className={cn('pt-4 md:pt-10 bg-red-500', className)}
                    ref={messagesRef}
                > */}
                {messages && messages.length > 0 && (
                    <ChatMessages
                        messages={messages}
                        spinning={eventState.modelLoading}
                    />
                )}
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
                    <Input
                        isAtBottom={isAtBottom}
                        scrollToBottom={scrollToBottom}
                        viewOnly={viewOnly}
                        // isRunning={state.matches('running')}
                        eventContext={eventState}
                    />
                </div>
            </div>
            {/* )} */}
        </div>
    )
}
