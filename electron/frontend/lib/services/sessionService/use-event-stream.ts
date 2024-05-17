import { useEffect, useState } from 'react'
import { createEventSource } from './sessionService'
import { useBackendUrl } from '@/contexts/BackendUrlContext';

type EventData = Record<string, any>

const useEventStream = sessionId => {
    const backendUrl = useBackendUrl()
    const [events, setEvents] = useState<EventData[]>([])

    useEffect(() => {
        if (!sessionId) return // Guard to ensure sessionId is provided

        const eventStreamUrl = `${backendUrl}/${sessionId}/events/stream`
        const eventSource = createEventSource(eventStreamUrl)

        eventSource.onMessage(event => {
            const newEvent: EventData = JSON.parse(event.data)
            setEvents((prevEvents: EventData[]) => [...prevEvents, newEvent])
        })

        eventSource.onError(error => {
            console.error('EventSource failed:', error)
            eventSource.close()
        })

        return () => eventSource.close() // Cleanup function to close the event source
    }, [sessionId])

    return events
}

export default useEventStream
