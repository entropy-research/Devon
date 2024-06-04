'use client'
import { useState, useEffect } from 'react'
import Chat from '@/components/chat/chat'
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable'
import { ViewMode } from '@/lib/types'
import EditorWidget from '@/components/agent-workspace/agent-tabs/editor-widget/editor-widget'
import TimelineWidget from '@/components/agent-workspace/agent-tabs/timeline-widget'
import { useSearchParams } from 'next/navigation'
import { createActorContext, useMachine } from '@xstate/react'
import { sessionMachine } from '@/lib/services/stateMachineService/stateMachine'
import { SessionMachineProps } from '@/lib/types'
import { theme, bottomPadding } from '@/lib/config'

export const SessionMachineContext = createActorContext(sessionMachine)

export default function Home({
    sessionMachineProps,
}: {
    sessionMachineProps: SessionMachineProps
}) {
    const searchParams = useSearchParams()
    const [sessionId, setSessionId] = useState<string | null>(null)
    const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Panel)

    const [showPlanner, setShowPlanner] = useState<boolean>(true)
    const [showTimeline, setShowTimeline] = useState<boolean>(true)

    const toggleViewMode = () => {
        setViewMode(
            viewMode === ViewMode.Panel ? ViewMode.Grid : ViewMode.Panel
        )
    }

    const visibilityProps = {
        showPlanner,
        setShowPlanner,
        showTimeline,
        setShowTimeline,
    }

    const [isAgentWorkspaceVisible, setAgentWorkspaceVisible] = useState(true)

    const toggleAgentWorkspace = () => {
        setAgentWorkspaceVisible(!isAgentWorkspaceVisible)
    }

    // Basically listens for change
    useEffect(() => {
        const chatId = searchParams.get('chat')
        // Handle when the chatId is 'New', which means the session hasn't been made yet, and we should prompt the select project modal
        if (chatId && chatId === 'New') {
            return
        }

        if (!chatId) {
            return
        }
        setSessionId(chatId)
    }, [])

    // Get session id and path from url
    return (
        <SessionMachineContext.Provider
            options={{
                input: {
                    host: 'http://localhost:' + sessionMachineProps.port,
                    name: sessionMachineProps.name,
                    path: sessionMachineProps.path,
                    reset: true,
                },
            }}
        >
            <div
                className={`w-full flex flex-row ${theme.showChatBorders.enabled ? 'pt-3' : ''}`}
            >
                <ResizablePanelGroup direction="horizontal">
                    <ResizablePanel
                        className={`flex ${viewMode === ViewMode.Panel ? 'flex-row' : 'flex-col'} w-full relative justify-center ${theme.showChatBorders.enabled ? bottomPadding : ''}`}
                    >
                        {/* {showTimeline && (
                            <TimelineWidget
                                className={
                                    viewMode === ViewMode.Panel
                                        ? 'w-[275px]'
                                        : 'w-full overflow-hidden'
                                }
                            />
                        )} */}
                        <Chat sessionId={sessionId} />
                    </ResizablePanel>
                    <ResizableHandle className={theme.showChatBorders.enabled ? "w-[9px]" : ''} />
                    <ResizablePanel className="flex-col w-full hidden md:flex">
                        <EditorWidget chatId={sessionId ?? null} />
                    </ResizablePanel>
                </ResizablePanelGroup>
            </div>
        </SessionMachineContext.Provider>
    )
}
