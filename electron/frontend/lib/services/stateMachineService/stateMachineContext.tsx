import React, { useState, createContext, useContext, ReactNode } from 'react'
import { useMachine } from '@xstate/react'
import { sessionMachine, eventHandlingLogic } from './stateMachine'
import {
    useSessionMachine,
    useEventHandlingMachine,
    fetchEvents,
} from './stateMachineService'
import { useStartSession } from './useStartSession'

interface StateMachineContextProps {
    startSession: (port: number, name: string, path: string) => void
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
    const { sessionService, startSession } = useStartSession()
    const { state: eventState, service: eventService } =
        useEventHandlingMachine()

    return (
        <StateMachineContext.Provider
            value={{ startSession, sessionService, eventService, fetchEvents }}
        >
            {children}
        </StateMachineContext.Provider>
    )
}

export const useStartSessionContext = () => {
    const context = useContext(StateMachineContext)
    if (context === undefined) {
        throw new Error(
            'useStartSessionContext must be used within a StateMachineProvider'
        )
    }
    return context.startSession
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
