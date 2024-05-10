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

export default function Home({ chatProps }: { chatProps: ChatProps }) {
    const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Panel)

    const toggleViewMode = () => {
        setViewMode(
            viewMode === ViewMode.Panel ? ViewMode.Grid : ViewMode.Panel
        )
    }

    return (
        <>
            {viewMode === ViewMode.Panel ? (
                <ResizablePanelGroup direction="horizontal">
                    <ResizablePanel>
                        <Chat chatProps={chatProps} />
                    </ResizablePanel>
                    <ResizableHandle withHandle className="px-3" />
                    <ResizablePanel className="w-full">
                        <AgentWorkspace
                            viewMode={viewMode}
                            toggleViewMode={toggleViewMode}
                            chatProps={chatProps}
                        />
                    </ResizablePanel>
                </ResizablePanelGroup>
            ) : (
                <AgentWorkspace
                    viewMode={viewMode}
                    toggleViewMode={toggleViewMode}
                    chatProps={chatProps}
                />
            )}
        </>
    )
}
