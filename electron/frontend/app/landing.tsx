'use client'
import { useLocalStorage } from '@/lib/hooks/chat.use-local-storage'
import Home, { SessionMachineContext } from './home'
import OnboardingModal from '@/components/modals/onboarding-modal'
import { LocalStorageKey } from '@/lib/types'
import SelectProjectDirectoryModal from '@/components/modals/select-project-directory-modal'

export default function Landing() {
    const [hasAcceptedCheckbox, setHasAcceptedCheckbox] =
        useLocalStorage<boolean>(LocalStorageKey.hasAcceptedCheckbox, false)

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
                openProjectModal={!state.can({ type: 'session.toggle' }) && !state.matches('resetting')}
                hideclose
                sessionActorref={sessionActorref}
                state={state}
            />
        </>
    )
}
