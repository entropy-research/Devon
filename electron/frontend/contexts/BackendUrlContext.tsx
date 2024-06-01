import React, { createContext, useContext, useEffect, useState } from 'react'

const BackendUrlContext = createContext<{
    port: number | null
    backendUrl: string | null
}>({ port: null, backendUrl: null })

export const BackendUrlProvider = ({ children }) => {
    const [port, setPort] = useState<number | null>(null)
    const [backendUrl, setBackendUrl] = useState<string | null>(null)

    useEffect(() => {
        if (port === null) {
            window.api.send('get-port')
            window.api.receive('get-port-response', (port: number) => {
                setPort(port)
                setBackendUrl(`http://localhost:${port}`)
            })
        }
    }, [port])

    return (
        <BackendUrlContext.Provider value={{ port, backendUrl }}>
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
