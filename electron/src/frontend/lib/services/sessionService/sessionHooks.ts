import { useState, useEffect } from 'react'
import axios from 'axios'
import { useBackendUrl } from '@/contexts/backend-url-context'

export async function getSessions(backendUrl: string) {
    if (!backendUrl) {
        return []
    }
    try {
        const response = await axios.get(`${backendUrl}/sessions`)
        return response.data
    } catch (error) {
        console.error('Error fetching sessions:', error)
        return []
    }
}

export const useReadSessions = () => {
    const { backendUrl } = useBackendUrl()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sessions, setSessions] = useState([])

    // Function to fetch session keys
    const fetchSessions = async () => {
        setLoading(true)
        setError(null)

        // Don't fetch if the backendUrl hasn't been set yet
        if (!backendUrl) {
            setLoading(false)
            return
        }
        try {
            const response = await axios.get(`${backendUrl}/sessions`)
            setSessions(response.data)
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
    const { backendUrl } = useBackendUrl()
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
