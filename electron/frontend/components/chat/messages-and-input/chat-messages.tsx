import { useEffect } from 'react'
import { useActor, useMachine } from '@xstate/react'
import {
    sessionMachine,
    eventHandlingLogic,
} from '@/lib/services/stateMachineService/stateMachine'
import { fetchEvents } from '@/lib/services/stateMachineService/stateMachineService'
import { ChatList2 } from '@/components/vercel-chat/chat-list'
import { useSearchParams } from 'next/navigation'

const ChatMessages = ({
    sessionMachineProps,
}: {
    sessionMachineProps: {
        port: number
        name: string
        path: string
    }
}) => {
    const searchParams = useSearchParams()
    const [eventState, sendEvent] = useActor(eventHandlingLogic)
    let messages = eventState.context.messages
    // This inits the state machine and starts the session
    const [state] = useMachine(sessionMachine, { input: sessionMachineProps })
    let status = ''

    if (!state.matches('running')) {
        status = 'Initializing...'
        console.log(status)
    } else {
        console.log('Running!')
    }
    let eventI = 0

    useEffect(() => {
        const intervalId = setInterval(async () => {
            const _sessionId = searchParams.get('chat')
            if (!_sessionId || _sessionId === 'New') return
            if (state.matches('running')) {
                const newEvents = await fetchEvents(10001, _sessionId)
                if (newEvents) {
                    console.log(newEvents)
                    for (let i = eventI; i < newEvents.length; i++) {
                        sendEvent(newEvents[i])
                        eventI++
                    }
                }
            }
        }, 2000)

        return () => {
            clearInterval(intervalId)
        }
    }, [state])

    return messages?.length ? (
        <ChatList2
            messages={messages}
            isShared={false}
            // spinning={modelLoading}
        />
    ) : (
        <></>
    )
}

export default ChatMessages
