import { useRef } from 'react'
import ChatHeader from './components/chat-header'
import { useScrollAnchor } from '@/panels/chat/lib/hooks/chat.use-scroll-anchor'
import ChatMessages from './components/messages/chat-messages'
import ChatInputField from './components/input/chat-input-field'
import { SessionMachineContext } from '@/contexts/session-machine-context'
import { Skeleton } from '@/components/ui/skeleton'

export default function Chat({
    sessionId,
    viewOnly = false,
    headerIcon,
    loading = false,
}: {
    sessionId: string | null
    viewOnly?: boolean
    headerIcon?: JSX.Element
    loading?: boolean
}) {
    const {
        // messagesRef,
        scrollRef,
        visibilityRef,
        isAtBottom,
        scrollToBottom,
    } = useScrollAnchor()

    let status = ''

    const state = SessionMachineContext.useSelector(state => state)

    const eventState = SessionMachineContext.useSelector(
        state => state.context.serverEventContext
    )
    const isPaused = SessionMachineContext.useActorRef()
        .getSnapshot()
        .matches('paused')

    let messages = eventState.messages.slice(2)
    const previousMessagesLengthRef = useRef(messages.length)

    if (
        previousMessagesLengthRef.current &&
        messages.length > previousMessagesLengthRef.current
    ) {
        scrollToBottom()
    }

    if (!state.matches('running')) {
        status = 'Initializing...'
    } else if (eventState.modelLoading) {
        status = 'Waiting for Devon...'
    } else if (eventState.userRequest) {
        status = 'Type your message:'
    } else {
        status = 'Interrupt:'
    }

    return (
        // <div className="rounded-lg h-full w-full max-w-4xl flex flex-col flex-2">
        <div className="rounded-lg h-full w-full flex flex-col flex-2">
            <ChatHeader sessionId={sessionId} headerIcon={headerIcon} />
            <div className="flex-1 overflow-y-auto">
                {/* {!backendStarted && <div>Initializing...</div>} */}
                {/* {backendStarted && sessionMachineProps && ( */}
                {/* {sessionMachineProps && (    */}
                {/* {loading ? (
                    <p>Loading Chat Messages and Input</p>
                ) : ( */}
                <div
                    className="flex flex-col flex-2 relative h-full overflow-y-auto"
                    ref={scrollRef}
                >
                    <div className="flex-1">
                        {/* <div
                    className={cn('pt-4 md:pt-10 bg-red-500', className)}
                    ref={messagesRef}
                > */}
                        {!state.matches('running') &&
                        !state.matches('paused') ? (
                            <LoadingSkeleton />
                        ) : (
                            <ChatMessages
                                messages={messages}
                                spinning={eventState.modelLoading}
                                paused={isPaused}
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
                            <ChatInputField
                                isAtBottom={isAtBottom}
                                scrollToBottom={scrollToBottom}
                                viewOnly={viewOnly}
                                eventContext={eventState}
                                loading={!state.can({ type: 'session.toggle' })}
                                sessionId={sessionId}
                            />
                        </div>
                    </div>
                    {/* )} */}
                </div>
                {/* )} */}
                {/* )} */}
            </div>
        </div>
    )
}

const LoadingSkeleton = () => {
    return (
        <>
            <div className="flex flex-col flex-2 relative h-full overflow-y-auto mx-6 mt-8 mr-10">
                <div className="flex-1">
                    <div className="mb-8">
                        <div className="flex gap-5">
                            <Skeleton className="w-[32px] h-[32px]" />
                            <div className="w-full flex flex-col justify-between">
                                <Skeleton className="w-full h-[12px] rounded-[4px]" />
                                <Skeleton className="w-2/3 h-[12px] rounded-[4px] bg-skeleton bg-opacity-60" />
                            </div>
                        </div>
                    </div>
                    <div className="mb-8">
                        <div className="flex gap-5">
                            <Skeleton className="w-[32px] h-[32px]" />
                            <div className="w-full flex flex-col justify-between">
                                <Skeleton className="w-full h-[12px] rounded-[4px]" />
                                <Skeleton className="w-1/3 h-[12px] rounded-[4px] bg-skeleton bg-opacity-60" />
                            </div>
                        </div>
                    </div>
                    <div className="mb-8">
                        <div className="flex gap-5">
                            <Skeleton className="w-[32px] h-[32px]" />
                            <div className="w-full flex flex-col justify-between">
                                <Skeleton className="w-full h-[12px] rounded-[4px]" />
                                <Skeleton className="w-4/5 h-[12px] rounded-[4px] bg-skeleton bg-opacity-60" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}
