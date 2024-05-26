import React, { createContext, useContext, ReactNode } from 'react'
import {
    useSessionMachine,
    useEventHandlingMachine,
    fetchEvents,
} from './stateMachineService'

interface StateMachineContextProps {
    sessionService: any
    eventService: any
    fetchEvents: (port: number) => Promise<any>
}

const StateMachineContext = createContext<StateMachineContextProps | undefined>(
    undefined
)

interface StateMachineProviderProps {
    children: ReactNode
}

export const StateMachineProvider: React.FC<StateMachineProviderProps> = ({
    children,
}) => {
    const { state: sessionState, service: sessionService } = useSessionMachine()
    const { state: eventState, service: eventService } =
        useEventHandlingMachine()

    return (
        <StateMachineContext.Provider
            value={{ sessionService, eventService, fetchEvents }}
        >
            {children}
        </StateMachineContext.Provider>
    )
}

export const useSessionService = () => {
    const context = useContext(StateMachineContext)
    if (context === undefined) {
        throw new Error(
            'useSessionService must be used within a StateMachineProvider'
        )
    }
    return context.sessionService
}

export const useEventService = () => {
    const context = useContext(StateMachineContext)
    if (context === undefined) {
        throw new Error(
            'useEventService must be used within a StateMachineProvider'
        )
    }
    return context.eventService
}

export const useFetchEvents = () => {
    const context = useContext(StateMachineContext)
    if (context === undefined) {
        throw new Error(
            'useFetchEvents must be used within a StateMachineProvider'
        )
    }
    return context.fetchEvents
}
