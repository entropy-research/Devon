// import { useEffect, useState } from 'react'
import ChatHeader from './chat-header'
import ChatMessagesAndInput from '@/components/chat/chat-messages-and-input/chat-messages-and-input'

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
    // const searchParams = useSearchParams()

    return (
        <div className="rounded-lg h-full w-full max-w-4xl flex flex-col flex-2">
            <ChatHeader sessionId={sessionId} headerIcon={headerIcon} />
            <div className="flex-1 overflow-y-auto">
                {/* {!backendStarted && <div>Initializing...</div>} */}
                {/* {backendStarted && sessionMachineProps && ( */}
                {/* {sessionMachineProps && (    */}
                {/* {loading ? (
                    <p>Loading Chat Messages and Input</p>
                ) : ( */}
                    <ChatMessagesAndInput
                        viewOnly={viewOnly}
                        loading={loading}
                        sessionId={sessionId as string}
                        // sessionMachineProps={sessionMachineProps}
                    />
                {/* )} */}
                {/* )} */}
            </div>
        </div>
    )
}
