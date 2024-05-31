import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatHeader from './chat-header'
import ChatMessagesAndInput from '@/components/chat/chat-messages-and-input/chat-messages-and-input'
import { spawnDevonAgent } from '@/lib/services/agentService'

export default function Chat({
    sessionId,
    viewOnly = false,
    headerIcon,
}: {
    sessionId: string | null
    viewOnly?: boolean
    headerIcon?: JSX.Element
}) {
    const searchParams = useSearchParams()
    const [sessionMachineProps, setSessionMachineProps] = useState<{
        port: number
        name: string
        path: string
    } | null>(null)
    const [backendStarted, setBackendStarted] = useState(false)

    useEffect(() => {
        async function startPythonServer(port: number) {
            try {
                const res: {
                    success: boolean
                    message?: string
                } = await spawnDevonAgent()
                if (res.success) {
                    setBackendStarted(true)
                } else {
                    console.error('Failed to spawn Python agent:', res.message)
                }
            } catch (error) {
                console.error('Failed to spawn Python agent:', error)
            }
        }

        // Get session id and path from url
        const sessionId = searchParams.get('chat')
        const encodedPath = searchParams.get('path')
        if (sessionId && encodedPath) {
            const PORT = 10001
            setSessionMachineProps({
                port: PORT,
                name: sessionId,
                path: decodeURIComponent(encodedPath),
            })
            startPythonServer(PORT)
        }
    }, [])

    return (
        <div className="rounded-lg h-full w-full max-w-4xl flex flex-col flex-2">
            <ChatHeader sessionId={sessionId} headerIcon={headerIcon} />
            <div className="flex-1 overflow-y-auto">
                {!backendStarted && <div>Initializing...</div>}
                {backendStarted && sessionMachineProps && (
                    <ChatMessagesAndInput
                        viewOnly={viewOnly}
                        sessionMachineProps={sessionMachineProps}
                    />
                )}
            </div>
        </div>
    )
}
