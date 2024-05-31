import { useState } from 'react'
import axios from 'axios'
import { useBackendUrl } from '@/contexts/BackendUrlContext';

// Send over user response

export const useCreateResponse = () => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [responseData, setResponseData] = useState(null)

    const createResponse = async (sessionId, response) => {
        setLoading(true)
        setError(null)
        try {
            const result = await axios.post(
                `${backendUrl}/session/${encodeURIComponent(sessionId)}/response?response=${encodeURIComponent(response)}`
            )
            console.log("SENDING RESPONSE", result)
            setResponseData(result.data)
            return result.data
        } catch (error) {
            setError(
                error.response
                    ? error.response.data
                    : 'An unknown error occurred'
            )
            return null
        } finally {
            setLoading(false)
        }
    }

    return {
        createResponse,
        responseData,
        loading,
        error,
    }
}

export const useInterruptSession = () => {
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

