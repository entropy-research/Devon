import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import ShellWidget from './shell-widget'
import BrowserWidget from './browser-widget'
import EditorWidget from './editor-widget'
import PlannerWidget from './planner-widget'
import Chat from '../../chat/chat'
import { ViewMode } from '@/lib/types'
import { CodeEditorContextProvider } from '@/contexts/CodeEditorContext'
const files = [
    {
        id: 1,
        name: 'main.py',
        language: 'python',
        value: "# Devon's Code Editor",
    },
    {
        id: 2,
        name: 'script.js',
        language: 'javascript',
        value: "console.log('Hello, world!');",
    },
    {
        id: 3,
        name: 'style.css',
        language: 'css',
        value: 'body { background-color: #f0f0f0; }',
    },
    {
        id: 4,
        name: 'index.html',
        language: 'html',
        value: '<h1>Hello, world!</h1>',
    },
    // {
    //     id: 5,
    //     name: 'README.md',
    //     language: 'markdown',
    //     value: '# Welcome to Devon!',
    // },
]

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
        content: (
            <CodeEditorContextProvider tabFiles={files}>
                <EditorWidget />
            </CodeEditorContextProvider>
        ),
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
        content: <Chat viewOnly />,
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
        content: (
            <CodeEditorContextProvider tabFiles={files}>
                <EditorWidget />
            </CodeEditorContextProvider>
        ),
    },
    // {
    //     id: 'planner',
    //     title: 'Planner',
    //     content: <Planner />,
    // },
]

export default function AgentWorkspaceTabs({
    viewMode,
}: {
    viewMode: ViewMode
}) {
    return <>{viewMode === ViewMode.Panel ? <PanelView /> : <GridView />}</>
}

const PanelView = () => (
    <Tabs defaultValue="shell" className="flex grow flex-col">
        <TabsList className="gap-1 justify-start">
            {tabs.map(({ id, title }) => (
                <TabsTrigger key={id} value={id}>
                    {title}
                </TabsTrigger>
            ))}
        </TabsList>
        {tabs.map(({ id, content }) => (
            <ContentContainer key={id} value={id}>
                {content}
            </ContentContainer>
        ))}
    </Tabs>
)

const GridView = () => (
    <div className="h-full w-full flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-4 h-1/2">
            {gridTabs.slice(0, 2).map(({ id, content }) => (
                <GridContentContainer key={id}>{content}</GridContentContainer>
            ))}
        </div>
        <div className="grid grid-cols-2 gap-4 h-1/2 block">
            {gridTabs.slice(2, 4).map(({ id, content }) => (
                <GridContentContainer key={id}>{content}</GridContentContainer>
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
