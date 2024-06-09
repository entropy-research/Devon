'use client'
import { useState, useEffect } from 'react'
import Chat from '@/components/chat/chat'
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable'
import { ViewMode } from '@/lib/types'
import { useSearchParams } from 'next/navigation'
import { createActorContext } from '@xstate/react'
import { newSessionMachine } from '@/lib/services/stateMachineService/stateMachine'
import { useSafeStorage } from "@/lib/services/safeStorageService"
import EditorWidget from '@/components/agent-workspace/agent-tabs/editor-widget/editor-widget'

export const SessionMachineContext = createActorContext(newSessionMachine)

export const SessionContextProviderComponent = ({
    sessionMachineProps, children
}: {
    sessionMachineProps: {
        host: string
        name: string
    },
    children: any
}) => {
    return (
        <SessionMachineContext.Provider
            options={{
                input: {
                    host: sessionMachineProps.host,
                    name: sessionMachineProps.name,
                    reset: true
                },
            }}
        >
            {children}
        </SessionMachineContext.Provider>
    )
}

export default function Home() {
    const [ agentConfig, setAgentConfig ] = useState<{
        api_key: undefined | string;
        model: undefined | string;
        prompt_type: undefined | string;
    }>({
        api_key: undefined,
        model: "gpt4-o",
        prompt_type: 'openai'
    })

    const sessionMachineRef = SessionMachineContext.useActorRef()

    const searchParams = useSearchParams();
    const { getApiKey } = useSafeStorage();
    const [sessionId, setSessionId] = useState<string | null>(null)
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

    // Basically listens for change
    useEffect(() => {
        const chatId = searchParams.get('chat')
        // Handle when the chatId is 'New', which means the session hasn't been made yet, and we should prompt the select project modal
        if (chatId && chatId === 'New') {
            return
        }

        if (!chatId) {
            return
        }
        setSessionId(chatId)
    }, [])

    useEffect(() => {
        getApiKey("gpt4-o").then((value) => {
            if( value ){
                sessionMachineRef.send({
                    type: "session.begin",
                    agentConfig: {
                        ...agentConfig,
                        api_key: value
                    }
                })
            }
        })
    }, [])

    let state = SessionMachineContext.useSelector(state => state)
    console.log(state.context.serverEventContext)
    // Get session id and path from url
    return (
        <div className="w-full flex flex-row">
            <ResizablePanelGroup direction="horizontal">
                <ResizablePanel
                    className={`flex ${viewMode === ViewMode.Panel ? 'flex-row' : 'flex-col'} w-full relative justify-center`}
                >
                    {/* {showTimeline && (
                        <TimelineWidget
                            className={
                                viewMode === ViewMode.Panel
                                    ? 'w-[275px]'
                                    : 'w-full overflow-hidden'
                            }
                        />
                    )} */}
                    {/* {port ? ( */}
                    <Chat
                        sessionId={sessionId}
                        // port={sessionMachineProps.port}
                        // sessionMachineProps={sessionMachineProps}
                        // headerIcon={<ToggleTimelineHeader showTimeline={showTimeline} setShowTimeline={setShowTimeline} />}
                    />
                    {/* ) : ( */}
                    {/* <div>Loading...</div> */}
                    {/* )} */}
                </ResizablePanel>
                <ResizableHandle className="" />
                <ResizablePanel className="flex-col w-full hidden md:flex">
                    <EditorWidget chatId={sessionId ?? null} />
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    )
}
