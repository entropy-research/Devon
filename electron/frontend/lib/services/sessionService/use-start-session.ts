import { useState } from 'react'
import axios from 'axios'
import { useBackendUrl } from '@/contexts/BackendUrlContext';

const useStartSession = () => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sessionStarted, setSessionStarted] = useState(false)

    const startSession = async (sessionId: string) => {
        setLoading(true)
        setError(null)
        try {
            if (!sessionId) throw new Error('Session ID is required')
            // If a session is already started, it will return a 304
            const response = await axios.post(
                `${backendUrl}/session/${encodeURIComponent(sessionId)}/start`
            )
            setSessionStarted(true)
        } catch (err) {
            if (err.response && err.response.status === 304) {
                setSessionStarted(true)
                return 'Session already running'
            }
            setError(err.message || 'Unknown error')
            setSessionStarted(false)
            throw new Error(
                err.response
                    ? err.response.data.detail
                    : 'An unknown error occurred'
            )
        } finally {
            setLoading(false)
        }
    }

    return { startSession, sessionStarted, loading, error }
}

export default useStartSession
