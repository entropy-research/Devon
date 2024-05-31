import { useState, useEffect } from 'react'
import axios from 'axios'
import { useBackendUrl } from '@/contexts/BackendUrlContext'
import { createEventSource } from './sessionService'

export const useReadSessions = () => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sessions, setSessions] = useState([])

    // Function to fetch session keys
    const fetchSessions = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = await axios.get(`${backendUrl}/session`)
            setSessions(response.data) // Assuming the backend returns an array of session keys
        } catch (err) {
            setError(err.message || 'Unknown error')
            setSessions([]) // Reset session keys on error
        }
        setLoading(false)
    }

    // Effect to fetch sessions when the hook is used
    useEffect(() => {
        fetchSessions()
    }, []) // Empty dependency array to run only once after the component mounts

    return { sessions, loading, error, refreshSessions: fetchSessions }
}

export const useDeleteSession = () => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [response, setResponse] = useState(null)

    // Function to delete a session
    // Note: session is the session id
    const deleteSession = async session => {
        setLoading(true)
        setError(null)
        try {
            const response = await axios.delete(`${backendUrl}/session`, {
                params: { session },
            })
            setResponse(response.data) // Save the response data which might be the updated session list
        } catch (err) {
            setError(err.message || 'Unknown error')
        }
        setLoading(false)
    }

    return { deleteSession, response, loading, error }
}

type EventData = Record<string, any>

export const useEventStream = sessionId => {
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
