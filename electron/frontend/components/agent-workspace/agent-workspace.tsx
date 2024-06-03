import AgentWorkspaceTabs from './agent-tabs/agent-tabs'
import { ViewMode } from '@/lib/types'
import { ChatProps } from '@/lib/chat.types'

export default function AgentWorkspace({
    viewMode,
    toggleViewMode,
    chatProps,
    visibilityProps,
}: {
    viewMode: ViewMode
    toggleViewMode: () => void
    chatProps: ChatProps
    visibilityProps: {
        showPlanner: boolean
        setShowPlanner: (show: boolean) => void
        showTimeline: boolean
        setShowTimeline: (show: boolean) => void
    }
}) {
    return (
        // <div className="h-full flex flex-col overflow-hidden w-full">
        //     <AgentWorkspaceTabs
        //         viewMode={viewMode}
        //         chatProps={chatProps}
        //         visibilityProps={visibilityProps}
        //     />
        // </div>

         <AgentWorkspaceTabs
             viewMode={viewMode}
             chatProps={chatProps}
             visibilityProps={visibilityProps}
         />
    )
}
