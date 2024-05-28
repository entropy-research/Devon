'use client'
import { useState, useEffect } from 'react'
import Chat from '@/components/chat/chat'
import AgentWorkspace from '@/components/agent-workspace/agent-workspace'
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable'
import { ViewMode } from '@/lib/types'
import { ChatProps } from '@/lib/chat.types'
import AgentWorkspaceHeader, {
    ToggleTimelineHeader,
} from '@/components/agent-workspace/agent-header'
import EditorWidget from '@/components/agent-workspace/agent-tabs/editor-widget/editor-widget'
import TimelineWidget from '@/components/agent-workspace/agent-tabs/timeline-widget'
// import ShellWidget from '@/components/agent-workspace/agent-tabs/shell-widget'
import { useSearchParams } from 'next/navigation'

export default function Home() {
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

    return (
        <>
            {/* <AgentWorkspaceHeader
                viewMode={viewMode}
                toggleViewMode={toggleViewMode}
                visibilityProps={visibilityProps}
            /> */}

            {/* {viewMode === ViewMode.Panel ? ( */}
            <>
                {/* <ResizablePanelGroup direction="horizontal">
                        <ResizablePanel className="w-full">
                            <Chat chatProps={chatProps} />
                        </ResizablePanel>
                        <ResizableHandle withHandle className="px-3" />
                        <ResizablePanel>
                            <AgentWorkspace
                                viewMode={viewMode}
                                toggleViewMode={toggleViewMode}
                                chatProps={chatProps}
                                visibilityProps={visibilityProps}
                            />
                        </ResizablePanel>
                    </ResizablePanelGroup> */}
                <div className="w-full flex flex-row">
                    <div
                        className={`flex ${viewMode === ViewMode.Panel ? 'flex-row' : 'flex-col'} w-full relative`}
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
                        {/* <div
                            // Set chat size for now
                            // className={`transition-all duration-500 ${showPlanner ? 'w-1/2' : 'w-full'}`}
                        //     className={`transition-all duration-500 w-[500px] flex justify-center`}
                        // >
                            <Chat chatProps={chatProps} />
                        </div> */}
                        <Chat
                            sessionId={sessionId}
                            // headerIcon={<ToggleTimelineHeader showTimeline={showTimeline} setShowTimeline={setShowTimeline} />}
                        />
                    </div>
                    <div className="flex flex-col w-full">
                        <EditorWidget chatId={sessionId ?? null} />
                    </div>

                    {/* <div className="flex flex-2">
                            <AgentWorkspace
                                viewMode={viewMode}
                                toggleViewMode={toggleViewMode}
                                chatProps={chatProps}
                                visibilityProps={visibilityProps}
                            />
                        </div> */}
                </div>
            </>
            {/* ) : (
                <AgentWorkspace
                    viewMode={viewMode}
                    toggleViewMode={toggleViewMode}
                    chatProps={chatProps}
                    visibilityProps={visibilityProps}
                />
            )} */}
        </>
    )
}
