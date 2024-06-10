'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home, { SessionMachineContext } from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'
import { useBackendUrl } from '@/contexts/BackendUrlContext'

export default function Landing() {
    const searchParams = useSearchParams()
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)
    const [openProjectModal, setOpenProjectModal] = useState(false)
    const { backendUrl } = useBackendUrl()

    useEffect(() => {

        if (hasAcceptedCheckbox) {
            setOpenProjectModal(true)
            window.history.replaceState({}, '', '/?chat=New')
        }
    }, [hasAcceptedCheckbox, searchParams])

    let sessionActorref = SessionMachineContext.useActorRef()
    let state = SessionMachineContext.useSelector(state => state)
    
    return (
        <>
            <Home />
            <OnboardingModal
                initialized={hasAcceptedCheckbox}
                setInitialized={setHasAcceptedCheckbox}
            />
            <SelectProjectDirectoryModal
                openProjectModal={!state.can({type: 'session.toggle'}) && !state.matches('resetting')}
                hideclose
                sessionActorref={sessionActorref}
                state={state}
            />
        </>
    )
}
