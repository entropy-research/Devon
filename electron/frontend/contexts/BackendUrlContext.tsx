import React, { createContext, useContext, useEffect, useState } from 'react'
import { BACKEND_URL } from '@/lib/config'

const BackendUrlContext = createContext('')

export const BackendUrlProvider = ({ children }) => {
    const [backendUrl, setBackendUrl] = useState(BACKEND_URL) // Default url to 8000

    useEffect(() => {
        const portHandler = port => {
            setBackendUrl(`http://localhost:${port}`)
        }
        window.api.receive('server-port', portHandler)

        return () => {
            window.api.removeAllListeners('server-port')
        }
    }, [])

    return (
        <BackendUrlContext.Provider value={backendUrl}>
            {children}
        </BackendUrlContext.Provider>
    )
}

export const useBackendUrl = () => {
    // const context = useContext(BackendUrlContext)
    // if (context === null) {
    //     throw new Error(
    //         'useBackendUrl must be used within a BackendUrlProvider'
    //     )
    // }
    // return context
    return BACKEND_URL
}
