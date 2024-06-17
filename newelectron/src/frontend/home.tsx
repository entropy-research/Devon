
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

    // const sessionMachineRef = SessionMachineContext.useActorRef()
    // const { getApiKey } = useSafeStorage();
    // const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Panel)

    // useEffect(() => {

    //     getApiKey(model).then((value) => {
    //         if (value) {
    //             console.log("CONIG",agentConfig)
    //             sessionMachineRef.send({
    //                 type: "session.begin",
    //                 agentConfig: {
    //                     ...agentConfig,
    //                     api_key: value
    //                 }
    //             })
    //         }
    //     })
    // }, [])



    // const state = SessionMachineContext.useSelector(state => state)
    // console.log(state.context.serverEventContext)
    // Get session id and path from url
    return (
        <div className="w-full flex flex-row">
            <ResizablePanelGroup direction="horizontal">
                <ResizablePanel
                    className={`flex ${ViewMode.Panel === ViewMode.Panel ? 'flex-row' : 'flex-col'} w-full relative justify-center`}
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
                <ResizableHandle className="" />
                <ResizablePanel className="flex-col w-full hidden md:flex">
                    <EditorWidget chatId={"UI"} />
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    )
}
