import { useQuery } from 'react-query'
import axios from 'axios'
import { useBackendUrl } from '@/contexts/BackendUrlContext';
// const backendUrl = useBackendUrl()
import { BACKEND_URL } from '@/lib/config'

// Function to fetch session events
export const fetchSessionEvents = async sessionId => {
    const { data } = await axios.get(
        `${BACKEND_URL}/session/${encodeURIComponent(sessionId)}/events`
    )
    return data
}

// Custom hook using React Query
const useFetchSessionEvents = sessionId => {
    return useQuery(
        ['sessionEvents', sessionId],
        () => fetchSessionEvents(sessionId),
        {
            enabled: !!sessionId, // This ensures the query only runs when sessionId is available
        }
    )
}

export default useFetchSessionEvents
