import AgentWorkspaceTabs from './agent-tabs/agent-tabs'
import { ViewMode } from '@/lib/types'
import { ChatProps } from '@/lib/chat.types'

export default function AgentWorkspace({
    viewMode,
    toggleViewMode,
    chatProps,
}: {
    viewMode: ViewMode
    toggleViewMode: () => void
    chatProps: ChatProps
}) {
    return (
        <div className="h-full w-full flex flex-col overflow-hidden">
            <AgentWorkspaceTabs viewMode={viewMode} chatProps={chatProps} />
        </div>
    )
}
