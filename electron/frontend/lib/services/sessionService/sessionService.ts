import axios from 'axios'

export const createEventSource = url => {
    const eventSource = new EventSource(url)

    return {
        onMessage: callback =>
            (eventSource.onmessage = event => callback(event)),
        onError: callback => (eventSource.onerror = event => callback(event)),
        close: () => eventSource.close(),
    }
}

export const fetchSessionState = async (backendUrl, sessionId) => {
    if (!backendUrl || !sessionId) {
        return null
    }
    const { data } = await axios.get(
        `${backendUrl}/session/${encodeURIComponent(sessionId)}/state`
    )
    return data
}

// Function to fetch session events
export const fetchSessionEvents = async sessionId => {
    // const { data } = await axios.get(
    //     `${BACKEND_URL}/session/${encodeURIComponent(sessionId)}/events`
    // )
    return []
}
