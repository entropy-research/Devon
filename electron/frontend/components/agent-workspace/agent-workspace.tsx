import AgentWorkspaceTabs from './agent-tabs/agent-tabs'
import AgentWorkspaceHeader from './agent-header'
import { ViewMode } from '@/lib/types'
import { ChatProps } from '@/lib/chat.types'


export default function AgentWorkspace({
    viewMode,
    toggleViewMode,
    chatProps

}: {
    viewMode: ViewMode
    toggleViewMode: () => void
    chatProps: ChatProps
}) {
    return (
        <div className="dark:bg-shade rounded-lg h-full w-full flex flex-col px-5 py-6 overflow-hidden">
            <AgentWorkspaceHeader toggleViewMode={toggleViewMode} />
            <div className="flex flex-grow overflow-auto w-full">
                <AgentWorkspaceTabs viewMode={viewMode} chatProps={chatProps} />
            </div>
        </div>
    )
}
