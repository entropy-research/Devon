import { useState } from 'react'
import axios from 'axios'
import { useBackendUrl } from '@/contexts/BackendUrlContext';

const useInterruptSession = () => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [interruptData, setInterruptData] = useState(null)

    const interruptSession = async (sessionId, message) => {
        setLoading(true)
        setError(null)
        try {
            const result = await axios.post(
                `${backendUrl}/session/${encodeURIComponent(sessionId)}/interrupt?message=${encodeURIComponent(message)}`
            )
            setInterruptData(result.data)
            return result.data
        } catch (error) {
            setError(
                error.response
                    ? error.response.data
                    : 'An unknown error occurred'
            )
            return null // Return null to indicate failure
        } finally {
            setLoading(false)
        }
    }

    return {
        interruptSession,
        interruptData,
        loading,
        error,
    }
}

export default useInterruptSession
