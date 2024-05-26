// stateMachineService.ts
import { useMachine, useActor } from '@xstate/react'
import axios from 'axios'
import { sessionMachine, eventHandlingLogic } from './stateMachine'

// Custom hooks to use the machines
export const useSessionMachine = (input: {
    port: number
    name: string
    path: string
}) => {
    const [state, service] = useMachine(sessionMachine, { input })
    return { state, service }
}

export const useEventHandlingMachine = () => {
    // TODO: Fix type later
    const [state, service] = useMachine<any>(eventHandlingLogic)
    return { state, service }
}

// Function to fetch events
export const fetchEvents = async (port: number) => {
    try {
        const response = await axios.get(
            `http://localhost:${port}/session/cli/events`
        )
        return response.data
    } catch (error: any) {
        console.error('Error:', error.message)
    }
}
