'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'

export default function Landing() {
    const searchParams = useSearchParams()
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)
    const [openProjectModal, setOpenProjectModal] = useState(false)

    useEffect(() => {
        const chatId = searchParams.get('chat')
        if (chatId) return
        if (hasAcceptedCheckbox) {
            setOpenProjectModal(true)
            window.history.replaceState({}, '', '/?chat=New')
        }
    }, [hasAcceptedCheckbox, searchParams])


    let [port, setPort] = useState<number>(NaN)

    useEffect(() => {
        window.api.send('get-port')
        window.api.receive('get-port-response', (port) => {
            setPort(port)
        })

    }, [])

    const [sessionMachineProps, setSessionMachineProps] = useState<{
        port: number
        name: string
        path: string
    } | null>(null)


    let sessionName = searchParams.get('chat')
    const encodedPath = searchParams.get('path')
    console.log(sessionName,encodedPath)
    useEffect(() => {

        if (sessionName && encodedPath && port) {
            const stateMachineProps = {
                port: port,
                name: sessionName,
                path: decodeURIComponent(encodedPath),
            }
            setSessionMachineProps(stateMachineProps)
        }
    }, [sessionName, encodedPath,port])

    return (
        <>
            <Home sessionMachineProps={sessionMachineProps} />
            <OnboardingModal
                initialized={hasAcceptedCheckbox}
                setInitialized={setHasAcceptedCheckbox}
            />
            <SelectProjectDirectoryModal
                openProjectModal={openProjectModal}
                hideclose
            />
        </>
    )
}
