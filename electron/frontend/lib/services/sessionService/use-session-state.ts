import { useState } from 'react'
import axios from 'axios'
import { useBackendUrl } from '@/contexts/BackendUrlContext';
// const backendUrl = useBackendUrl()
const BACKEND_URL = 'http://localhost:10001' // TODO: Change this to the actual backend URL

export const fetchSessionState = async sessionId => {
    const { data } = await axios.get(
        `${BACKEND_URL}/session/${encodeURIComponent(sessionId)}/state`
    )
    return data
}

const useSessionState = sessionId => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sessionState, setSessionState] = useState(null)

    const updateSessionState = async () => {
        setLoading(true)
        setError(null)
        if (!sessionId || sessionId === 'New') return
        try {
            const response = await axios.post(
                `${backendUrl}/session/${encodeURIComponent(sessionId)}/state`
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
