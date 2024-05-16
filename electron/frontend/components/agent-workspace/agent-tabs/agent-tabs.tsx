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
}: {
    viewMode: ViewMode
    chatProps: ChatProps
}) {
    return (
        <>
            {viewMode === ViewMode.Panel ? (
                <div className="flex gap-5 w-full h-full justify-around">
                    <PlannerWidget />
                    <TimelineWidget />
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
