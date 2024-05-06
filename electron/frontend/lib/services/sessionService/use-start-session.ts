import { useState } from 'react'
import axios from 'axios'

const BACKEND_URL = 'http://localhost:8000'

const useStartSession = () => {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sessionStarted, setSessionStarted] = useState(false)

    const startSession = async (sessionId: string) => {
        setLoading(true)
        setError(null)
        try {
            if (!sessionId) throw new Error('Session ID is required')
            const response = await axios.post(
                `${BACKEND_URL}/session/${encodeURIComponent(sessionId)}/start`
            )
            setSessionStarted(true) // Assuming you might want to know if the session was started successfully
        } catch (err) {
            setError(err.message || 'Unknown error')
            setSessionStarted(false)
        } finally {
            setLoading(false)
        }
    }

    return { startSession, sessionStarted, loading, error }
}

export default useStartSession
