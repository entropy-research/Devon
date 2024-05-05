import { useState } from 'react'
import axios from 'axios'
import { nanoid } from '@/lib/chat.utils'

const BACKEND_URL = 'http://localhost:8000'

const useCreateSession = () => {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [sessionId, setSessionId] = useState('')

    const createSession = async (session, path) => {
        setLoading(true)
        setError(null)
        setSessionId(nanoid())
        session = 'mysession'
        path = 'mypath'
        try {
            const response = await axios.post(`${BACKEND_URL}/session`, {
                session,
                path,
            })
            setSessionId(response.data)
        } catch (err) {
            setError(err.message || 'Unknown error')
        }
        setLoading(false)
    }

    return { createSession, sessionId, loading, error }
}

export default useCreateSession
