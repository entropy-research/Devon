'use client'
import { useState, useEffect } from 'react'
import Chat from '@/components/chat/chat'
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from '@/components/ui/resizable'
import { ViewMode } from '@/lib/types'
import { createActorContext } from '@xstate/react'
import { newSessionMachine } from '@/lib/services/stateMachineService/stateMachine'
import EditorWidget from '@/components/agent-workspace/agent-tabs/editor-widget/editor-widget'
import TimelineWidget from '@/components/agent-workspace/agent-tabs/timeline-widget'
import { SessionMachineProps } from '@/lib/types'
import { theme, bottomPadding } from '@/lib/config'
import { useSafeStorage } from "@/lib/services/safeStorageService"


export const SessionMachineContext = createActorContext(newSessionMachine)

export const SessionContextProviderComponent = ({
    sessionMachineProps, children
}: {
    sessionMachineProps: SessionMachineProps
    children: React.ReactNode
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
};

export default function Home() {
    const [agentConfig, setAgentConfig] = useState<{
        api_key: undefined | string;
        model: undefined | string;
        prompt_type: undefined | string;
    }>({
        api_key: undefined,
        model: "gpt4-o",
        prompt_type: 'openai'
    })

    const sessionMachineRef = SessionMachineContext.useActorRef()
    const { getApiKey } = useSafeStorage();
    const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Panel)

    useEffect(() => {
        getApiKey("gpt4-o").then((value) => {
            if (value) {
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
        <div className={`w-full flex flex-row ${theme.showChatBorders.enabled ? 'pt-3' : ''}`}>
            <ResizablePanelGroup direction="horizontal">
                <ResizablePanel
                    className={`flex ${viewMode === ViewMode.Panel ? 'flex-row' : 'flex-col'} w-full relative justify-center ${theme.showChatBorders.enabled ? bottomPadding : ''}`}
                >
                    {/* <SidebarItem
                        text="Settings"
                        icon={<Settings className="text-primary" />}
                        active={true}
                        alert={false}
                        route="/settings"
                        expanded={true}
                    /> */}
                    <Chat
                        sessionId={"UI"}
                    />
                </ResizablePanel>
                <ResizableHandle className={theme.showChatBorders.enabled ? "w-[9px]" : ''} />
                <ResizablePanel className="flex-col w-full hidden md:flex">
                    <EditorWidget chatId={"UI"} />
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    )
}