import { useEffect, useState } from 'react'
import { createEventSource } from './sessionService'

type EventData = Record<string, any>

const BACKEND_URL = 'http://localhost:8000'

const useEventStream = sessionId => {
    const [events, setEvents] = useState<EventData[]>([])

    useEffect(() => {
        if (!sessionId) return // Guard to ensure sessionId is provided

        const eventStreamUrl = `${BACKEND_URL}/${sessionId}/events/stream`
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
