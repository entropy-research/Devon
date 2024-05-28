import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Header from './header'
import { SimpleChat } from '@/components/chat/messages-and-input/simple.chat'

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

    useEffect(() => {
        // Get session id and path from url
        const sessionId = searchParams.get('chat')
        const encodedPath = searchParams.get('path')
        if (sessionId && encodedPath) {
            setSessionMachineProps({
                port: 10001,
                name: sessionId,
                path: decodeURIComponent(encodedPath),
            })
        }
    }, [])

    return (
        <div className="rounded-lg h-full w-full max-w-4xl flex flex-col flex-2">
            <Header sessionId={sessionId} headerIcon={headerIcon} />
            <div className="flex-1 overflow-y-auto">
                {sessionMachineProps && (
                    <SimpleChat
                        viewOnly={viewOnly}
                        sessionMachineProps={sessionMachineProps}
                    />
                )}
            </div>
        </div>
    )
}
