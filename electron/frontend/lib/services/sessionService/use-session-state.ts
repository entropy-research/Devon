import { useState } from 'react'
import axios from 'axios'

const BACKEND_URL = 'http://localhost:8000'

export const fetchSessionState = async sessionId => {
    const { data } = await axios.get(
        `${BACKEND_URL}/session/${encodeURIComponent(sessionId)}/state`
    )
    return data
}

const useSessionState = sessionId => {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sessionState, setSessionState] = useState(null)

    const updateSessionState = async () => {
        setLoading(true)
        setError(null)
        if (!sessionId || sessionId === 'New') return
        try {
            const response = await axios.post(
                `${BACKEND_URL}/session/${encodeURIComponent(sessionId)}/state`
            )
            setSessionState(response.data)
        } catch (err) {
            setError(err.response ? err.response.data.detail : 'Unknown error')
            setSessionState(null)
        } finally {
            setLoading(false)
        }
    }

    return { sessionState, loading, error, updateSessionState }
}

export default useSessionState
