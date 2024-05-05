import AgentWorkspaceTabs from './agent-tabs/agent-tabs'
import AgentWorkspaceHeader from './agent-header'
import { ViewMode } from '@/lib/types'

export default function AgentWorkspace({
    viewMode,
    toggleViewMode,
}: {
    viewMode: ViewMode
    toggleViewMode: () => void
}) {
    return (
        <div className="dark:bg-shade rounded-lg h-full w-full flex flex-col px-5 py-6 overflow-hidden">
            <AgentWorkspaceHeader toggleViewMode={toggleViewMode} />
            <div className="flex flex-grow overflow-auto w-full">
                <AgentWorkspaceTabs viewMode={viewMode} />
            </div>
        </div>
    )
}
