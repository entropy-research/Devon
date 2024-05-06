'use client'
import React, { useEffect } from 'react'
import useFetchSessionEvents from '@/lib/services/sessionService/use-fetch-session-events'

const SessionEventsDisplay = ({ sessionId, setMessages }) => {
    const {
        data: events,
        isLoading,
        isError,
        error,
    } = useFetchSessionEvents(sessionId)

    useEffect(() => {
        if (isLoading) {
            return
        }
        if (error) {
            console.error('Error loading session events:', error)
        }
        if (events) {
            setMessages(events)
        }
    }, [isLoading, error])

    if (isLoading) return <div>Loading events...</div>
    if (isError) return <div>Error loading events: {error.message}</div>

    return <></>
}

export default SessionEventsDisplay
