import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import ShellWidget from './shell-widget'
import BrowserWidget from './browser-widget'
import EditorWidget from './editor-widget/editor-widget'
import TimelineWidget from './timeline-widget'
import PlannerWidget from './planner-widget'
import Chat from '../../chat/chat'
import { ViewMode } from '@/lib/types'
import { ChatProps } from '@/lib/chat.types'

const observeTabs = [
    {
        id: 'planner',
        title: 'Planner',
        content: <PlannerWidget />,
    },
    {
        id: 'timeline',
        title: 'Minimap',
        content: <TimelineWidget />,
    },
]

const gridTabs = [
    {
        id: 'chat',
        content: <></>,
    },
    {
        id: 'shell',
        content: <ShellWidget />,
    },
    {
        id: 'browser',
        content: <BrowserWidget />,
    },
    {
        id: 'editor',
        content: <></>,
    },
    // {
    //     id: 'planner',
    //     title: 'Planner',
    //     content: <Planner />,
    // },
]

export default function AgentWorkspaceTabs({
    viewMode,
    chatProps,
    visibilityProps: {
        showPlanner,
        setShowPlanner,
        showTimeline,
        setShowTimeline,
    },
}: {
    viewMode: ViewMode
    chatProps: ChatProps
    visibilityProps: {
        showPlanner: boolean
        setShowPlanner: (show: boolean) => void
        showTimeline: boolean
        setShowTimeline: (show: boolean) => void
    }
}) {
    return (
        <>
            {viewMode === ViewMode.Panel ? (
                <div className="flex gap-5 w-full h-full justify-around pr-5 flex-1">
                    {showPlanner && <PlannerWidget />}
                    {showTimeline && <TimelineWidget />}
                </div>
            ) : (
                <GridView chatProps={chatProps} />
            )}
        </>
    )
}

const GridView = ({ chatProps }: { chatProps: ChatProps }) => (
    <div className="h-full w-full flex flex-row gap-4">
        <div className="flex flex-col flex-1">
            <EditorWidget chatId={chatProps.id ?? null} />
        </div>
        <TimelineWidget />
    </div>
)
