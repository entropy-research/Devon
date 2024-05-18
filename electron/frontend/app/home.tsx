'use client'
import { useState } from 'react'
import Chat from '@/components/chat/chat'
import AgentWorkspace from '@/components/agent-workspace/agent-workspace'
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable'
import { ViewMode } from '@/lib/types'
import { ChatProps } from '@/lib/chat.types'
import AgentWorkspaceHeader from '@/components/agent-workspace/agent-header'

export default function Home({ chatProps }: { chatProps: ChatProps }) {
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

    return (
        <>
            <AgentWorkspaceHeader
                toggleViewMode={toggleViewMode}
                visibilityProps={visibilityProps}
            />

            {viewMode === ViewMode.Panel ? (
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
                            className={`transition-all duration-500 ${showPlanner ? 'w-1/2' : 'w-full'}`}
                        >
                            <Chat chatProps={chatProps} />
                        </div>
                        <AgentWorkspace
                            viewMode={viewMode}
                            toggleViewMode={toggleViewMode}
                            chatProps={chatProps}
                            visibilityProps={visibilityProps}
                        />
                    </div>
                </>
            ) : (
                <AgentWorkspace
                    viewMode={viewMode}
                    toggleViewMode={toggleViewMode}
                    chatProps={chatProps}
                    visibilityProps={visibilityProps}
                />
            )}
        </>
    )
}
