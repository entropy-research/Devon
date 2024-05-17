import React, { createContext, useContext, useEffect, useState } from 'react'

const BackendUrlContext = createContext('')

export const BackendUrlProvider = ({ children }) => {
    const [backendUrl, setBackendUrl] = useState('http://localhost:10001') // Default url to 8000

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
    const context = useContext(BackendUrlContext)
    if (context === null) {
        throw new Error(
            'useBackendUrl must be used within a BackendUrlProvider'
        )
    }
    return context
}
