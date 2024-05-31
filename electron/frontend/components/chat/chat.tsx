import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatHeader from './chat-header'
import ChatMessagesAndInput from '@/components/chat/chat-messages-and-input/chat-messages-and-input'
import { spawnDevonAgent } from '@/lib/services/agentService'

export default function Chat({
    sessionId,
    viewOnly = false,
    headerIcon,
    port,
}: {
    sessionId: string | null
    viewOnly?: boolean
    headerIcon?: JSX.Element,
    port: number
}) {

    const searchParams = useSearchParams()

    // const [sessionMachineProps, setSessionMachineProps] = useState<{
    //     port: number
    //     name: string
    //     path: string
    // } | null>(null)


    // let sessionName = searchParams.get('chat')
    // const encodedPath = searchParams.get('path')
    // console.log(sessionName,encodedPath)
    // useEffect(() => {

    //     if (sessionName && encodedPath) {
    //         const stateMachineProps = {
    //             port: port,
    //             name: sessionName,
    //             path: decodeURIComponent(encodedPath),
    //         }
    //         setSessionMachineProps(stateMachineProps)
    //     }
    // }, [sessionName, encodedPath,port])
    


    return (
        <div className="rounded-lg h-full w-full max-w-4xl flex flex-col flex-2">
            <ChatHeader sessionId={sessionId} headerIcon={headerIcon} />
            <div className="flex-1 overflow-y-auto">
                {/* {!backendStarted && <div>Initializing...</div>} */}
                {/* {backendStarted && sessionMachineProps && ( */}
                {/* {sessionMachineProps && (    */}
                <ChatMessagesAndInput
                    viewOnly={viewOnly}
                    // sessionMachineProps={sessionMachineProps}
                />
                {/* )} */}
            </div>
        </div>
    )
}
