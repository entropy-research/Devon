import { useQuery } from 'react-query'
import axios from 'axios'

const BACKEND_URL = 'http://localhost:8000'

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
