'use client'
import { useEffect, useState } from 'react'
import { Session } from '@/lib/chat.types'
import { Message } from '@/lib/chat/chat.actions'
import { useScrollAnchor } from '@/lib/hooks/chat.use-scroll-anchor'
import { useToast } from '@/components/ui/use-toast'
import ChatMessages from './chat-messages'
import { useSearchParams } from 'next/navigation'
import { RegularInput } from './input'

export interface ChatProps extends React.ComponentProps<'div'> {
    initialMessages?: Message[]
    id?: string
    session?: Session
    missingKeys?: string[]
}

export function SimpleChat({ viewOnly }: { viewOnly: boolean }) {
    const {
        // messagesRef,
        scrollRef,
        visibilityRef,
        isAtBottom,
        scrollToBottom,
    } = useScrollAnchor()
    const { toast } = useToast()
    const searchParams = useSearchParams()
    const [sessionMachineProps, setSessionMachineProps] = useState<any>(null)
    const [userRequested, setUserRequested] = useState(false)
    const [modelLoading, setModelLoading] = useState(false)

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
                {sessionMachineProps?.name && (
                    <ChatMessages sessionMachineProps={sessionMachineProps} />
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
                    <RegularInput
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
        </div>
    )
}
