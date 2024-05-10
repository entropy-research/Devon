import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import ShellWidget from './shell-widget'
import BrowserWidget from './browser-widget'
import EditorWidget from './editor-widget/editor-widget'
import PlannerWidget from './planner-widget'
import Chat from '../../chat/chat'
import { ViewMode } from '@/lib/types'
import { ChatProps } from '@/lib/chat.types'

const tabs = [
    {
        id: 'shell',
        title: 'Shell',
        content: <ShellWidget />,
    },
    {
        id: 'browser',
        title: 'Browser',
        content: <BrowserWidget />,
    },
    {
        id: 'editor',
        title: 'Editor',
        content: <></>,
    },
    {
        id: 'planner',
        title: 'Planner',
        content: <PlannerWidget />,
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
                <PanelView chatProps={chatProps} />
            ) : (
                <GridView chatProps={chatProps} />
            )}
        </>
    )
}

const PanelView = ({ chatProps }: { chatProps: ChatProps }) => (
    <Tabs defaultValue="shell" className="flex flex-col h-full">
        <TabsList className="gap-1 justify-start">
            {tabs.map(({ id, title }) => (
                <TabsTrigger key={id} value={id}>
                    {title}
                </TabsTrigger>
            ))}
        </TabsList>
        {tabs.map(({ id, content }) => (
            <ContentContainer key={id} value={id}>
                {id === 'editor' ? (
                    <EditorWidget chatId={chatProps.id ?? null} />
                ) : (
                    content
                )}
            </ContentContainer>
        ))}
    </Tabs>
)

const GridView = ({ chatProps }: { chatProps: ChatProps }) => (
    <div className="h-full w-full flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4 h-1/2">
            {gridTabs.slice(0, 2).map(({ id, content }) => (
                <GridContentContainer key={id}>
                    {id === 'chat' ? (
                        <Chat viewOnly chatProps={chatProps} />
                    ) : (
                        content
                    )}
                </GridContentContainer>
            ))}
        </div>
        <div className="grid grid-cols-2 gap-4 h-1/2 block">
            {gridTabs.slice(2, 4).map(({ id, content }) => (
                <GridContentContainer key={id}>
                    {id === 'editor' ? (
                        <EditorWidget chatId={chatProps.id ?? null} />
                    ) : (
                        content
                    )}
                </GridContentContainer>
            ))}
        </div>
    </div>
)

const GridContentContainer = ({ children }: { children: React.ReactNode }) => (
    <div className="border-2 rounded-lg overflow-y-scroll bg-night border-outline-night h-full flex flex-col flex-grow overflow-auto w-full">
        {children}
    </div>
)
const ContentContainer = ({
    value,
    children,
}: {
    value: string
    children: React.ReactNode
}) => (
    <TabsContent
        value={value}
        className="border-2 rounded-lg h-full bg-night border-outline-night"
    >
        <div className="flex flex-col flex-grow overflow-auto w-full h-full">
            {children}
        </div>
    </TabsContent>
)
