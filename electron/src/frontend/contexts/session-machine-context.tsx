import { createActorContext } from '@xstate/react'
import { newSessionMachine } from '@/lib/services/stateMachineService/stateMachine'

export const SessionMachineContext = createActorContext(newSessionMachine)

export const SessionContextProviderComponent = ({
    sessionMachineProps,
    children,
}: {
    sessionMachineProps: {
        host: string
        name: string
    }
    children: any
}) => {
    return (
        <SessionMachineContext.Provider
            options={{
                input: {
                    host: sessionMachineProps.host,
                    name: sessionMachineProps.name,
                    reset: true,
                },
            }}
        >
            {children}
        </SessionMachineContext.Provider>
    )
}
