'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import { useBackendUrl } from '@/contexts/BackendUrlContext'
import AtomLoader from '@/components/ui/atom-loader/atom-loader'

export default function Landing() {
    const searchParams = useSearchParams()
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)
    const [openProjectModal, setOpenProjectModal] = useState(false)
    const { port, backendUrl } = useBackendUrl()
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        const chatId = searchParams.get('chat')
        if (chatId && chatId !== 'New') return
        if (hasAcceptedCheckbox) {
            setOpenProjectModal(true)
            window.history.replaceState({}, '', '/?chat=New')
        }
    }, [hasAcceptedCheckbox, searchParams])

    const [sessionMachineProps, setSessionMachineProps] = useState<{
        port: number
        name: string
        path: string
    } | null>(null)

    let sessionName = searchParams.get('chat')
    const encodedPath = searchParams.get('path')

    useEffect(() => {
        if (sessionName && encodedPath && port) {
            const stateMachineProps = {
                port: port,
                name: sessionName,
                path: decodeURIComponent(encodedPath),
            }

            setSessionMachineProps(stateMachineProps)
        }
    }, [sessionName, encodedPath, port])

    useEffect(() => {
        // Ensure the loader is displayed for at least 3 seconds
        const minimumLoadingDuration = 1500
        const timer = setTimeout(() => {
            setIsLoading(false)
        }, minimumLoadingDuration)

        return () => clearTimeout(timer)
    }, [])

    // When still loading session machine, show loading screen
    return (
        <>
            {sessionMachineProps && !isLoading ? (
                <Home sessionMachineProps={sessionMachineProps} />
            ) : (
                <div className="absolute top-0 left-0 w-full h-full bg-night z-50">
                    <div className="fixed left-[50%] top-[50%] grid translate-x-[-50%] translate-y-[-50%]">
                        <div className="flex items-center justify-center flex-col gap-10">
                            <AtomLoader size="lg" />
                            <p className="text-2xl">{`Devon's cleaning up his desk...`}</p>
                        </div>
                    </div>
                </div>
            )}
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
