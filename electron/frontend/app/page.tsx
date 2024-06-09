'use client'

import { useEffect, useState } from 'react'
import Landing from './landing'
import { useBackendUrl } from '@/contexts/BackendUrlContext'
import { SessionContextProviderComponent } from './home'


export default function IndexPage() {

    const {backendUrl} = useBackendUrl()

    const [sessionMachineProps, setSessionMachineProps] = useState<{
        host: string
        name: string
    } | null>(null)

    useEffect(() => {
        if (backendUrl) {
            setSessionMachineProps({ host: backendUrl, name: "UI"})
        }
    }, [backendUrl])

    return (
        <>
        {sessionMachineProps ? (
            <SessionContextProviderComponent sessionMachineProps={sessionMachineProps}>
                <Landing />
            </SessionContextProviderComponent>
        ) :    <Landing />}
        </>
    )
}
