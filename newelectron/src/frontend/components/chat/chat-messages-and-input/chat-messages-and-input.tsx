'use client'
import { Session } from '@/lib/chat.types'
import { useScrollAnchor } from '@/lib/hooks/chat.use-scroll-anchor'
import ChatMessages from './messages/chat.messages'
import Input from './input/input'
import { SessionMachineContext } from '@/home'
import { Skeleton } from '@/components/ui/skeleton'

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
    loading,
    sessionId
    // sessionMachineProps,
}: {
    viewOnly: boolean
    loading: boolean
    sessionId: string
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

    // const searchParams = useSearchParams()
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

    const state = SessionMachineContext.useSelector(state => state)

    const eventState = SessionMachineContext.useSelector(
        state => state.context.serverEventContext
    )

    let messages = eventState.messages

    if (!state.matches('running')) {
        status = 'Initializing...'
    } else if (eventState.modelLoading) {
        status = 'Waiting for Devon...'
    } else if (eventState.userRequest) {
        status = 'Type your message:'
    } else {
        status = 'Interrupt:'
    }

    // useEffect(() => {
    //     missingKeys?.map(key => {
    //         toast({
    //             title: `Missing ${key} environment variable!`,
    //         })
    //     })
    // }, [toast, missingKeys])

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
                {!state.matches('running') ? (
                    <LoadingSkeleton />
                ) : (
                    messages &&
                    messages.length > 0 && (
                        <ChatMessages
                            messages={messages}
                            spinning={eventState.modelLoading}
                        />
                    )
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
                        eventContext={eventState}
                        loading={!state.matches('running')}
                        sessionId={sessionId}
                    />
                </div>
            </div>
            {/* )} */}
        </div>
    )
}

const LoadingSkeleton = () => {
    return (
        <>
            <div className="flex flex-col flex-2 relative h-full overflow-y-auto mx-8 mt-8 mr-10">
                <div className="flex-1">
                    <div className="mb-8">
                        <div className="flex gap-5">
                            <Skeleton className="w-[32px] h-[32px]" />
                            <div className="w-full flex flex-col justify-between">
                                <Skeleton className="w-full h-[12px] rounded-[4px]" />
                                <Skeleton className="w-2/3 h-[12px] rounded-[4px] bg-[#333333]" />
                            </div>
                        </div>
                    </div>
                    <div className="mb-8">
                        <div className="flex gap-5">
                            <Skeleton className="w-[32px] h-[32px]" />
                            <div className="w-full flex flex-col justify-between">
                                <Skeleton className="w-full h-[12px] rounded-[4px]" />
                                <Skeleton className="w-1/3 h-[12px] rounded-[4px] bg-[#333333]" />
                            </div>
                        </div>
                    </div>
                    <div className="mb-8">
                        <div className="flex gap-5">
                            <Skeleton className="w-[32px] h-[32px]" />
                            <div className="w-full flex flex-col justify-between">
                                <Skeleton className="w-full h-[12px] rounded-[4px]" />
                                <Skeleton className="w-4/5 h-[12px] rounded-[4px] bg-[#333333]" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}
